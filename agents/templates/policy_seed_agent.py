from typing import Any, TypeAlias

from arcengine import FrameData, GameAction, GameState

from ..agent import Agent

PolicyEntry: TypeAlias = int | dict[str, int]

POLICIES: dict[str, tuple[PolicyEntry, ...]] = {
    "ls20": (3, 3, 3, 1, 1, 1, 1, 4, 4, 4, 1, 1, 1),
    "sc25": (
        {"id": 6, "x": 30, "y": 50},
        {"id": 6, "x": 30, "y": 50},
        {"id": 6, "x": 25, "y": 55},
        {"id": 6, "x": 35, "y": 55},
        {"id": 6, "x": 30, "y": 60},
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
    ),
}


def policy_for_game(game_id: str) -> tuple[PolicyEntry, ...]:
    """Return the seed policy matching the game id prefix before a hyphen."""
    return POLICIES.get(game_id.split("-", 1)[0], ())


def action_from_policy_entry(entry: PolicyEntry) -> tuple[GameAction, dict[str, int]]:
    """Convert a replay policy entry to an action and optional action data."""
    if isinstance(entry, dict):
        action = GameAction.from_id(int(entry["id"]))
        data = {
            key: int(entry[key])
            for key in ("x", "y")
            if key in entry
        }
        return action, data
    return GameAction.from_id(int(entry)), {}


def format_policy_for_name(policy: tuple[PolicyEntry, ...]) -> str:
    """Return a compact filename-safe policy description."""
    parts: list[str] = []
    for entry in policy:
        if isinstance(entry, dict):
            action_id = int(entry["id"])
            if "x" in entry and "y" in entry:
                parts.append(f"a{action_id}x{int(entry['x'])}y{int(entry['y'])}")
            else:
                parts.append(f"a{action_id}")
        else:
            parts.append(f"a{int(entry)}")
    return "-".join(parts)


def legal_non_reset_actions(frame: FrameData) -> list[GameAction]:
    """Return explicit legal non-reset actions, or all non-reset actions if absent."""
    available_actions = getattr(frame, "available_actions", None)
    if not available_actions:
        return [action for action in GameAction if action is not GameAction.RESET]

    actions: list[GameAction] = []
    for raw in available_actions:
        try:
            action = (
                raw if isinstance(raw, GameAction) else GameAction.from_id(int(raw))
            )
        except (TypeError, ValueError):
            continue
        if action is not GameAction.RESET:
            actions.append(action)

    return actions


class PolicySeed(Agent):
    """Replay a known seed policy, then use deterministic legal fallback actions."""

    MAX_ACTIONS = 80

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.policy = policy_for_game(self.game_id)
        self.policy_index = 0
        self.fallback_counter = 0

    @property
    def name(self) -> str:
        policy = getattr(self, "policy", policy_for_game(getattr(self, "game_id", "")))
        return f"{super().name}.{self.MAX_ACTIONS}.policy-{format_policy_for_name(policy)}"

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Stop after a win or a completed level once seed policy replay is exhausted."""
        if latest_frame.state is GameState.WIN:
            return True
        if not self.policy:
            return True
        return (
            self.policy_index >= len(self.policy)
            and latest_frame.levels_completed > 0
        )

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose the next legal seed policy action, then deterministic fallback."""
        if latest_frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
            return self._prepare_action(
                GameAction.RESET,
                latest_frame,
                f"Resetting {self.game_id} because state is {latest_frame.state.value}.",
            )

        legal_actions = legal_non_reset_actions(latest_frame)
        legal_actions_unavailable = not getattr(latest_frame, "available_actions", None)

        while self.policy_index < len(self.policy):
            policy_value = self.policy[self.policy_index]
            self.policy_index += 1
            try:
                action, action_data = action_from_policy_entry(policy_value)
            except (KeyError, TypeError, ValueError):
                continue
            if legal_actions_unavailable or action in legal_actions:
                return self._prepare_action(
                    action,
                    latest_frame,
                    (
                        f"Following seed policy action {action.name} "
                        f"at position {self.policy_index}/{len(self.policy)}."
                    ),
                    **action_data,
                )

        if legal_actions:
            action = sorted(legal_actions, key=lambda candidate: candidate.value)[
                self.fallback_counter % len(legal_actions)
            ]
            self.fallback_counter += 1
            return self._prepare_action(
                action,
                latest_frame,
                f"Seed policy exhausted; using legal fallback action {action.name}.",
            )

        return self._prepare_action(
            GameAction.RESET,
            latest_frame,
            "Seed policy exhausted and no legal non-reset actions are available.",
        )

    def _prepare_action(
        self,
        action: GameAction,
        latest_frame: FrameData,
        reasoning: str,
        x: int | None = None,
        y: int | None = None,
    ) -> GameAction:
        if action.is_simple():
            action.set_data({"game_id": self.game_id})
            action.reasoning = reasoning
        elif action.is_complex():
            action_x = self._center_coordinate(latest_frame, axis="x") if x is None else x
            action_y = self._center_coordinate(latest_frame, axis="y") if y is None else y
            action.set_data(
                {
                    "game_id": self.game_id,
                    "x": action_x,
                    "y": action_y,
                }
            )
            action.reasoning = {
                "desired_action": action.name,
                "strategy": "policy_seed",
                "reason": reasoning,
                "game_id": self.game_id,
                "x": action_x,
                "y": action_y,
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
