"""Cost of one /submit. Usage: python cap_cost.py   (python app.py must be running for the HTTP part)"""
import json
import os
import resource
import sys
import time
import urllib.request
from pathlib import Path

os.environ["AI201_RATE_LIMITS"] = "0"
GOOD = ("The committee met on Tuesday to review the budget for the coming year. "
        "Several members raised concerns about the cost of the new library wing, "
        "and after a long discussion they agreed to postpone the vote until the "
        "next meeting so that the figures could be checked again by an outside firm.")

t0 = time.perf_counter()
import app as appmod  # noqa: E402
t_import = time.perf_counter() - t0
t0 = time.perf_counter()
appmod.app.test_client().post("/submit", json={"text": GOOD, "creator_id": "cost_cold"})
t_cold = time.perf_counter() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024 if sys.platform == "darwin" else 1024)


def post(tag):
    body = json.dumps({"text": GOOD, "creator_id": f"cost_{os.getpid()}_{tag}"}).encode()
    req = urllib.request.Request("http://127.0.0.1:5000/submit", data=body,
                                 headers={"Content-Type": "application/json"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()
        assert r.status == 200, r.status
    return time.perf_counter() - t


try:
    post("warmup")
except Exception as e:
    sys.exit(f"HTTP part failed ({e}). Is python app.py running?")
times = [post(i) for i in range(10)]
avg = sum(times) / len(times)
size = 0
for p in Path.home().glob(".cache/huggingface/hub/models--gpt2*"):
    size += sum(f.stat().st_size for f in (p / "blobs").glob("*") if f.is_file())
out = f"""# Cost of one /submit

| Measure | Value |
|---|---|
| Average over 10 warm HTTP requests | {avg:.3f} s |
| Fastest / slowest of the 10 | {min(times):.3f} s / {max(times):.3f} s |
| Cold start: import app | {t_import:.1f} s |
| Cold start: first request (loads the model) | {t_cold:.1f} s |
| Peak memory of a process that loaded the model | {rss:.0f} MB |
| GPT-2 weights on disk (Hugging Face cache) | {size / 1e6:.0f} MB |
| Money per request | 0 (the model runs on this machine, no API) |
| 100 requests (the daily rate limit) | {avg * 100:.1f} s of compute |

Runs (seconds): {", ".join(f"{t:.3f}" for t in times)}
"""
Path("results").mkdir(exist_ok=True)
Path("results/cap_cost.md").write_text(out, encoding="utf-8")
print(out)
