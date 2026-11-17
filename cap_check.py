"""Capstone checks. Usage: python cap_check.py <label> [--no-appeals]"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ["AI201_RATE_LIMITS"] = "0"   # the limiter would block the 10-run timing
import app as appmod                    # noqa: E402

label = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "run"
client = appmod.app.test_client()
LOG = Path("logs/audit.jsonl")
GOOD = ("The committee met on Tuesday to review the budget for the coming year. "
        "Several members raised concerns about the cost of the new library wing, "
        "and after a long discussion they agreed to postpone the vote until the "
        "next meeting so that the figures could be checked again by an outside firm.")


def find(obj, key):
    if isinstance(obj, dict):
        if obj.get(key) is not None:
            return obj[key]
        for v in obj.values():
            r = find(v, key)
            if r is not None:
                return r
    return None


def log_lines():
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]


def post(text, creator="cap_check"):
    return client.post("/submit", json={"text": text, "creator_id": creator})


def force_crash():
    """Make a stage inside /submit raise an error nobody planned for."""
    def boom(*a, **k):
        raise RuntimeError("forced failure")
    import scoring as scoring_mod
    orig = scoring_mod.combine_signals
    undo = [(scoring_mod, "combine_signals", orig)]
    scoring_mod.combine_signals = boom
    for k, v in list(vars(appmod).items()):
        if v is orig:
            undo.append((appmod, k, v))
            setattr(appmod, k, boom)
    det = getattr(appmod, "detector", None)
    if det is not None and hasattr(det, "model_signal"):
        undo.append((det, "model_signal", det.model_signal))
        det.model_signal = lambda t: 0.5          # skip the slow model

    def restore():
        for o, n, f in undo:
            setattr(o, n, f)
    return restore


rows = []

# 1. too-short inputs -> 400 text_too_short, never 5xx
short = ["a", "ok", "Hi.", "yes no", "?"]
good1, five_xx = 0, 0
for t in short:
    r = post(t)
    five_xx += r.status_code >= 500
    good1 += r.status_code == 400 and r.is_json and r.get_json().get("error") == "text_too_short"
rows.append(("1. Too-short inputs return 400 text_too_short", "5 of 5, 0 five-hundreds",
             f"{good1}/5, {five_xx} 5xx", good1 == 5 and five_xx == 0))

# 2. forced crash -> JSON 500 internal_error
restore = force_crash()
good2 = 0
for _ in range(10):
    r = post(GOOD, "cap_crash")
    good2 += r.status_code == 500 and r.is_json and r.get_json().get("error") == "internal_error"
restore()
rows.append(("2. Forced crash answers JSON 500 internal_error", "10 of 10", f"{good2}/10", good2 == 10))

# 3. every refused /submit request leaves one record with reason + status (+ duration)
cases = [  # (name, send, written_by_global_handler)
    ("missing text", lambda: client.post("/submit", json={"creator_id": "c"}), False),
    ("empty text", lambda: post(""), False),
    ("missing creator", lambda: client.post("/submit", json={"text": GOOD}), False),
    ("too long", lambda: post("word " * 1200), False),
    ("too short", lambda: post("a"), False),
    ("not JSON", lambda: client.post("/submit", data="hello", content_type="text/plain"), False),
    ("GET /submit (405)", lambda: client.get("/submit"), True),
    ("forced crash (500)", None, True),
]
good3, detail = 0, []
for name, send, handler in cases:
    restore = force_crash() if send is None else None
    before = len(log_lines())
    r = send() if send else post(GOOD, "cap_log")
    if restore:
        restore()
    new = log_lines()[before:]
    ok = (len(new) == 1 and r.is_json
          and find(new[0], "reason") == r.get_json().get("error")
          and find(new[0], "http_status") == r.status_code
          and (handler or find(new[0], "duration_ms") is not None))
    good3 += bool(ok)
    detail.append(f"- {name}: HTTP {r.status_code}, new records {len(new)}, {'ok' if ok else 'MISSING'}")
rows.append(("3. Each refusal leaves one record with reason, status, duration",
             "8 of 8", f"{good3}/8", good3 == 8))

# 4. warm latency over 10 runs
post(GOOD, "cap_warmup")
times = []
for i in range(10):
    t0 = time.perf_counter()
    r = post(GOOD, f"cap_time_{i}")
    times.append(time.perf_counter() - t0)
    assert r.status_code == 200, f"timing request failed: {r.status_code}"
avg = sum(times) / len(times)
rows.append(("4. Average warm /submit time over 10 runs", "at most 3.0 s", f"{avg:.2f} s", avg <= 3.0))

# 5. regression: appeals still work (needs python app.py running)
if "--no-appeals" in sys.argv:
    rows.append(("5. Appeals still work (check_appeals.py)", "5/5 + unknown id 404", "not run", None))
else:
    out = subprocess.run([sys.executable, "check_appeals.py", f"cap_{label}"],
                         capture_output=True, text=True, timeout=300).stdout
    ok5 = "RESULT: 5/5 valid appeals recorded, unknown-id error: True" in out
    rows.append(("5. Appeals still work (check_appeals.py)", "5/5 + unknown id 404",
                 "5/5" if ok5 else "FAILED (is python app.py running?)", ok5))

table = "| Criterion | Target | Result | Verdict |\n|---|---|---|---|\n"
for n, tgt, res, ok in rows:
    table += f"| {n} | {tgt} | {res} | {'**MET**' if ok else ('not run' if ok is None else '**MISSED**')} |\n"
body = (f"# Capstone check: {label}\n\n{table}\n**Criterion 3 detail**\n\n" + "\n".join(detail)
        + "\n\n**Criterion 4 runs (seconds):** " + ", ".join(f"{t:.2f}" for t in times)
        + f"\n\n**Average {avg:.2f} s per warm request; x100 requests/day = {avg * 100 / 60:.1f} minutes of CPU.**\n")
Path("results").mkdir(exist_ok=True)
Path(f"results/cap_{label}.md").write_text(body, encoding="utf-8")
print(body)
