# Capstone check: before_2

| Criterion | Target | Result | Verdict |
|---|---|---|---|
| 1. Too-short inputs return 400 text_too_short | 5 of 5, 0 five-hundreds | 0/5, 5 5xx | **MISSED** |
| 2. Forced crash answers JSON 500 internal_error | 10 of 10 | 0/10 | **MISSED** |
| 3. Each refusal leaves one record with reason, status, duration | 8 of 8 | 0/8 | **MISSED** |
| 4. Average warm /submit time over 10 runs | at most 3.0 s | 0.06 s | **MET** |
| 5. Appeals still work (check_appeals.py) | 5/5 + unknown id 404 | not run | not run |

**Criterion 3 detail**

- missing text: HTTP 400, new records 1, MISSING
- empty text: HTTP 400, new records 1, MISSING
- missing creator: HTTP 400, new records 1, MISSING
- too long: HTTP 400, new records 1, MISSING
- too short: HTTP 503, new records 1, MISSING
- not JSON: HTTP 400, new records 1, MISSING
- GET /submit (405): HTTP 405, new records 0, MISSING
- forced crash (500): HTTP 500, new records 0, MISSING

**Criterion 4 runs (seconds):** 0.07, 0.07, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06

**Average 0.06 s per warm request; x100 requests/day = 0.1 minutes of CPU.**
