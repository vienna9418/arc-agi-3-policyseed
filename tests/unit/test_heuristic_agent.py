import pytest
from arcengine import FrameData, GameAction, GameState

from agents.templates.heuristic_agent import (
    Heuristic,
    frame_signature,
    legal_non_reset_actions,
)


def make_agent() -> Heuristic:
    return Heuristic(
        card_id="test-card",
        game_id="test-game",
        agent_name="test-agent",
        ROOT_URL="https://example.com",
        record=False,
        arc_env=None,
    )


def test_frame_signature_changes_when_grid_changes():
    frame_a = FrameData(frame=[[[1, 2], [3, 4]]])
    frame_b = FrameData(frame=[[[1, 2], [3, 5]]])

    assert frame_signature(frame_a) != frame_signature(frame_b)


def test_frame_signature_includes_state_and_levels_completed():
    base = FrameData(
        frame=[[[1]]],
        state=GameState.NOT_FINISHED,
        levels_completed=0,
    )
    changed_state = FrameData(
        frame=[[[1]]],
        state=GameState.GAME_OVER,
        levels_completed=0,
    )
    changed_level = FrameData(
        frame=[[[1]]],
        state=GameState.NOT_FINISHED,
        levels_completed=1,
    )

    assert frame_signature(base) != frame_signature(changed_state)
    assert frame_signature(base) != frame_signature(changed_level)


def test_legal_non_reset_actions_uses_available_actions_when_present():
    frame = FrameData(available_actions=[GameAction.RESET.value, GameAction.ACTION2.value])

    assert legal_non_reset_actions(frame) == [GameAction.ACTION2]


def test_legal_non_reset_actions_falls_back_to_all_non_reset_actions_when_available_actions_absent():
    frame = FrameData()

    assert legal_non_reset_actions(frame) == [
        action for action in GameAction if action is not GameAction.RESET
    ]


@pytest.mark.parametrize("state", [GameState.NOT_PLAYED, GameState.GAME_OVER])
def test_choose_action_returns_reset_for_not_played_and_game_over(state):
    agent = make_agent()
    frame = FrameData(state=state)

    action = agent.choose_action([frame], frame)

    assert action is GameAction.RESET
    assert action.reasoning


def test_choose_action_returns_an_available_non_reset_action():
    agent = make_agent()
    frame = FrameData(
        game_id="frame-game",
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.RESET.value, GameAction.ACTION3.value],
    )

    action = agent.choose_action([frame], frame)

    assert action is GameAction.ACTION3
    assert action is not GameAction.RESET
    assert action.reasoning


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (GameState.NOT_PLAYED, False),
        (GameState.NOT_FINISHED, False),
        (GameState.GAME_OVER, False),
        (GameState.WIN, True),
    ],
)
def test_is_done_only_returns_true_for_win(state, expected):
    agent = make_agent()
    frame = FrameData(state=state)

    assert agent.is_done([frame], frame) is expected


def test_heuristic_agent_is_registered():
    from agents import AVAILABLE_AGENTS

    assert "heuristic" in AVAILABLE_AGENTS
