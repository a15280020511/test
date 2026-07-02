from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .agents import run_expert_panel
from .gpt_modeling import build_modeling_result
from .mesa_runner import run_mesa
from .report_writer import write_outputs
from .router import decide_model_roles, decide_need_gpt_modeling, decide_need_mesa
from .schemas import AgentCallRecord, Task
from .status import write_status


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_task(task_file: str | Path) -> int:
    task_file = Path(task_file)
    raw_task = load_json(task_file)
    job_id = str(raw_task.get("task_id") or task_file.stem)
    try:
        write_status(job_id, "queued", "queued", 0.0, task_file=str(task_file), task_id=job_id)
        task = Task.model_validate(raw_task)
        job_id = task.task_id
        write_status(job_id, "running", "planning", 0.1, task_file=str(task_file), task_id=task.task_id)

        routing_config = load_json("configs/routing.json")
        models_config = load_json("configs/models.json")
        mesa_config = load_json("configs/mesa.json")

        roles = decide_model_roles(task, models_config)
        need_gpt = decide_need_gpt_modeling(task, routing_config)
        mesa_needed, mesa_reason = decide_need_mesa(task, routing_config)

        write_status(job_id, "running", "pydantic_ai_planning", 0.25, task_file=str(task_file), task_id=task.task_id)
        agent_results, calls = run_expert_panel(task, roles, models_config)

        write_status(job_id, "running", "gpt_modeling", 0.45, task_file=str(task_file), task_id=task.task_id)
        modeling_result = build_modeling_result(task, mesa_needed=mesa_needed, mesa_reason=mesa_reason) if need_gpt else {}

        write_status(job_id, "running", "mesa", 0.65, task_file=str(task_file), task_id=task.task_id)
        mesa_result = run_mesa(task, modeling_result, mesa_config, mesa_needed=mesa_needed, mesa_reason=mesa_reason)

        write_status(job_id, "running", "writing_report", 0.85, task_file=str(task_file), task_id=task.task_id)
        report_path, artifact_path = write_outputs(task, modeling_result, mesa_result, agent_results, calls)
        write_status(job_id, "completed", "done", 1.0, report_path=report_path, artifact_path=artifact_path, task_file=str(task_file), task_id=task.task_id)
        print_run_summary(job_id, "completed", report_path, artifact_path, calls, None)
        _move_processed(task_file)
        return 0
    except Exception as exc:
        error = _format_error(exc)
        try:
            task = Task.model_validate(raw_task)
        except Exception:
            task = Task(task_id=job_id, task_type="analysis", question="invalid task placeholder")
        calls: list[AgentCallRecord] = []
        report_path, artifact_path = write_outputs(task, {}, {}, {}, calls, error=error)
        write_status(job_id, "failed", "failed", 1.0, report_path=report_path, artifact_path=artifact_path, error=error, task_file=str(task_file), task_id=job_id)
        print_run_summary(job_id, "failed", report_path, artifact_path, calls, error)
        return 1


def print_run_summary(job_id: str, status: str, report_path: str, artifact_path: str, calls: list[AgentCallRecord], error: str | None) -> None:
    summary = {
        "job_id": job_id,
        "status": status,
        "report_path": report_path,
        "artifact_path": artifact_path,
        "total_cost_usd": round(sum(call.cost_usd for call in calls), 8),
        "calls": [
            {
                "role": call.role,
                "provider": call.provider,
                "model": call.model,
                "status": call.status,
                "cost_usd": call.cost_usd,
                "error": call.error,
            }
            for call in calls
        ],
        "error": error,
    }
    print("HEBC_LITE_RUN_SUMMARY_START")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("HEBC_LITE_RUN_SUMMARY_END")


def _format_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return exc.json()
    return f"{type(exc).__name__}: {exc}"


def _move_processed(task_file: Path) -> None:
    if not task_file.exists() or "tasks/inbox" not in str(task_file).replace("\\", "/"):
        return
    processed = Path("tasks/processed")
    processed.mkdir(parents=True, exist_ok=True)
    target = processed / task_file.name
    if target.exists():
        target = processed / f"{task_file.stem}.processed{task_file.suffix}"
    task_file.replace(target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one HEBC-Lite task.")
    parser.add_argument("--task", required=True, help="Path to task JSON")
    args = parser.parse_args(argv)
    return run_task(args.task)


if __name__ == "__main__":
    sys.exit(main())
