from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .schemas import JobStatus, JobStatusValue

STATUS_DIR = Path("jobs/status")
TZ = ZoneInfo("Asia/Seoul")


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def status_path(job_id: str) -> Path:
    return STATUS_DIR / f"{job_id}.status.json"


def _read_raw(job_id: str) -> dict | None:
    path = status_path(job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_status(
    job_id: str,
    status: JobStatusValue,
    stage: str,
    progress: float,
    report_path: str | None = None,
    artifact_path: str | None = None,
    error: str | None = None,
    task_id: str | None = None,
    task_file: str | None = None,
) -> JobStatus:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    existing = _read_raw(job_id) or {}
    started_at = existing.get("started_at") or now_iso()
    model = JobStatus(
        job_id=job_id,
        task_id=task_id or existing.get("task_id") or job_id,
        status=status,
        stage=stage,
        progress=progress,
        task_file=task_file or existing.get("task_file"),
        report_path=report_path if report_path is not None else existing.get("report_path"),
        artifact_path=artifact_path if artifact_path is not None else existing.get("artifact_path"),
        started_at=started_at,
        updated_at=now_iso(),
        error=error,
    )
    path = status_path(job_id)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(path)
    return model


def read_status(job_id: str) -> JobStatus:
    data = _read_raw(job_id)
    if data is None:
        raise FileNotFoundError(f"status not found: {job_id}")
    return JobStatus.model_validate(data)


def mark_failed(job_id: str, error: str) -> JobStatus:
    return write_status(job_id, "failed", "failed", 1.0, error=error)


def mark_completed(job_id: str, report_path: str, artifact_path: str) -> JobStatus:
    return write_status(job_id, "completed", "done", 1.0, report_path=report_path, artifact_path=artifact_path, error=None)
