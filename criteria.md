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
