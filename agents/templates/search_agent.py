import hashlib
import json
from collections import Counter, defaultdict, deque
from typing import Any

from arcengine import FrameData, GameAction, GameState

from ..agent import Agent


def frame_signature(frame: FrameData) -> str:
    """Return a stable signature for frame content used by the search policy."""
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
    if not available_actions:
        return [action for action in GameAction if action is not GameAction.RESET]

    actions: list[GameAction] = []
    for raw in available_actions:
        try:
            action = raw if isinstance(raw, GameAction) else GameAction.from_id(int(raw))
        except (TypeError, ValueError):
            continue
        if action is not GameAction.RESET:
            actions.append(action)

    return actions


def score_transition(
    previous: FrameData,
    current: FrameData,
    repeated: bool = False,
) -> float:
    """Score a transition between observed frames."""
    score = 1000 * (current.levels_completed - previous.levels_completed)
    if current.state != previous.state:
        score += 10
    if current.state is GameState.GAME_OVER:
        score -= 5
    if repeated:
        score -= 1
    return float(score)


def generate_action_sequences(
    actions: list[GameAction],
    depth: int,
    limit: int,
) -> list[tuple[GameAction, ...]]:
    """Generate deterministic breadth-first action tuples."""
    if depth <= 0 or limit <= 0:
        return []

    non_reset_actions = [action for action in actions if action is not GameAction.RESET]
    search_actions = non_reset_actions or list(actions)
    ordered_actions = sorted(dict.fromkeys(search_actions), key=lambda action: action.value)

    sequences: list[tuple[GameAction, ...]] = []
    queue: deque[tuple[GameAction, ...]] = deque((action,) for action in ordered_actions)
    while queue and len(sequences) < limit:
        sequence = queue.popleft()
        sequences.append(sequence)
        if len(sequence) < depth:
            queue.extend(sequence + (action,) for action in ordered_actions)

    return sequences


class Search(Agent):
    """A deterministic, non-rollout search baseline agent."""

    MAX_ACTIONS = 80

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.state_counts: Counter[str] = Counter()
        self.action_counts: Counter[GameAction] = Counter()
        self.action_scores: defaultdict[GameAction, list[float]] = defaultdict(list)
        self.recent_actions: deque[GameAction] = deque(maxlen=6)
        self.last_frame: FrameData | None = None
        self.last_action: GameAction | None = None
        self.planned_actions: deque[GameAction] = deque()

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}.search"

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Stop only when the game has been won."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose a legal action using observed transition scores and novelty."""
        signature = frame_signature(latest_frame)
        repeated = self.state_counts[signature] > 0
        self.state_counts[signature] += 1

        if self.last_frame is not None and self.last_action is not None:
            self.action_scores[self.last_action].append(
                score_transition(self.last_frame, latest_frame, repeated=repeated)
            )

        if latest_frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
            self.planned_actions.clear()
            self.last_frame = latest_frame
            self.last_action = GameAction.RESET
            action = GameAction.RESET
            action.set_data({"game_id": self.game_id})
            action.reasoning = (
                f"Resetting {self.game_id} because state is {latest_frame.state.value}."
            )
            return action

        legal_actions = legal_non_reset_actions(latest_frame)
        if not legal_actions:
            self.planned_actions.clear()
            self.last_frame = latest_frame
            self.last_action = GameAction.RESET
            action = GameAction.RESET
            action.set_data({"game_id": self.game_id})
            action.reasoning = (
                f"Resetting {self.game_id} because no legal non-reset actions are available."
            )
            return action

        while self.planned_actions:
            planned = self.planned_actions.popleft()
            if planned in legal_actions:
                return self._prepare_action(
                    planned,
                    latest_frame,
                    f"Following queued search action {planned.name}.",
                )

        sequences = generate_action_sequences(legal_actions, depth=2, limit=self.MAX_ACTIONS)
        best_sequence = max(
            sequences,
            key=lambda sequence: (
                self._sequence_score(sequence, latest_frame),
                tuple(-action.value for action in sequence),
            ),
        )
        self.planned_actions.extend(best_sequence[1:])
        return self._prepare_action(
            best_sequence[0],
            latest_frame,
            f"Selected best search sequence {[action.name for action in best_sequence]}.",
        )

    def _sequence_score(
        self,
        sequence: tuple[GameAction, ...],
        latest_frame: FrameData,
    ) -> float:
        average_score = sum(self._average_action_score(action) for action in sequence) / len(
            sequence
        )
        recent_use_penalty = sum(
            (0.05 * self.action_counts[action])
            + (0.1 * list(self.recent_actions).count(action))
            for action in sequence
        ) / len(sequence)
        return average_score - recent_use_penalty

    def _average_action_score(self, action: GameAction) -> float:
        scores = self.action_scores.get(action)
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _prepare_action(
        self,
        action: GameAction,
        latest_frame: FrameData,
        reasoning: str,
    ) -> GameAction:
        self.last_frame = latest_frame
        self.last_action = action
        self.action_counts[action] += 1
        self.recent_actions.append(action)

        if action.is_simple():
            action.set_data({"game_id": self.game_id})
            action.reasoning = reasoning
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
                "strategy": "search",
                "reason": reasoning,
                "game_id": self.game_id,
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
