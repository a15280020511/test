# HEBC-Lite

HEBC-Lite is a lightweight external analysis-decision expert panel and simulation scaffold for GitHub Actions.

Final first-version stack:

```text
Pydantic AI + Mesa + GPT modeling
```

Excluded from this repository as direct dependencies:

```text
SimPy
Monte Carlo
NumPy/Pandas Monte Carlo
Scrapy
Crawlee
n8n
Firecrawl
LangGraph
CrewAI
```

## Purpose

The system lets ChatGPT submit a structured `task.json` into `tasks/inbox/`, then GitHub Actions runs a small pipeline:

```text
task.json
→ schema validation
→ status updates
→ Pydantic AI expert-panel adapter or test-mode mock
→ GPT-style structural modeling
→ optional Mesa runner
→ red-team and judge stages
→ report.md + artifact.json
```

## Default cost policy

The default configuration is test-mode and zero-spend:

```text
allow_paid_models = false
max_cost_usd_per_task = 0.0
prefer_free_models = true
```

Real OpenRouter calls require `OPENROUTER_API_KEY` in GitHub Secrets and an explicit config change away from zero-spend test mode.

## Submit a task

Create a file under `tasks/inbox/`, for example:

```json
{
  "task_id": "20260702_fuzhou_job_choice",
  "task_type": "decision_modeling",
  "question": "福州夜班保安、网约车、外卖、快递哪个更适合？",
  "background": {
    "location": "福州",
    "current_job": "夜班保安",
    "preferences": ["稳定", "低维护", "低成本", "不买车", "不违法"]
  },
  "constraints": {
    "avoid": ["买车", "高押金长租", "无证运营", "严重影响睡眠"],
    "must_have": ["净收入判断", "合规判断", "身体负荷", "止损条件"]
  },
  "modeling": {
    "use_gpt_modeling": true,
    "use_mesa": false,
    "mesa_reason": null
  },
  "outputs": [
    "core_conclusion",
    "variables",
    "assumptions",
    "scenario_tree",
    "risk_analysis",
    "red_team",
    "stop_loss",
    "next_actions"
  ]
}
```

Then run the **HEBC Lite Run Task** workflow manually, or push the JSON file and let the workflow trigger.

## Check status

Each task writes:

```text
jobs/status/{task_id}.status.json
```

The **Check Status** workflow can print a status file by `job_id`.

## Read outputs

Completed runs write:

```text
reports/archive/{task_id}.md
reports/latest_report.md
artifacts/archive/{task_id}.json
artifacts/latest_result.json
```

## Safety rules

- Never print `OPENROUTER_API_KEY`.
- Never write secrets into reports, artifacts, logs, README, or configs.
- Failed tasks must produce failed status and an error artifact.
- Mesa is disabled by default and requires an explicit reason.
