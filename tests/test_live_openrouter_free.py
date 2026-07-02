import base64
import json
import os
import urllib.request
from pathlib import Path


def test_model_choice_report():
    key = os.getenv("OPENROUTER_API_KEY")
    assert key
    prompt_b64 = "5L2g5piv5LiA5Liq5Yqh5a6e55qE6IGM5Lia5pS25YWl5Yaz562W5YiG5p6Q5biI44CC5Zyw54K577ya56aP5bee44CC5q+U6L6D5Zub5Liq6YCJ6aG577yaCkE95byA572R57qm6L2mCkI96YCB5pmu6YCa5b+r6YCSCkM96YCB5py05py0L+eUn+mynOWNs+aXtumFjemAgQpEPemAgeWkluWNlgrnlKjmiLfog4zmma/vvJrnm67liY3kuIrlpJznj63kv53lronvvIzmg7Plop7liqDmlLblhaXvvIzkvYbopoHmsYLkvY7miJDmnKzjgIHkvY7nu7TmiqTjgIHlj6/pgIbpgIDlh7rvvIzkuI3mg7Ppq5jmirzph5HjgIHkuI3mg7PkubDovabmiJbnp5/ovablpZfniaLvvIzkuI3mg7PkuKXph43kvKTouqvkvZPvvIzkvJjlhYjnqLPlrprlh4DmlLblhaXjgIIK6K+36L+U5Zue5Lil5qC8IEpTT07vvIzlrZfmrrXljIXmi6zvvJoKcmFua2luZ++8iOS7juacgOmAguWQiOWIsOacgOS4jemAguWQiO+8ie+8jApjb3JlX2NvbmNsdXNpb27vvIwKcmVhc29uc19ieV9vcHRpb27vvIwKcmlza3NfYnlfb3B0aW9u77yMCm5ldF9pbmNvbWVfbG9naWPvvIjor7TmmI7kuLrku4DkuYjkuI3og73lj6rnnIvmtYHmsLTvvIzopoHnnIvlh4DmlLblhaXjgIHmirzph5HjgIHovabovoYv55S15Yqo6L2m5oiQ5pys44CB572a5qy+44CB562J5b6F5pe26Ze044CB55ay5Yqz5ZKM5LqL5pWF6aOO6Zmp77yJ77yMCnNldmVuX2RheV90cmlhbF9wbGFu77yMCnN0b3BfY29uZGl0aW9uc++8jApmaW5hbF9yZWNvbW1lbmRhdGlvbuOAggrkuI3opoHlhpnnqbror53vvIzopoHnu5nlj6/miafooYznu5PorrrjgII="
    prompt = base64.b64decode(prompt_b64).decode("utf-8")
    payload = {"model": "deepseek/deepseek-v4-flash", "messages": [{"role": "system", "content": "You are a practical decision analyst. Return JSON only."}, {"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 2000}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(payload).encode("utf-8"), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"].get("content", "")
    usage = data.get("usage", {})
    cost = usage.get("prompt_tokens", 0) * 0.000000045 + usage.get("completion_tokens", 0) * 0.00000015
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    result = {"model": "deepseek/deepseek-v4-flash", "task": "fuzhou_work_options", "content": content, "usage": usage, "estimated_cost_usd": cost}
    Path("artifacts/model_choice_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("reports/model_choice_report.md").write_text("# Model Choice Report\n\n" + content + "\n", encoding="utf-8")
    assert content
