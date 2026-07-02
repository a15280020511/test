# WebGPT Orchestration Contract

This file defines the rule requested by the user: WebGPT owns all task input, model selection, role organization, and tool planning. HEBC-Lite validates and executes the declared contract.

## Core rule

WebGPT must provide the task JSON. HEBC-Lite must not silently choose paid models, add undeclared roles, disable requested plugins, or hide missing dependencies.

## Required task fields

```json
{
  "task_id": "example_task",
  "task_type": "decision_modeling",
  "question": "The problem to solve.",
  "background": {},
  "constraints": {
    "avoid": [],
    "must_have": []
  },
  "modeling": {
    "use_gpt_modeling": true,
    "use_mesa": false,
    "mesa_reason": null
  },
  "orchestration": {
    "strict": true,
    "roles": ["planner", "red_team", "judge"],
    "models": {
      "planner": "deepseek/deepseek-v4-flash",
      "red_team": "deepseek/deepseek-v4-flash",
      "judge": "deepseek/deepseek-v4-flash"
    },
    "budget": {
      "test_mode": false,
      "allow_paid_models": true,
      "allow_expensive_models": false,
      "max_cost_usd_per_task": 0.05,
      "max_calls_per_task": 3
    },
    "tool_plan": {
      "expert_panel": true,
      "gpt_modeling": true,
      "mesa": false,
      "report": true
    },
    "fallback": {
      "on_model_unavailable": "stop_and_report"
    }
  }
}
```

## WebGPT responsibilities

1. Decide the task type.
2. Fill the question and factual background.
3. Decide which roles are needed.
4. Choose a model for every role.
5. Set budget and paid/free policy.
6. Decide whether GPT modeling is needed.
7. Decide whether Mesa is needed and provide a reason if enabled.
8. Define output requirements.
9. Keep model choices explicit and auditable.

## HEBC-Lite responsibilities

1. Validate the task contract.
2. Execute declared roles in declared order.
3. Use declared models per role.
4. Enforce budget and paid/free policy.
5. Run declared tools when available.
6. Report missing plugins, missing secrets, and failures.
7. Write report and artifact.

## Forbidden behavior

HEBC-Lite must not:

- silently replace WebGPT-declared models;
- silently add paid models;
- silently drop roles;
- hide dependency failures;
- claim Mesa ran when it was skipped or failed;
- claim industrial simulation when only toy simulation ran.

## Recommended role patterns

Simple task:

```json
"roles": ["judge"]
```

Risky decision:

```json
"roles": ["planner", "red_team", "judge"]
```

Modeling task:

```json
"roles": ["planner", "modeler", "red_team", "judge"]
```

Long report task:

```json
"roles": ["planner", "modeler", "red_team", "judge", "reporter"]
```
