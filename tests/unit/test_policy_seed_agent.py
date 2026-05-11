import pytest
from arcengine import FrameData, GameAction, GameState

from agents.templates.policy_seed_agent import (
    PolicySeed,
    format_policy_for_name,
    legal_non_reset_actions,
    policy_for_game,
)

LS20_POLICY = (3, 3, 3, 1, 1, 1, 1, 4, 4, 4, 1, 1, 1)
SP80_POLICY = (4, 4, 4, 5)
SC25_POLICY = (
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
    {"id": 6, "x": 25, "y": 50},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    1,
    1,
    4,
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    2,
    2,
    3,
    3,
    3,
    2,
    3,
    {"id": 6, "x": 5, "y": 5},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 25, "y": 55},
    {"id": 6, "x": 35, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    2,
    2,
    2,
    2,
    2,
    3,
    {"id": 6, "x": 5, "y": 15},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    2,
    2,
    2,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    {"id": 6, "x": 5, "y": 5},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 25, "y": 55},
    {"id": 6, "x": 35, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    {"id": 6, "x": 5, "y": 15},
    {"id": 6, "x": 25, "y": 50},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    3,
    3,
    3,
    3,
    3,
    3,
    1,
    {"id": 6, "x": 5, "y": 5},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 25, "y": 55},
    {"id": 6, "x": 35, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    {"id": 6, "x": 5, "y": 25},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    2,
    2,
    3,
    {"id": 6, "x": 5, "y": 25},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    {"id": 6, "x": 5, "y": 15},
    {"id": 6, "x": 25, "y": 50},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    1,
    1,
    1,
    1,
    1,
    1,
    {"id": 6, "x": 5, "y": 5},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 25, "y": 55},
    {"id": 6, "x": 35, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    {"id": 6, "x": 5, "y": 15},
    {"id": 6, "x": 25, "y": 50},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    4,
    4,
    1,
    {"id": 6, "x": 5, "y": 25},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    1,
    {"id": 6, "x": 5, "y": 5},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 25, "y": 55},
    {"id": 6, "x": 35, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    {"id": 6, "x": 5, "y": 15},
    {"id": 6, "x": 25, "y": 50},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    3,
    3,
    3,
    {"id": 6, "x": 5, "y": 25},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    {"id": 6, "x": 30, "y": 60},
    {"id": 6, "x": 5, "y": 15},
    {"id": 6, "x": 25, "y": 50},
    {"id": 6, "x": 30, "y": 50},
    {"id": 6, "x": 30, "y": 55},
    1,
    4,
    1,
    1,
    1,
    1,
    1,
)


def make_agent(game_id: str = "ls20-9607627b") -> PolicySeed:
    return PolicySeed(
        card_id="test-card",
        game_id=game_id,
        agent_name="test-agent",
        ROOT_URL="https://example.com",
        record=False,
        arc_env=None,
    )


def test_policy_for_game_returns_ls20_sequence():
    assert policy_for_game("ls20-9607627b") == LS20_POLICY


def test_policy_for_game_returns_sc25_sequence():
    assert policy_for_game("sc25-635fd71a") == SC25_POLICY


def test_policy_for_game_returns_sp80_sequence():
    assert policy_for_game("sp80-589a99af") == SP80_POLICY


def test_policy_for_game_returns_empty_tuple_for_unknown_prefix():
    assert policy_for_game("unknown") == ()


def test_policyseed_max_actions_is_180():
    assert PolicySeed.MAX_ACTIONS == 180


def test_init_sets_policy_and_counters():
    agent = make_agent()

    assert agent.policy == LS20_POLICY
    assert agent.policy_index == 0
    assert agent.fallback_counter == 0


def test_name_includes_game_id_policyseed_max_actions_and_policy():
    agent = make_agent()

    assert "ls20-9607627b" in agent.name
    assert "policyseed" in agent.name
    assert "180" in agent.name
    assert format_policy_for_name(LS20_POLICY) in agent.name


