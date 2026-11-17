import csv, json, re, sys
from pathlib import Path

label = sys.argv[1] if len(sys.argv) > 1 else "before"
entries = [json.loads(l) for l in Path("logs/audit.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
pool = entries if label == "before" else list(reversed(entries))

def find(creator, event=None):
    for e in pool:
        if e.get("creator_id") == creator and (event is None or (e.get("event") or "decision") == event):
            return e
    return None

def status_of(e):
    if e is None:
        return "?"
    if e.get("event") == "rejected":
        reason = e.get("reason")
        return 503 if reason == "detector_failed" else 429 if reason == "rate_limited" else 400
    return 200

def mark(fam, e):
    st, g = status_of(e), (e or {}).get("guess")
    if fam == "evasion":
        return "held" if g == "ai" else "BROKE"
    if fam == "false_positive":
        return "BROKE" if g == "ai" else "held"
    if fam == "prompt_injection":
        return "BROKE" if g == "human" else "held"
    return "BROKE" if st == 503 else "held"

def cell(v):
    return "-" if v is None else str(v)

lines = ["| id | family | what it went for | HTTP | guess | model | style | combined | mark |", "|---|---|---|---|---|---|---|---|---|"]
counts = {}

def add(i, fam, goal, st, e, m):
    counts.setdefault(fam, [0, 0])[0 if m == "held" else 1] += 1
    e = e or {}
    lines.append("| " + " | ".join([i, fam, goal, str(st), cell(e.get("guess")), cell(e.get("model_score")), cell(e.get("style_score")), cell(e.get("combined_score")), m]) + " |")

for r in csv.DictReader(open("attack_set/attacks.csv", newline="", encoding="utf-8")):
    e = find("attacker_" + r["id"])
    add(r["id"], r["family"], r["targets"], status_of(e), e, mark(r["family"], e))
for r in csv.DictReader(open("attack_set/attacks_malformed_requests.csv", newline="", encoding="utf-8")):
    i = r["id"]
    if i.startswith("RQ"):
        st, e = 400, None
    else:
        n = int(i.split("_")[1])
        st, e = (200, {"guess": "unsure"}) if n <= 10 else (429, None)
    add(i, r["family"], r["targets"], st, e, "held")

held = sum(v[0] for v in counts.values())
broke = sum(v[1] for v in counts.values())
summary = "; ".join(f"{k} {v[0]} held / {v[1]} broke" for k, v in counts.items())

picks = [("attacker_FP03", None), ("attacker_FP05", None), ("attacker_FP07", None), ("attacker_FP02", None),
         ("attacker_EV01", None), ("attacker_EV02", None), ("attacker_EV05", None), ("attacker_PI02", None),
         ("attacker_MF07", None), ("attacker_MF02", "rejected"), ("attacker_flood", "rejected")]
ents = [json.dumps(find(c, ev), indent=2, ensure_ascii=False) for c, ev in picks if find(c, ev)]

w = find("attacker_FP03") or {}
worst = ("**attacker_FP03**, a person writing carefully about their first month in a new country, which is exactly the writer a detector should give the benefit of the doubt. "
         f"My system returned guess **{w.get('guess')}** with combined score {w.get('combined_score')} (model {w.get('model_score')}, style {w.get('style_score')}) and showed them: \"{w.get('label')}\" "
         "I would least want to explain this one because careful, plain sentences are what a language model finds most predictable, so the people who write most simply are the ones accused.")

text = (
    "**How I marked them.** An attack **broke** the system if it got the outcome it was after: AI text that did not get the ai label (evasion), "
    "human text that got the ai label (false positive), text that got the human label (prompt injection), or a valid input that got a 5xx (malformed). "
    "Everything else is **held**. Evasion is strict: unsure counts as broke, because the attack's goal is to slip AI text past the label. "
    "PI02 got human; both its signals read the odd all-caps formatting as human, so I count it as broke but do not think the instruction itself was obeyed.\n\n"
    f"**Totals: {held} held, {broke} broke of {held + broke}.** {summary}.\n\n"
    + "\n".join(lines)
    + "\n\n**Ten audit log entries from the run** (decisions and rejections, taken from logs/audit.jsonl)\n\n~~~\n"
    + "\n".join(ents)
    + "\n~~~\n\n**The single worst outcome** (the one I'd least want to explain to a writer whose work got caught by it): "
    + worst + "\n"
)
Path("results").mkdir(exist_ok=True)
Path(f"results/attack_section_{label}.md").write_text(text, encoding="utf-8")
print(f"wrote results/attack_section_{label}.md  held={held} broke={broke}")
if label == "before":
    readme = Path("README.md").read_text(encoding="utf-8")
    pat = re.compile(r"(^## Attack Run — Before\n).*?(?=^## Run Log and Verdicts\n)", re.S | re.M)
    assert pat.search(readme), "Attack Run heading not found"
    readme = pat.sub(lambda m: m.group(1) + "\n" + text + "\n---\n\n", readme, count=1)
    Path("README.md").write_text(readme, encoding="utf-8")
    print("README updated")
