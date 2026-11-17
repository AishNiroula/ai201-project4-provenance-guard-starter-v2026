import json
import re
from pathlib import Path

F = "~" * 3
R = Path("results")
readme_path = Path("README.md")
readme = readme_path.read_text(encoding="utf-8")
assert "**The Shape**" in readme, "capstone block (What This Extends / The Shape) not found in README.md"
assert "**Running It**" not in readme, "already built; delete the generated sections first"


def rows_of(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d)\. ", line)
        if m:
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            out[int(m.group(1))] = c
    return out


def trials(prefix):
    return [rows_of(R / f"cap_{prefix}_{i}.md") for i in (1, 2, 3)]


def avg_of(path):
    return float(re.search(r"\*\*Average ([\d.]+) s", Path(path).read_text(encoding="utf-8")).group(1))


before, after = trials("before"), trials("after")
rb, ra = trials("redo_before"), trials("redo_after")

# ---- Run Log table
table = "| Criterion | Target | Before (trials 1, 2, 3) | After (trials 1, 2, 3) | Verdict after |\n|---|---|---|---|---|\n"
for n in range(1, 6):
    name = re.sub(r"^\d\. ", "", after[0][n][0])
    tgt = after[0][n][1]
    b = " / ".join(t[n][2] for t in before) if n != 5 else "not run on the old code (unit 8: 5/5 in all 3 trials)"
    a = " / ".join(t[n][2] for t in after)
    v = "**MET**" if all("MET" in t[n][3] for t in after) else "**MISSED**"
    table += f"| {n}. {name} | {tgt} | {b} | {a} | {v} |\n"

strict = "| Check | Before the improvement (trials 1, 2, 3) | After the improvement (trials 1, 2, 3) |\n|---|---|---|\n"
strict += "| C3 strict: all 8 records carry duration_ms | " + " / ".join(t[3][2] for t in rb) + " | " + " / ".join(t[3][2] for t in ra) + " |\n"
for n in (1, 2, 4, 5):
    name = re.sub(r"^\d\. ", "", ra[0][n][0])
    strict += f"| C{n} {name} | not re-run | " + " / ".join(t[n][2] for t in ra) + " |\n"

b_avg = [avg_of(R / f"cap_before_{i}.md") for i in (1, 2, 3)]
a_avg = [avg_of(R / f"cap_after_{i}.md") for i in (1, 2, 3)]

