import json, re
from pathlib import Path

entries = [json.loads(l) for l in Path("logs/audit.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

def hits(creator, event=None, prefix=False):
    out = []
    for e in entries:
        c = e.get("creator_id") or ""
        ok = c.startswith(creator) if prefix else c == creator
        if ok and (event is None or (e.get("event") or "decision") == event):
            out.append(e)
    return out

def trial_guess(creator, t):
    h = hits(creator, "decision")
    return h[-3 + t].get("guess") if len(h) >= 3 else None

stand = [f"eval_STAND-IN hum_{i}" for i in range(1, 11)]
flagged = [sum(trial_guess(c, t) == "ai" for c in stand) for t in range(3)]
ai_avg = sum(hits(f"eval_clearly AI_{i}", "decision")[-1]["combined_score"] for i in range(1, 6)) / 5
hu_avg = sum(hits(f"eval_clearly huma_{i}", "decision")[-1]["combined_score"] for i in range(1, 6)) / 5
gap = ai_avg - hu_avg
cov = sorted({e["creator_id"] for e in entries if str(e.get("creator_id", "")).startswith("eval_label")})
distinct = [len({trial_guess(c, t) for c in cov}) for t in range(3)]
n_appeal = len([e for e in entries if e.get("event") == "appeal" and str(e.get("creator_id", "")).startswith("appeal_a")])
bad = ["eval_bad_empty", "eval_bad_missing", "eval_bad_huge", "eval_bad_null"]
ok5 = all(len(hits(c, "rejected")) >= 6 and not hits(c, "decision") for c in bad)

def verdict(ok):
    return "**MET**" if ok else "**MISSED**"

rows = [
    ("1. Own writing flagged as AI (**stand-in texts, not my own writing**)", "at most 1 of 10", [f"{n}/10" for n in flagged], all(n <= 1 for n in flagged)),
    ("2. Score spread, clearly AI minus clearly human (average)", "at least 0.3", [f"{gap:.2f}"] * 3, gap >= 0.3),
    ("3. All three labels reachable (label coverage scenario)", "3 of 3", [f"{n}/3" for n in distinct], all(n == 3 for n in distinct)),
    ("4. Appeal sets under_review and is logged; unknown id errors", "5 of 5", ["5/5"] * 3 if n_appeal == 15 else ["CHECK"] * 3, n_appeal == 15),
    ("5. Bad input returns 400 and is not logged as a decision", "5 of 5", ["5/5"] * 3 if ok5 else ["CHECK"] * 3, ok5),
]
table = "| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |\n|---|---|---|---|---|---|\n"
for name, target, runs, ok in rows:
    table += f"| {name} | {target} | {runs[0]} | {runs[1]} | {runs[2]} | {verdict(ok)} |\n"
print(table)

def counts(path):
    t = Path(path).read_text(encoding="utf-8")
    m = re.search(r"\*\*Totals: (\d+) held, (\d+) broke of \d+\.\*\* (.*?)\.\n", t)
    fam = {k: (int(a), int(b)) for k, a, b in re.findall(r"(\w+) (\d+) held / (\d+) broke", m.group(3))}
    return int(m.group(1)), int(m.group(2)), fam

bh, bb, bf = counts("results/attack_section_before.md")
ah, ab, af = counts("results/attack_section_after.md")
fam_table = "| Family | Before (held / broke) | After (held / broke) |\n|---|---|---|\n"
for k in bf:
    fam_table += f"| {k} | {bf[k][0]} / {bf[k][1]} | {af.get(k, ('-', '-'))[0]} / {af.get(k, ('-', '-'))[1]} |\n"
fam_table += f"| **Total** | **{bh} / {bb}** | **{ah} / {ab}** |\n"

after_text = Path("results/attack_section_after.md").read_text(encoding="utf-8")
after_table = after_text[after_text.index("**Totals:"):after_text.index("**Ten audit log entries")].rstrip()

def short(e):
    return f"combined {e['combined_score']} (model {e['model_score']}, style {e['style_score']}) -> {e['guess']}"
fp3b, fp3a = hits("attacker_FP03")[0], hits("attacker_FP03")[-1]
fp5a = hits("attacker_FP05")[-1]
s4b, s4a = hits("eval_STAND-IN hum_4")[0], hits("eval_STAND-IN hum_4")[-1]
evidence = ("~~~\nattacker_FP03 (careful non-native speaker)\n  before: " + short(fp3b) + "\n  after:  " + short(fp3a)
            + "\neval_STAND-IN hum_4 (the highest-scoring stand-in)\n  before: " + short(s4b) + "\n  after:  " + short(s4a)
            + "\nattacker_FP05 (technical documentation, still flagged)\n  after:  " + short(fp5a) + "\n~~~")

improvement = f"""
**What I changed:** One change. I raised AI_THRESHOLD in config.py from 0.69 to 0.75 and updated the matching number in the scoring.py docstring. The weights, the disagreement rule, the labels and the input checks are as they were. The 40-word cap in app.py::submit is written as AI_THRESHOLD minus 0.01, so it moved with the threshold (it now caps at 0.74), which is the same parameter and not a second change.

**Which diagnosis pointed at it:** The false positives. Ordinary human prose combined to 0.69 to 0.77 (8 of the 18 plain human texts I tested were labeled ai), overlapping the 0.66 to 0.76 where my clearly-AI texts landed, and signal one was the main driver (0.74 to 0.88 on plain prose). The label mapping decides who gets accused, so I moved the accusation line above where plain human text lands. Before choosing I tested two options against every score I had measured: raising the threshold to 0.75 flagged 0 of 10 stand-ins and reweighting signal one from 0.5 to 0.3 flagged 1 of 10, and both would break criterion 3. I chose the threshold because the reweight landed exactly on my target of at most 1 in 10 with no room.

**Run log after the change**, three trials each, nothing else changed in between (before: criteria 1 and 3 had 4/10 MISSED and 3/3 MET):

{table}
Criterion 3 is MISSED on my label-coverage scenario because its AI text combined to 0.6994, which now falls below 0.75 and is labeled unsure. The ai label is still reachable: clearly-AI texts 1 and 3 and attack EV10 got it in the after run. The failure is that I had tuned the old 0.69 threshold to make that one text reach ai.

### Attack Run — After

{fam_table}
{after_table}

**Did it help, and how do I know:** It helped on the target it aimed at, at a real cost.

- **Helped:** Criterion 1 went from 4/10 MISSED to 0/10 MET in all three trials, and false positives in the attack set went from 4 of 8 broke to 1 of 8 (FP05, technical documentation at 0.7745, is still labeled ai). Total broke went from {bb} to {ab} of 56. Evidence, from logs/audit.jsonl:

{evidence}

- **Cost:** The system now labels fewer AI texts ai. Across the 14 AI texts I tested it went from 5 caught to 3, and criterion 3 went from MET to MISSED. Evasion did not change (1 held, 9 broke) because those attacks were already getting unsure, and only EV10 at 0.863 ever reached ai.
- **Caveat:** I chose 0.75 after seeing these same texts. The highest stand-in scored 0.7453, only 0.0047 under the threshold, so the criterion 1 result is partly fitted to the stand-ins and says nothing about my own writing.
"""

still = """
**What I'd do about each remaining failure, and why I stopped:**

- **Criterion 3 (MISSED):** The ai label is reachable but my label-coverage scenario no longer demonstrates it. I would replace its AI text with one that scores well above 0.75 and require three different AI texts to produce ai. I did not change the criterion or the test because this unit allows one change.
- **FP05, technical documentation labeled ai (0.7745):** Both signals are high on it (model 0.8005, style 0.7485). Raising the threshold again to clear it (to about 0.78) would leave only EV10 labeled ai, so I would need a signal that recognizes technical register instead. I stopped because that is a new signal, not a one-line change.
- **Evasion, 9 of 10 attacks (broke):** AI text sits just above the threshold and both signals are easy to move. Typos lower signal one, uneven sentences lower signal two, and semicolon padding makes the splitter see one sentence so signal two returns no opinion. I would split sentences on semicolons, clean obvious typos before scoring, and add a third signal. I stopped because each of those is its own change.
- **MF02, single character returned 503:** detector.py raises ValueError for text that is too short, and app.py::submit reports it as a server error. I would catch ValueError and return a 400 saying the text is too short. This is the cheapest fix left and I held it back to keep the before-and-after comparison to one change.
- **PI02 labeled human:** both signals read the odd formatting as human, not instruction-following. I would not fix it directly, because it comes from the same weakness as the evasions.
- **Criterion 1 on my own writing:** unmeasured. The result is on stand-in texts, and I would run my own ten pieces before relying on it.

**The trade I'd make if this ran for real:** Fewer wrong accusations means more AI text getting through: after my change the system accused 1 of 18 plain human texts instead of 8, and caught 3 of 14 AI texts instead of 5. I would keep it that way on a writing site, because a wrong accusation costs a real person and a missed AI piece costs little, and the people who pay are moderators and honest writers competing with AI text that slips past. I would send every unsure item to a human reviewer instead of treating it as a pass.
"""

moments = """

**Moment 3**

- *What I asked for:* I had not collected ten pieces of my own writing for criterion 1, so I asked for ten human-style texts to run the test.
- *What came back:* Ten plain paragraphs written by the AI assistant, not by me.
- *What I changed:* Nothing in the texts. I labeled them "STAND-IN human writing (NOT my own)" in scenarios.py and in the run log, and I report criterion 1 as a result on stand-ins. Criterion 1 on my own writing is still unmeasured.

**Moment 4**

- *What I asked for:* After the attack run and my criteria run, I asked what the one improvement should be.
- *What came back:* The assistant tested threshold and reweighting options against my measured scores and recommended raising AI_THRESHOLD from 0.69 to 0.75, warning that it would reduce AI detection and break my label-coverage criterion. It also wrote the scripts that built the Attack Run and Run Log sections of this README from logs/audit.jsonl.
- *What I changed:* I made that one change, re-ran the attack set and my criteria, and reported the cost: criterion 3 went from MET to MISSED. I ran the scripts, and the numbers in those sections come from my audit log.
"""

readme = Path("README.md").read_text(encoding="utf-8")

def sub_section(text, start, end_pat, body):
    pat = re.compile(r"(^## " + re.escape(start) + r"\n).*?(?=" + end_pat + r")", re.S | re.M)
    assert pat.search(text), start
    return pat.sub(lambda m: m.group(1) + body + "\n", text, count=1)

readme = sub_section(readme, "The Improvement", r"^## What's Still Broken\n", improvement + "\n---\n")
readme = sub_section(readme, "What's Still Broken", r"^---\s*\n+📖|\Z", still)

for old, new in [
    ("The AI threshold (0.69)", "The AI threshold (0.75)"),
    ("AI threshold 0.69, minimum", "AI threshold 0.75 (raised from 0.69 in the improvement, see The Improvement), minimum"),
    ("| unsure | 0.35 - 0.69 |", "| unsure | 0.35 - 0.75 |"),
    ("| high-confidence AI | 0.69 - 1.00 |", "| high-confidence AI | 0.75 - 1.00 |"),
]:
    print(("updated: " if old in readme else "NOT FOUND: ") + old)
    readme = readme.replace(old, new)

m = re.search(r"\n---\s*\n+## Rate Limiting", readme)
if m:
    readme = readme[:m.start()] + moments + readme[m.start():]
else:
    Path("results/how_i_used_ai_moments.md").write_text(moments, encoding="utf-8")
    print("NOTE: could not find the Rate Limiting heading; wrote results/how_i_used_ai_moments.md, paste it under How I Used AI by hand")
Path("README.md").write_text(readme, encoding="utf-8")
print("README updated: The Improvement, What's Still Broken, How I Used AI, threshold numbers")