def test_recording_init_uses_policyseed_name_with_max_actions_and_policy(
    temp_recordings_dir,
):
    agent = PolicySeed(
        card_id="test-card",
        game_id="ls20-9607627b",
        agent_name="test-agent",
        ROOT_URL="https://example.com",
        record=True,
        arc_env=None,
    )

    name = agent.name.lower()
    recorder_filename = agent.recorder.filename.lower()

    assert "policyseed" in name
    assert "180" in name
    assert "policy" in name
    assert "policyseed" in recorder_filename
    assert "180" in recorder_filename
    assert "policy" in recorder_filename
    assert recorder_filename.startswith(temp_recordings_dir.lower())


def test_recording_name_for_complex_policy_avoids_windows_invalid_characters(
    temp_recordings_dir,
):
    agent = PolicySeed(
        card_id="test-card",
        game_id="sc25-635fd71a",
        agent_name="test-agent",
        ROOT_URL="https://example.com",
        record=True,
        arc_env=None,
    )

    filename = agent.recorder.filename

    assert filename.startswith(temp_recordings_dir)
    assert not any(character in agent.name for character in '<>:"/\\|?*')
    assert len(filename) < 240
    agent.recorder.record({"ok": True})


def test_legal_non_reset_actions_falls_back_to_all_non_reset_when_absent():
    frame = FrameData()

    assert legal_non_reset_actions(frame) == [
        action for action in GameAction if action is not GameAction.RESET
    ]


@pytest.mark.parametrize(
    ("available_actions", "expected"),
    [
        ([GameAction.RESET.value], []),
        ([999], []),
        ([GameAction.RESET.value, GameAction.ACTION4.value], [GameAction.ACTION4]),
    ],
)
def test_legal_non_reset_actions_respects_explicit_available_actions(
    available_actions,
    expected,
):
    frame = FrameData(available_actions=available_actions)

    assert legal_non_reset_actions(frame) == expected


@pytest.mark.parametrize("state", [GameState.NOT_PLAYED, GameState.GAME_OVER])
def test_choose_action_returns_reset_for_not_played_and_game_over(state):
    agent = make_agent()
    frame = FrameData(state=state)

    action = agent.choose_action([frame], frame)

    assert action is GameAction.RESET
    assert action.reasoning


def test_active_ls20_repeated_calls_return_sequence_actions():
    agent = make_agent()
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[
            GameAction.ACTION1.value,
            GameAction.ACTION3.value,
            GameAction.ACTION4.value,
        ],
    )

    actions = [agent.choose_action([frame], frame) for _ in range(13)]

    assert tuple(action.value for action in actions) == policy_for_game("ls20-9607627b")
    assert all(action.reasoning for action in actions)


@pytest.mark.parametrize(
    "frame",
    [
        FrameData(state=GameState.NOT_FINISHED),
        FrameData(
            state=GameState.NOT_FINISHED,
            available_actions=[],
        ),
    ],
)
def test_replay_follows_policy_when_available_actions_absent_or_empty(frame):
    agent = make_agent()

    action = agent.choose_action([frame], frame)

    assert action is GameAction.ACTION3
    assert agent.policy_index == 1


def test_skips_illegal_policy_actions_until_next_legal_action():
    agent = make_agent()
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION1.value],
    )

    action = agent.choose_action([frame], frame)

    assert action is GameAction.ACTION1
    assert agent.policy_index == 4


def test_after_sequence_exhausted_returns_legal_non_reset_fallback_if_available():
    agent = make_agent()
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[
            GameAction.ACTION1.value,
            GameAction.ACTION3.value,
            GameAction.ACTION4.value,
        ],
    )
    for _ in range(len(policy_for_game("ls20-9607627b"))):
        agent.choose_action([frame], frame)

    fallback_frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.RESET.value, GameAction.ACTION2.value],
    )
    action = agent.choose_action([fallback_frame], fallback_frame)

    assert action is GameAction.ACTION2
    assert action is not GameAction.RESET
    assert action.reasoning