# ---- Instrumentation: log entries
entries = [json.loads(l) for l in Path("logs/audit.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
picked, seen = [], set()
for e in reversed(entries):
    k = (e.get("event"), e.get("reason"))
    if k not in seen:
        seen.add(k)
        picked.append(e)
for e in reversed(entries):
    if len(picked) >= 12:
        break
    if e not in picked:
        picked.append(e)
picked = sorted(picked[:12], key=lambda e: e.get("timestamp", ""))
sample = "\n".join(json.dumps(e, ensure_ascii=False) for e in picked)
crash = [e for e in entries if e.get("reason") == "internal_error"][-1]
old_fail = next((e for e in entries if e.get("reason") == "detector_failed"), None)
b1 = Path(R / "cap_before_1.md").read_text(encoding="utf-8")
miss = [l.strip("- ").strip() for l in b1.splitlines() if "new records 0" in l]
old_fail_txt = json.dumps(old_fail, ensure_ascii=False) if old_fail else "(no detector_failed entry found)"

cost = Path(R / "cap_cost.md").read_text(encoding="utf-8")
cost_table = cost[cost.index("| Measure"):cost.index("Runs (seconds)")].strip()
runs = re.search(r"Runs \(seconds\): (.*)", cost).group(1)
http_avg = float(re.search(r"warm HTTP requests \| ([\d.]+) s", cost).group(1))

sections = f"""
**Running It**

This is Path B, run locally, because the model is about 551 MB and I did not host it. RUNNING.md has the steps: clone, create a virtual environment, `pip install -r requirements.txt`, then one command, `python app.py`. A run from a fresh clone, with Python 3.13.5, is committed as results/clean_checkout_run.txt. In it the ping answered ok, a two-sentence text came back scored (unsure), and the one-character text came back as a 400 text_too_short. The first request after starting is slower because it loads the model (2.0 s in my cost run).

**Instrumentation**

Every request to /submit and /appeal ends in a JSON line in logs/audit.jsonl. Decisions record the scores, the guess, the text length, a 12-character SHA-256 fingerprint of the text (so a decision can be matched to its input without storing the text) and duration_ms. Refusals record the reason, http_status and duration_ms; refusals caught by the global handler also record the path and the Python error type. Twelve entries from my audit log, covering the kinds of entry I could find, oldest first:

{F}
{sample}
{F}

**The failed run.** I forced a stage inside /submit to raise (the check script replaces scoring.combine_signals with a function that raises RuntimeError). After the extension, the log alone says what happened: reason internal_error, http_status 500, error_type RuntimeError, path /submit, and how long it took.

{F}
{json.dumps(crash, ensure_ascii=False)}
{F}

Before the extension the same forced crash returned an HTML error page and left no record, and so did a GET to /submit: from results/cap_before_1.md, "{miss[0] if miss else '?'}" and "{miss[1] if len(miss) > 1 else '?'}". The only trace of the other old failure (a one-character text returning 503 in unit 8) is this entry, which says detector_failed and nothing about what the user did wrong:

{F}
{old_fail_txt}
{F}

**What It Costs**

Measured with cap_cost.py, an average over 10 warm HTTP requests to a running server (one warm-up request first, then 10 timed ones):

{cost_table}

Runs (seconds): {runs}

One request averages {http_avg:.3f} s of compute, so 100 requests (the daily limit for one creator) is about {http_avg * 100:.1f} s and 1,000 requests is about {http_avg * 1000:.0f} s. There is no money cost per request because the model runs on my machine and no API is called; the real costs are memory (about 906 MB peak once the model is loaded) and a 2.0 s first request while it loads. A host with 1 GB of memory would be tight. The extension added no measurable time: the in-process average over 10 warm requests was {", ".join(f"{x:.2f}" for x in b_avg)} s per trial before and {", ".join(f"{x:.2f}" for x in a_avg)} s after (that check skips the network, so it reads lower than the HTTP number above).

**Run Log and Verdicts**

The criteria are in criteria.md, committed as "add capstone criteria" (c848b01) before any result was committed. Each was run three times before the extension (the unit 8 code, app.py from d25f1f4) and three times after:

{table}
Diagnoses, from the before runs: C1 failed because the route turned the detector's "too short" error into a 503 (the generic `except Exception` caught it). C2 failed because Flask answers an unplanned crash with an HTML page and nothing is logged, since the route's own error handling never saw it. C3 failed because the refusal records had no http_status, and a 405 or a crash left no record at all (0 new records for those two kinds). C4 was met on both sides, so it measured nothing: 0.06 s against a 3.0 s limit. C5 was not run on the old code; its unit 8 result was 5/5 three times.

Two things about the runs themselves. C5 in the after trials ran against the server I had already started with the capstone code; the first strict run (cap_strict_after_*) shows C5 MISSED because the server was not running, which is a harness problem and not a regression. And my first strict "before" runs (cap_strict_before_*) were invalid: they ran after the improvement was already in the code (they read 8/8, as the after runs did), so I redid them from the commit before the improvement; those are the cap_redo_* files used in The Improvement.

**The Improvement**

**What I changed:** One change to app.py. A before_request hook records the start time, and the global error handler now writes duration_ms into its record using it. Before this, only the route's own refusals recorded duration; the 405 and the unplanned 500 did not, which is why my C3 exempted them.

**Which diagnosis pointed at it:** C3. I wrote the exemption into the criterion because I knew those two records had no duration, so a passing C3 hid the gap. To measure it I added a strict mode to the check (--strict: all 8 records need duration_ms) and ran it before and after.

**Run log, three trials each, before from app.py at the commit before the improvement:**

{strict}
**Did it help, and how do I know:** It helped on what it targeted, 6/8 to 8/8 in all three trials, from logs/audit.jsonl: the 500 record now reads duration_ms {crash.get("duration_ms")} and the 405 record carries duration_ms 0 (a request refused before any work rounds to 0 ms, so that number says "fast", not "missing"). The other criteria were re-run in the same trials and stayed MET. The cost is two small functions and a hook that runs on every request. The caveat is that the check only proves the two handler-level kinds on /submit; I did not test /appeal.

**What's Still Broken**

- **C4 is too loose.** I set 3.0 s from my memory of unit 8's one-to-two-second requests and never measured first. The result is 0.068 s, so a slowdown of more than 40 times would still pass. I would set it from a measured baseline (for example 0.15 s). I did not change it because the criteria are fixed before the results.
- **C1 to C4 run through Flask's test client, in-process.** That skips the network, the rate limiter (I switch it off for the timing) and the server process. A failure that only happens over a real connection, such as a client that disconnects mid-request, is untested. Only C5 and the cost measurement use real HTTP.
- **C3 covers /submit only.** I did not check that the refusals from /appeal (missing fields, unknown id) leave a record with a status. I would add 3 appeal cases to the check.
- **C1 uses five inputs.** The detector's real minimum length is unknown to me; text just above it is still too short to mean anything and gets scored.
- **Only /submit and /appeal failures are logged.** The global handler writes a record only for those two paths, by design, so requests to other URLs leave no record.
- **C5 checks appeals, not scoring.** The extension touched the code around the scoring path and I did not re-run the unit 8 label scenarios on it. I would add the stand-in and clearly-AI scenarios to the check.
- **Unit 8's open problems are untouched,** as the scope says: label coverage (criterion 3) is still MISSED, FP05 is still labeled ai, and 9 of 10 evasion attacks still get through.

**How I Used AI**

**Moment 1**

- *What I asked for:* Help choosing what to extend and which shape, building on units 7 and 8.
- *What came back:* Shape B (harden against failure), chosen because my unit 8 attack MF02 had shown a real bug, and a scope that listed what I would not touch.
- *What I changed:* Nothing. I kept the scope and wrote it into the README before building.

**Moment 2**

- *What I asked for:* The code for the three failure-handling changes and the check scripts.
- *What came back:* Three patches to app.py and cap_check.py. The first run of cap_check.py exited with "could not find combine_signals" because the script assumed how app.py imports scoring; the assistant had not seen that file. It also told me to run cap_cost.py without giving me the file.
- *What I changed:* I ran everything and pasted the real output back each time. The assistant fixed the script (patching scoring.combine_signals directly) and supplied the missing file; the committed before and after results are from the fixed versions.

**Moment 3**

- *What I asked for:* The five criteria; I asked the assistant to pick fair numbers for me.
- *What came back:* Five criteria with targets and reasons, which I committed unchanged as "add capstone criteria" before running anything. They are the assistant's proposals and not my own judgement; the weakest, C4, turned out to be too loose.
- *What I changed:* Nothing before the runs. I report C4's looseness above instead of editing it.

**Moment 4**

- *What I asked for:* The improvement, with a before and after.
- *What came back:* A duration fix and a strict check. My first before and after runs were identical (8/8 both), which meant the "before" runs had run after the fix was already applied. I pasted the numbers, the assistant pointed out that identical before and after cannot show an improvement, and we redid the before runs from git.
- *What I changed:* I kept the invalid runs in the repo and said so in Run Log and Verdicts, and used the redone runs as the evidence.
"""
readme_path.write_text(readme.rstrip() + "\n" + sections, encoding="utf-8")
print("README capstone sections written")
