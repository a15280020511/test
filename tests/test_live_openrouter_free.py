import base64
import json
import os
import urllib.request
from pathlib import Path


def test_model_choice_report():
    key = os.getenv("OPENROUTER_API_KEY")
    assert key
    prompt_b64 = "5L2g5piv5LiA5Liq5Yqh5a6e55qE6IGM5Lia5pS25YWl5Yaz562W5YiG5p6Q5biI44CC5Zyw54K577ya56aP5bee44CC5q+U6L6D5Zub5Liq6YCJ6aG577yaCkE95byA572R57qm6L2mCkI95Y+R5pmu6YCa5b+r6YCSCkM95Y+R5py15py14oCZL+eUn+e6v+WNsuaXtuS6peiAgeéCkQ95Y+R5aSW5Y2WCueUqOaIt+iƒjOaZrO+8muebrueJjeS4iuWknOePreS/neWuie+8jOaDs+WinuWKoOaUtuWFpe+8jOS9huaYr+imgeaxguWQjOaIkOacrOOAgeS9juç»´æŠ¤ã€�å¯é€†é€€å‡ºï¼Œä¸æƒ³é«˜æŠ¼é‡‘ã€�ä¸æƒ³ä¹°è½¦æˆ–ç§Ÿè½¦å¥—ç‰¢ï¼Œä¸æƒ³ä¸¥é‡ä¼¤èº«ä½“ï¼Œä¼˜å…ˆç¨³å®šå‡€æ”¶å…¥ã€‚Cuivt+ino+WbnuS4peagvCBKU09O77yM5a2X5q616YCa5YyF5ous77yacnJhbmtpbmfvvIjku47mnIDpgJDlkIjmjqTliLDmnIDkuI3pgJDlkIjvvIksCmNvcmVfY29uY2x1c2lvbu+8jApyZWFzb25zX2J5X29wdGlvbu+8jApyaXNrc19ieV9vcHRpb27vvIwKbmV0X2luY29tZV9sb2dpY+WvvOivt+ivt+ivt+WkmuS4jeWPl+eZu+a1geawtO+8jOimgeeci+WHgOaUtuWFpeOAgeaKv+é‡‘ã€�è½¦è¾†/ç”µåŠ¨è½¦æˆæœ¬ã€�ç½šæ¬¾ã€�ç­‰å¾…æ—¶é—´ã€�ç–²åŠ³å’Œäº‹æ•…é£Žé™©ï¼‰,
c2V2ZW5fZGF5X3RyaWFsX3BsYW7vvIwKc3RvcF9jb25kaXRpb25z77yMCmZpbmFsX3JlY29tbWVuZGF0aW9u44CCCuS4jeimgeWGmeept+ivn+ï¼Œè¦ç»™å¯æ‰§è¡Œç»“è®ºã€‚"
    prompt = base64.b64decode(prompt_b64).decode("utf-8", errors="replace")
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