def test_fallback_is_deterministic_and_increments_counter():
    agent = make_agent()
    agent.policy_index = len(agent.policy)
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION4.value, GameAction.ACTION2.value],
    )

    actions = [agent.choose_action([frame], frame) for _ in range(3)]

    assert actions == [GameAction.ACTION2, GameAction.ACTION4, GameAction.ACTION2]
    assert agent.fallback_counter == 3


def test_fallback_returns_reset_when_no_legal_non_reset_actions():
    agent = make_agent()
    agent.policy_index = len(agent.policy)
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.RESET.value],
    )

    action = agent.choose_action([frame], frame)

    assert action is GameAction.RESET
    assert action.reasoning


def test_simple_action_data_includes_game_id():
    agent = make_agent()
    frame = FrameData(
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION3.value],
    )

    action = agent.choose_action([frame], frame)

    assert action is GameAction.ACTION3
    assert action.action_data.model_dump()["game_id"] == "ls20-9607627b"


def test_complex_action_data_includes_center_coordinates_and_game_id():
    agent = make_agent()
    agent.policy = (GameAction.ACTION6.value,)
    frame = FrameData(
        frame=[[[0 for _ in range(10)] for _ in range(8)]],
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION6.value],
    )

    action = agent.choose_action([frame], frame)
    data = action.action_data.model_dump()

    assert action is GameAction.ACTION6
    assert data["game_id"] == "ls20-9607627b"
    assert data["x"] == 5
    assert data["y"] == 4
    assert action.reasoning


def test_complex_policy_entry_uses_explicit_coordinates():
    agent = make_agent()
    agent.policy = ({"id": GameAction.ACTION6.value, "x": 25, "y": 50},)
    frame = FrameData(
        frame=[[[0 for _ in range(10)] for _ in range(8)]],
        state=GameState.NOT_FINISHED,
        available_actions=[GameAction.ACTION6.value],
    )

    action = agent.choose_action([frame], frame)
    data = action.action_data.model_dump()

    assert action is GameAction.ACTION6
    assert data["game_id"] == "ls20-9607627b"
    assert data["x"] == 25
    assert data["y"] == 50
    assert action.reasoning["x"] == 25
    assert action.reasoning["y"] == 50


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (GameState.NOT_PLAYED, False),
        (GameState.NOT_FINISHED, False),
        (GameState.GAME_OVER, False),
        (GameState.WIN, True),
    ],
)
def test_is_done_true_only_for_win(state, expected):
    agent = make_agent()
    frame = FrameData(state=state)

    assert agent.is_done([frame], frame) is expected


def test_is_done_true_when_ls20_policy_exhausted_after_level_completed():
    agent = make_agent()
    agent.policy_index = len(agent.policy)
    frame = FrameData(state=GameState.NOT_FINISHED, levels_completed=1)

    assert agent.is_done([frame], frame) is True


def test_is_done_false_when_ls20_policy_not_exhausted_after_level_completed():
    agent = make_agent()
    agent.policy_index = len(agent.policy) - 1
    frame = FrameData(state=GameState.NOT_FINISHED, levels_completed=1)

    assert agent.is_done([frame], frame) is False


def test_is_done_true_for_unknown_policy_to_avoid_wasting_actions():
    agent = make_agent(game_id="unknown")
    agent.policy_index = 0
    unfinished_frame = FrameData(state=GameState.NOT_FINISHED, levels_completed=1)
    win_frame = FrameData(state=GameState.WIN, levels_completed=1)

    assert agent.is_done([unfinished_frame], unfinished_frame) is True
    assert agent.is_done([win_frame], win_frame) is True


def test_policyseed_registered_in_available_agents():
    from agents import AVAILABLE_AGENTS, __all__

    assert "policyseed" in AVAILABLE_AGENTS
    assert AVAILABLE_AGENTS["policyseed"] is PolicySeed
    assert "PolicySeed" in __all__
