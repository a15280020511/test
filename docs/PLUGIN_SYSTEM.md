# HEBC-Lite Plugin System

HEBC-Lite uses an explicit plugin registry. The registry is `configs/plugins.json`.

## Plugins

- `pydantic_ai`: expert agent framework.
- `mesa`: agent based simulation framework.
- `openrouter`: model gateway.
- `webgpt_orchestrator`: task and orchestration owner.

## Rule

WebGPT supplies task information, role order, model ids, budget, and tool plan. HEBC-Lite validates and executes that plan.

## Runtime layers

1. Read task JSON.
2. Validate WebGPT orchestration.
3. Check plugin registry.
4. Run declared expert roles.
5. Run GPT modeling if requested.
6. Run Mesa if requested with a reason.
7. Write report and artifact.
8. Record roles, models, plugin status, and tool results.

## Light check and full check

Light check is fast and may use minimal dependencies.

Full check should install the full dependency set and verify that pydantic, pydantic_ai, and mesa are importable.

## Simulation maturity

The current Mesa runner proves that the simulation plugin can execute. It is not a mature local market model. A mature model needs real local data, calibrated parameters, richer agents, time windows, route and distance logic, fatigue, weather, cost, and backtesting.

## Audit fields

Every report should show enabled plugins, import status, declared roles, model id per role, tool plan, Mesa status, cost policy, and failures.
