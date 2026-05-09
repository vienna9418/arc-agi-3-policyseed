import hashlib
import json
from collections import Counter, deque
from typing import Any

from arcengine import FrameData, GameAction, GameState

from ..agent import Agent


def frame_signature(frame: FrameData) -> str:
    """Return a stable signature for the parts of a frame used for novelty."""
    payload = {
        "frame": frame.frame,
        "state": frame.state,
        "levels_completed": frame.levels_completed,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def legal_non_reset_actions(frame: FrameData) -> list[GameAction]:
    """Return legal actions for a frame, excluding RESET."""
    available_actions = getattr(frame, "available_actions", None)
    raw_actions: list[Any] = list(available_actions) if available_actions else list(GameAction)

    actions: list[GameAction] = []
    for raw in raw_actions:
        try:
            action = raw if isinstance(raw, GameAction) else GameAction.from_id(int(raw))
        except (TypeError, ValueError):
            continue
        if action is not GameAction.RESET:
            actions.append(action)

    return actions or [action for action in GameAction if action is not GameAction.RESET]


class Heuristic(Agent):
    """A light-weight novelty-seeking baseline agent."""

    MAX_ACTIONS = 80

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.state_counts: Counter[str] = Counter()
        self.action_counts: Counter[GameAction] = Counter()
        self.recent_actions: deque[GameAction] = deque(maxlen=4)
        self.last_level_count = self.levels_completed

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}.novelty"

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Decide if the agent is done playing or not."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        """Choose the least-used currently legal non-reset action."""
        if latest_frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
            action = GameAction.RESET
            action.reasoning = (
                f"Resetting {self.game_id} because state is {latest_frame.state.value}."
            )
            return action

        signature = frame_signature(latest_frame)
        self.state_counts[signature] += 1

        if latest_frame.levels_completed > self.last_level_count:
            self.action_counts.clear()
        self.last_level_count = latest_frame.levels_completed

        legal_actions = legal_non_reset_actions(latest_frame)
        action = min(
            legal_actions,
            key=lambda candidate: (
                self.action_counts[candidate]
                + (0.25 * list(self.recent_actions).count(candidate)),
                candidate.value,
            ),
        )

        self.action_counts[action] += 1
        self.recent_actions.append(action)

        if action.is_simple():
            action.set_data({"game_id": self.game_id})
            action.reasoning = (
                f"Novelty heuristic chose {action.name}; state seen "
                f"{self.state_counts[signature]} time(s)."
            )
        elif action.is_complex():
            action.set_data(
                {
                    "game_id": self.game_id,
                    "x": self._center_coordinate(latest_frame, axis="x"),
                    "y": self._center_coordinate(latest_frame, axis="y"),
                }
            )
            action.reasoning = {
                "desired_action": action.name,
                "strategy": "novelty",
                "game_id": self.game_id,
                "state_visits": self.state_counts[signature],
            }

        return action

    def _center_coordinate(self, frame: FrameData, axis: str) -> int:
        if not frame.frame or not frame.frame[0]:
            return 32

        if axis == "y":
            size = len(frame.frame[0])
        else:
            size = len(frame.frame[0][0]) if frame.frame[0][0] else 64

        return max(0, min(63, size // 2))
