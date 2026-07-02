from hebc_lite.status import read_status, write_status


def test_status_write_and_read(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_status("job1", "running", "planning", 0.3, task_id="job1", task_file="tasks/inbox/job1.json")
    status = read_status("job1")
    assert status.job_id == "job1"
    assert status.status == "running"
    assert status.progress == 0.3
