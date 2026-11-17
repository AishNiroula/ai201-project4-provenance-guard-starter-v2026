import json
import sys
import requests

BASE = "http://127.0.0.1:5000"
TEXTS = [
    "I walked to the library after class and found the book I needed on the second shelf. The librarian was kind and showed me where the quiet study rooms were.",
    "Last weekend my brother and I drove out to the lake. We forgot the sunscreen, argued about the map, and still had the best afternoon in months.",
    "The recipe calls for two cups of flour, but my grandmother always added a little more. She never measured anything, and somehow it came out perfect every time.",
    "My first job was washing dishes at a diner. It was loud and hot, and I loved the cooks, who taught me to swear in three languages and fold a napkin like a swan.",
    "We moved apartments in the rain. The couch would not fit through the door, so we took the door off, and then the neighbor came out with a drill.",
]
trial = sys.argv[1] if len(sys.argv) > 1 else "t1"

ok = 0
for i, text in enumerate(TEXTS):
    cid = None
    try:
        r = requests.post(f"{BASE}/submit", json={"text": text, "creator_id": f"appeal_{trial}_{i}"}, timeout=60)
        cid = r.json().get("content_id")
        a = requests.post(f"{BASE}/appeal", json={"content_id": cid, "reasoning": "I wrote this myself."}, timeout=30)
        status_ok = a.status_code == 200 and a.json().get("status") == "under_review"
        log = requests.get(f"{BASE}/log", timeout=30).json()["entries"]
        logged = any(e.get("content_id") == cid and e.get("event") == "appeal" and e.get("status") == "under_review" for e in log)
        good = status_ok and logged
    except Exception as exc:
        print("error:", exc)
        good = False
    print(f"appeal {i+1}: id={cid} status_changed_and_logged={good}")
    ok += good

u = requests.post(f"{BASE}/appeal", json={"content_id": "doesnotexist", "reasoning": "x"}, timeout=30)
unknown_ok = u.status_code in (400, 404)
print(f"unknown id returns error: {unknown_ok} (HTTP {u.status_code})")
print(f"RESULT: {ok}/5 valid appeals recorded, unknown-id error: {unknown_ok}")
