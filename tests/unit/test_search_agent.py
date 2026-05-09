import pytest
from arcengine import FrameData, GameAction, GameState

from agents.templates.search_agent import (
    Search,
    frame_signature,
    generate_action_sequences,
    legal_non_reset_actions,
    score_transition,
)


def make_agent() -> Search:
    return Search(
        card_id="test-card",
        game_id="test-game",
        agent_name="test-agent",
        ROOT_URL="https://example.com",
        record=False,
        arc_env=None,
    )


def test_score_transition_rewards_level_gain_more_than_unchanged_frame():
    previous = FrameData(state=GameState.NOT_FINISHED, levels_completed=0)
    unchanged = FrameData(state=GameState.NOT_FINISHED, levels_completed=0)
    advanced = FrameData(state=GameState.NOT_FINISHED, levels_completed=1)

    assert score_transition(previous, advanced) > score_transition(previous, unchanged)


def test_score_transition_applies_repeated_penalty():
    previous = FrameData(state=GameState.NOT_FINISHED, levels_completed=0)
    current = FrameData(state=GameState.NOT_FINISHED, levels_completed=0)

    assert score_transition(previous, current, repeated=True) < score_transition(
        previous,
        current,
        repeated=False,
    )


def test_frame_signature_is_deterministic_and_includes_relevant_fields():
    frame = FrameData(
        frame=[[[1, 2], [3, 4]]],
        state=GameState.NOT_FINISHED,
        levels_completed=0,
    )
    same = FrameData(
        frame=[[[1, 2], [3, 4]]],
        state=GameState.NOT_FINISHED,
        levels_completed=0,
    )
    changed_level = FrameData(
        frame=[[[1, 2], [3, 4]]],
        state=GameState.NOT_FINISHED,
        levels_completed=1,
    )

    assert frame_signature(frame) == frame_signature(same)
    assert frame_signature(frame) != frame_signature(changed_level)


def test_legal_non_reset_actions_falls_back_only_when_available_actions_empty():
    frame = FrameData()

    assert legal_non_reset_actions(frame) == [
        action for action in GameAction if action is not GameAction.RESET
    ]


@pytest.mark.parametrize(
    "available_actions",
    [
        [GameAction.RESET.value],
        [999],
        [GameAction.RESET.value, 999],
    ],
)
def test_legal_non_reset_actions_returns_empty_when_explicit_actions_have_no_legal_non_reset(
    available_actions,
):
    frame = FrameData(available_actions=available_actions)

    assert legal_non_reset_actions(frame) == []


def test_generate_action_sequences_is_deterministic_and_excludes_reset_when_non_reset_actions_supplied():
    actions = [GameAction.ACTION3, GameAction.RESET, GameAction.ACTION1]

    first = generate_action_sequences(actions, depth=2, limit=5)
    second = generate_action_sequences(actions, depth=2, limit=5)

    assert first == second
    assert first
    assert len(first) <= 5
    assert all(isinstance(sequence, tuple) for sequence in first)
    assert all(0 < len(sequence) <= 2 for sequence in first)
    assert all(GameAction.RESET not in sequence for sequence in first)


@pytest.mark.parametrize("state", [GameState.NOT_PLAYED, GameState.GAME_OVER])
def test_choose_action_returns_reset_for_not_played_and_game_over(state):
    agent = make_agent()
    frame = FrameData(state=state)

    action = agent.choose_action([frame], frame)

    assert action is GameAction.RESET
    assert action.reasoning


def test_choose_action_chooses_from_available_actions_for_active_frames():
    agent = make_agent()
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION2.value, GameAction.ACTION4.value],
    )

    action = agent.choose_action([frame], frame)

    assert action in {GameAction.ACTION2, GameAction.ACTION4}
    assert action.reasoning


@pytest.mark.parametrize(
    "available_actions",
    [
        [GameAction.RESET.value],
        [999],
    ],
)
def test_choose_action_returns_reset_when_active_frame_has_no_legal_non_reset_actions(
    available_actions,
):
    agent = make_agent()
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=available_actions,
    )

    action = agent.choose_action([frame], frame)

    assert action is GameAction.RESET
    assert action.reasoning


def test_sequence_score_penalizes_recently_used_actions():
    agent = make_agent()
    agent.action_scores[GameAction.ACTION1].append(1.0)
    agent.action_scores[GameAction.ACTION2].append(1.0)
    agent.action_counts[GameAction.ACTION1] = 3
    agent.recent_actions.append(GameAction.ACTION1)
    frame = FrameData(state=GameState.NOT_FINISHED)

    assert agent._sequence_score((GameAction.ACTION2,), frame) > agent._sequence_score(
        (GameAction.ACTION1,),
        frame,
    )


def test_choose_action_sets_complex_action6_data_and_reasoning():
    agent = make_agent()
    frame = FrameData(
        frame=[[[0 for _ in range(10)] for _ in range(8)]],
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION6.value],
    )

    action = agent.choose_action([frame], frame)
    data = action.action_data.model_dump()

    assert action is GameAction.ACTION6
    assert data["game_id"] == "test-game"
    assert 0 <= data["x"] <= 63
    assert 0 <= data["y"] <= 63
    assert action.reasoning


def test_choose_action_scores_previous_action_before_resetting_on_game_over():
    agent = make_agent()
    active_frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION2.value],
    )
    game_over_frame = FrameData(state=GameState.GAME_OVER)

    chosen = agent.choose_action([active_frame], active_frame)
    reset = agent.choose_action([active_frame, game_over_frame], game_over_frame)

    assert chosen is GameAction.ACTION2
    assert reset is GameAction.RESET
    assert agent.action_scores[GameAction.ACTION2] == [5.0]
    assert agent.action_scores[GameAction.ACTION2][0] < 10.0


def test_search_agent_is_registered():
    from agents import AVAILABLE_AGENTS

    assert "search" in AVAILABLE_AGENTS
    assert AVAILABLE_AGENTS["search"] is Search
