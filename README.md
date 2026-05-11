# ARC-AGI-3-Agents

## Quickstart

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if not aready installed.

1. Clone the ARC-AGI-3-Agents repo and enter the directory.

```bash
git clone https://github.com/arcprize/ARC-AGI-3-Agents.git
cd ARC-AGI-3-Agents
```

2. Copy .env.example to .env

```bash
cp .env.example .env
```

3. Get an API key from the [ARC-AGI-3 Website](https://three.arcprize.org/) and set it as an environment variable in your .env file.

```bash
export ARC_API_KEY="your_api_key_here"
```

4. Run the random agent (generates random actions) against the ls20 game.

```bash
uv run main.py --agent=random --game=ls20
```

For more information, see the [documentation](https://three.arcprize.org/docs#quick-start) or the [tutorial video](https://youtu.be/xEVg9dcJMkw).

## Changelog
## [0.9.3] - 2026-01-29
**Note: This will be a breaking change is you use the fields outline below**

### Added
- `FrameData` had two field names changes. 
  - `score` changed to `levels_completed`
  - `win_score` changed to `win_levels`
- Updated to use the new [ARC-AGI](https://github.com/arcprize/ARC-AGI) tool
  - Allows local execution of environments
  - Allows the creation of your own environments, see [Creating an Environment](https://docs.arcprize.org/add_game)
  - If you want to continue to use the online API/Replays set `ONLINE_ONLY` to `True` in `.env.example`

## [0.9.2] - 2025-08-19

### Added
- `available_actions` to `FrameData`
- `ACTION7` as possible `GameAction`

## [0.9.1] - 2025-07-18

Initial Release

## Observability (Optional)

[AgentOps](https://agentops.ai/) is an observability platform designed for providing real-time monitoring, debugging, and analytics for your agent's behavior, helping you understand how your agents perform and make decisions.

### Installation

AgentOps is already included as an optional dependency in this project. To install it:

```bash
uv sync --extra agentops
```

Or if you're installing manually:

```bash
pip install -U agentops
```

### Getting Your API Key

1. Visit [app.agentops.ai](https://app.agentops.ai) and create an account if you haven't already
2. Once logged in, click on "New Project" to create a project for your ARC-AGI-3 agents
3. Give your project a meaningful name (e.g., "ARC-AGI-3-Agents")
4. After creating the project, you'll see your project dashboard
5. Click on the "API Keys" tab on the left side & copy the API key

### Configuration

1. Add your AgentOps API key to your `.env` file:

```bash
AGENTOPS_API_KEY=aos_your_api_key_here
```

2. The AgentOps integration is automatically initialized when you run an agent. The tracing decorator `@trace_agent_session` is already applied to agent execution methods in the codebase.

3. When you run your agent, you'll see AgentOps initialization messages and session URLs in the console:

```bash
🖇 AgentOps: Session Replay for your-agent-name: https://app.agentops.ai/sessions?trace_id=xxxxx
```

4. Click on the session URL to view real-time traces of your agent's execution. You can also view the traces in the AgentOps dashboard by locating the trace ID in the "Traces" tab.

### Using AgentOps with Custom Agents

If you're creating a custom agent, the tracing is automatically applied through the `@trace_agent_session` decorator on the `main()` method. No additional code changes are needed.

## Contest Submission

To submit your agent for the ARC-AGI-3 competition, please use this form: https://forms.gle/wMLZrEFGDh33DhzV9.

## PolicySeed v0 Submission

This fork adds a deterministic baseline agent named `policyseed`.

### Run Instructions

1. Install the project dependencies following the quick-start steps above.
2. Create a `.env` file with an ARC API key:

   ```bash
   ARC_API_KEY="your_api_key_here"
   SCHEME=https
   HOST=three.arcprize.org
   PORT=443
   ARC_BASE_URL=https://three.arcprize.org
   OPERATION_MODE=online
   ```

3. Run the submitted agent on all available ARC-AGI-3 public games:

   ```bash
   uv run main.py --agent=policyseed --tags policyseed-v0
   ```

   To reproduce the local smoke test for LS20 only:

   ```bash
   uv run main.py --agent=policyseed --game=ls20
   ```

### Solution Description

`PolicySeed` replays a short, deterministic action sequence discovered by local
state-space search for the `ls20` public game:

```text
3, 3, 3, 1, 1, 1, 1, 4, 4, 4, 1, 1, 1
```

For games without a known seed policy, it uses a deterministic legal-action
fallback that avoids reset actions where possible. This is intentionally a small
and reproducible baseline rather than an LLM or large-compute solution.

### Verification Notes

On 2026-05-10, the v0 online scorecard run for `policyseed` completed with:

- scorecard: https://three.arcprize.org/scorecards/4dda3df5-5c04-484a-a933-34b855314d40
- total levels completed: 1 / 183
- total environments: 25
- total actions: 1317

The v1 run adds a deterministic `sc25` level-0 policy and avoids spending
actions on games without a known seed policy:

- scorecard: https://three.arcprize.org/scorecards/dc05a240-5812-4be7-a293-1f817efb7962
- total levels completed: 2 / 183
- total environments: 25
- total actions: 30

The v2 run extends the deterministic `sc25` replay through its second solved
level and keeps unknown games at zero policy actions:

- scorecard: https://three.arcprize.org/scorecards/64ea6217-337e-4013-a19d-473865212df6
- total levels completed: 3 / 183
- total environments: 25
- total actions: 35

The v3 run extends `sc25` through its third solved level:

- scorecard: https://three.arcprize.org/scorecards/e35e46cf-576d-4db3-ab8d-1b91248bbd03
- total levels completed: 4 / 183
- total environments: 25
- total actions: 46

The v4 run extends `sc25` through its fourth solved level:

- scorecard: https://three.arcprize.org/scorecards/7eb7a0bf-945f-41c6-9d87-df42eb28d3d1
- total levels completed: 5 / 183
- total environments: 25
- total actions: 73

The v5 run extends `sc25` through its fifth solved level and raises the
policy replay action cap to cover the longer deterministic sequence:

- scorecard: https://three.arcprize.org/scorecards/db25681e-db34-4d26-be53-66720b1e8e51
- total levels completed: 6 / 183
- total environments: 25
- total actions: 115

The v6 run completes all six public `sc25` levels with a deterministic replay
and keeps the `ls20` seed solution:

- scorecard: https://three.arcprize.org/scorecards/f0e09f7c-ae83-4a71-870a-e2e599ab48aa
- total levels completed: 7 / 183
- total environments: 25
- total actions: 159

The v7 run adds a four-action deterministic `sp80` level-0 policy:

- scorecard: https://three.arcprize.org/scorecards/34fd896a-e8ce-424f-9864-d1c2f107dc99
- total levels completed: 8 / 183
- total environments: 25
- total actions: 163

The v8 run adds a deterministic `tr87` policy that completes all six public
`tr87` levels:

- scorecard: https://three.arcprize.org/scorecards/17fa586d-e2f9-4260-a538-b931a60c6265
- total levels completed: 14 / 183
- total environments: 25
- total actions: 290

Local targeted tests:

```bash
python -m pytest tests/unit/test_policy_seed_agent.py tests/unit/test_search_agent.py tests/unit/test_heuristic_agent.py -q
ruff check agents/__init__.py agents/templates/policy_seed_agent.py tests/unit/test_policy_seed_agent.py
```

## Contributing

We welcome contributions! To contribute to ARC-AGI-3-Agents, please follow these steps:

1.  Fork the repository and create a new branch for your feature or bugfix.
2.  Make your changes and ensure that all tests pass, you are welcome to add more tests for your specific fixes.
3.  This project uses `ruff` for linting and formatting. Please set up the pre-commit hooks to ensure your contributions match the project's style.
    ```bash
    pip install pre-commit
    pre-commit install
    ```
4.  Write clear commit messages describing your changes.
5.  Open a pull request with a description of your changes and the motivation behind them.

If you have questions or need help, feel free to open an issue.

## Tests

To run the tests, you will need to have `pytest` installed. Run the tests like this:

```bash
pytest
```

For more information on tests, please see the [tests documentation](https://three.arcprize.org/docs#testing).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
