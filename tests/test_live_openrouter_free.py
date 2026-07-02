import json
import os
import urllib.request
from pathlib import Path


def test_model_choice_report():
    key = os.getenv("OPENROUTER_API_KEY")
    assert key
    prompt = "Compare options A, B, C, D for a low-cost reversible income trial. Prefer low entry cost, stable net return, low accident risk, low compliance burden, and easy exit. Return Chinese JSON with ranking, reasons, risks, seven_day_trial, stop_conditions."
    payload = {"model": "deepseek/deepseek-v4-flash", "messages": [{"role": "system", "content": "You are a practical decision analyst. Return JSON only."}, {"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 1200}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(payload).encode("utf-8"), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"].get("content", "")
    usage = data.get("usage", {})
    cost = usage.get("prompt_tokens", 0) * 0.000000045 + usage.get("completion_tokens", 0) * 0.00000015
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    result = {"model": "deepseek/deepseek-v4-flash", "mapping": {"A": "option_1", "B": "option_2", "C": "option_3", "D": "option_4"}, "content": content, "usage": usage, "estimated_cost_usd": cost}
    Path("artifacts/model_choice_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("reports/model_choice_report.md").write_text("# Model Choice Report\n\n" + content + "\n", encoding="utf-8")
    assert content
