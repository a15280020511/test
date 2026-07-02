# GitHub Actions Diagnosis

## Current finding

HEBC-Lite code, configs, workflows, tests, free-model policy, and maintenance runner have been written to the repository. However, expected workflow output files have not appeared on the default branch.

Missing outputs checked:

```text
jobs/status/example_decision_task.status.json
reports/latest_report.md
artifacts/latest_result.json
reports/health_check.md
reports/cleanup_report.json
reports/maintenance_report.md
```

## Most likely causes

```text
1. GitHub Actions did not trigger from connector-created commits.
2. Repository Actions may be disabled or restricted.
3. Workflow ran but could not push generated outputs.
4. OPENROUTER_API_KEY is missing, so live free-model calls fail.
5. Free OpenRouter model returned a runtime error or rate-limit error.
```

## Important distinction

This is not evidence that the HEBC-Lite Python code is missing. The repository now contains the code path for:

```text
python -m hebc_lite.run_task --task tasks/inbox/example_task.json
python -m hebc_lite.health_check
python -m hebc_lite.cleanup
python -m hebc_lite.maintenance
```

## Next diagnostic action

Inspect the GitHub Actions page for the repository and check whether workflow runs exist for:

```text
HEBC Lite Run Task
Test
Health Check
Cleanup
Maintenance
```

If runs exist, inspect the failed job logs. If no runs exist, Actions triggering or repository Actions settings are the root cause.
