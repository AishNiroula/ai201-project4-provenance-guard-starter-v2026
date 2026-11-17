# Acceptance criteria — Provenance Guard

## 1. False positives

Of 10 pieces I wrote myself, at most 1 is labeled high-confidence AI, and this holds in every one of 3 trials.

**Why this target:** On a writing site, wrongly accusing a real writer costs more than missing an AI piece, so I accept some missed detections before I accept more than one false accusation in ten.

---

## 2. Score spread

The average combined score of 5 clearly-AI texts is at least 0.3 higher than the average of 5 clearly-human texts, in every one of 3 trials.

**Why this target:** If the two groups score close together, the score tells the reader nothing, and 0.3 is the smallest gap I would trust to mean something.

---

## 3. Label coverage

All 3 labels (high-confidence AI, high-confidence human, unsure) are reachable, and I can show one real submission that produces each.

**Why this target:** A label that no score can reach is dead text, and "unsure" is the one most likely to end up unreachable.

---

## 4. Appeal path

100% of appeals with a valid content_id set the status to under_review and appear in the log next to the original decision. An unknown content_id returns an error.

**Why this target:** A writer who appeals needs proof it was recorded, so there can be no silent failures.

---

## 5. Bad input

Missing text, empty text, or text over 5,000 characters returns a 400 error and is not logged as a decision.

**Why this target:** Bad input should not crash the service or fill the audit log with decisions that were never made.

## Capstone criteria (written before any capstone results)

**C1 (extension, bad path): Too-short text gets a 400.**
Target: each of 5 inputs ("a", "ok", "Hi.", "yes no", "?") returns 400 with error text_too_short, and none returns a 5xx (5 of 5).
Why: these are the inputs that crashed the detector in unit 8 (attack MF02 returned 503). I chose all five because a single 5xx is the bug itself, so 4 of 5 would not mean fixed.

**C2 (extension, bad path): An unplanned crash still answers in JSON.**
Target: with a stage forced to raise, 10 of 10 requests return HTTP 500 with a JSON body whose error is internal_error.
Why: the crash is forced the same way each time, so any HTML page or other status is a real miss. 10 requests, because the answer should not vary.

**C3 (extension): Every refused /submit request leaves exactly one log record.**
Target: for 8 kinds of refused request (missing text, empty text, missing creator, too long, too short, not JSON, GET /submit, forced crash), 8 of 8 leave exactly one new record whose reason matches the response error and whose http_status matches the response status. Records written by the route must also have duration_ms. The 405 and the forced 500 are written by the global handler, which cannot see the request start, so they are exempt from duration_ms.
Why: an audit log is only useful if every refusal is in it. I exempt duration for the two handler-level kinds because I know that gap exists.

**C4 (cost): Speed stays reasonable.**
Target: average of at most 3.0 seconds per warm /submit over 10 requests, after one warm-up request.
Why: in unit 8, requests took one to two seconds each once the model was loaded. 3.0 leaves room for noise but would catch the new logging doubling the time. I measure warm requests only because the first one loads the model.

**C5 (original system): Appeals still work.**
Target: check_appeals.py gives 5/5 valid appeals recorded and the unknown-id error (HTTP 404) in each of 3 trials.
Why: /appeal is from units 7 and 8, and the new error handler sits around it, so it is the likeliest thing to break by accident.
