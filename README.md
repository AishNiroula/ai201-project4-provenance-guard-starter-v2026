# Provenance Guard

Finished milestone 1
>
> 
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

A submission goes through seven steps:

1. `POST /submit` receives JSON with `text` and `creator_id` (app.py::submit).
2. Input checks run first. Missing or empty text, text over 5,000 characters, or a missing creator_id returns a 400 and is logged as a rejection, not a decision.
3. Signal one (detector.py::model_signal) runs a local GPT-2 model and scores how predictable the text is.
4. Signal two (stylometry.py::style_signal) measures sentence-length spread, vocabulary variety and punctuation.
5. scoring.py::combine_signals merges the two into one 0-1 score. In app.py, texts under 40 words are capped just below the AI threshold.
6. scoring.py::score_to_label turns the score into a guess and a plain-English label.
7. audit.py::log_decision writes both signal scores, the combined score, the label, text length and duration to logs/audit.jsonl, and the response returns the content_id, guess, confidence, label and both signal scores.

`POST /appeal` takes a content_id and the writer's reasoning, checks the id exists (404 if not), appends an appeal entry with status `under_review` beside the original decision, and confirms.

---

## Signals and Scoring

### Signal one: the model signal

**What it measures:** How predictable the text is to GPT-2 (perplexity, mapped to 0-1, higher = more likely AI). Code: detector.py::model_signal.

**Why that might differ between human and AI writing:** Generated text is built from likely next words, so a model finds it easy to predict. Human writing has more surprises.

**What it can't see:** Plain, simple human writing is also very predictable, so it scores as AI-like. It reads word patterns, not meaning, and doesn't know who wrote the text.

### Signal two: the style signal

**What it measures:** Three measures of the text as text, flipped so higher = more likely AI: sentence-length spread (stdev / mean, weight 0.45), vocabulary variety (unique words over the first 100 words, weight 0.30), and punctuation other than commas and full stops, per word (weight 0.25). Code: stylometry.py::style_signal. Texts with fewer than 3 sentences or 30 words return 0.5 ("no opinion").

**Why that might differ between human and AI writing:** AI prose tends toward even, mid-length sentences and a narrower vocabulary. Human writing is lumpier, with more varied punctuation.

**What it can't see:** It can't read. Short, even human sentences look AI-like, and anything that reshapes text without changing its meaning (typos, chopped sentences, pasted quotes) moves the score.

### The combining rule

**The rule:** A weighted average of the two signals, except that when they disagree by 0.45 or more, the result is pulled toward 0.5 by keeping only 40% of its distance from the middle, because two methods disagreeing is uncertainty. The AI threshold (0.69) sits further from the middle than the human threshold (0.35), so a wrong accusation needs more evidence than a "human" call. Texts under 40 words cannot get the high-confidence AI label, because there is too little evidence and a false accusation is the expensive mistake.

**The numbers:** model weight 0.5, style weight 0.5, disagreement gap 0.45, shrink factor 0.4, human threshold 0.35, AI threshold 0.69, minimum words for AI 40. All in config.py.

**Where it lives:** `scoring.py::combine_signals` (the short-text cap is in app.py::submit)

**A case where my two signals split, and what my rule does with it:** On my first test the human text "Honestly? I almost quit..." scored model 0.458 and style 0.101, a gap of 0.357. My original gap setting of 0.35 treated that as disagreement and pulled the score from 0.28 up to 0.41, which hid a correct "human" call as "unsure". I raised the gap to 0.45, and the text now scores 0.28 and is labeled human. A second finding: a plain human text ("I went to the store after work...") scored 0.724 and was labeled AI, a false positive. Both signals misread it (model 0.806, style 0.642). I added the 40-word cap, which brought it to 0.68 (unsure). The 40-word cutoff was chosen after seeing that one example, so it is tuned to it and is not a general fix.

---

## Label Variants

| Label | Score range | The exact text a reader sees |
| --- | --- | --- |
| high-confidence human | 0.00 - 0.35 | We think this was probably written by a person. |
| unsure | 0.35 - 0.69 | We can't tell for sure whether this was written by a person or by AI. That isn't a finding that anything is wrong. If you wrote it yourself, you don't need to do anything, and you can ask for a review at any time. |
| high-confidence AI | 0.69 - 1.00 | Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look. |

**Why I worded the "unsure" one this way:** Someone reading it may have written every word themselves, so it says plainly that it is not an accusation, and it tells them they don't have to do anything.

---

## Sample Run

**A submission** (run before the threshold tuning described above, so the final settings would label this text "human")

~~~
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Honestly? I almost quit. The bus was late, my phone died, and I stood in the rain for forty minutes. Then, out of nowhere, a stranger shared her umbrella. We talked about nothing—dogs, mostly. I got home soaked and weirdly happy.", "creator_id": "me"}'
~~~

~~~
{
  "combined_score": 0.4119,
  "confidence": 0.4119,
  "content_id": "68a1bee3c18b",
  "guess": "unsure",
  "label": "We can't tell for sure whether this was written by a person or by AI. That isn't a finding that anything is wrong. If you wrote it yourself, you don't need to do anything, and you can ask for a review at any time.",
  "model_score": 0.4583,
  "style_score": 0.1012
}
~~~

**An appeal**

~~~
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "68a1bee3c18b", "reasoning": "I wrote this myself about a real afternoon."}'
~~~

~~~
{
  "content_id": "68a1bee3c18b",
  "message": "Thank you. Your appeal has been recorded and a person will review it.",
  "status": "under_review"
}
~~~

**What the log shows afterwards** (the decision entry and the appeal entry for that content_id, from `curl "http://127.0.0.1:5000/log?limit=6"`)

~~~
{
  "combined_score": 0.4119,
  "content_id": "68a1bee3c18b",
  "creator_id": "me",
  "duration_ms": 4242,
  "guess": "unsure",
  "model_score": 0.4583,
  "status": "decided",
  "style_score": 0.1012,
  "text_length": 229,
  "timestamp": "2026-11-15T22:57:46+00:00"
}
{
  "content_id": "68a1bee3c18b",
  "creator_id": "me",
  "event": "appeal",
  "reasoning": "I wrote this myself about a real afternoon.",
  "status": "under_review",
  "timestamp": "2026-11-15T22:59:01+00:00"
}
~~~

The same log also holds a rejected entry for the empty-text request: `"event": "rejected", "reason": "missing_text"`.

**All four calibration inputs, after tuning** (`python check_inputs.py`)

~~~
input            model  style   comb  guess
clearly AI      0.8294 0.5693 0.6994  ai
clearly human   0.4583 0.1012 0.2797  human
plain human      0.806 0.6423   0.68  unsure
edited AI       0.6527 0.4399 0.5463  unsure
~~~

---

## How I Used AI

**Moment 1**

- *What I asked for:* I didn't know what numbers to pick for my acceptance criteria, so I asked for suggested targets and the reasoning behind each.
- *What came back:* Suggested targets of at most 1 false positive in 10, an average score gap of at least 0.3, a 5,000-character input limit and 100% for appeals, with a one-sentence reason for each.
- *What I changed:* I kept the numbers after checking each one was specific and testable, and had the criteria reworded to match my repo's template (including that targets must hold across all three trials). The numbers started as AI suggestions, so I'm noting that here.

**Moment 2**

- *What I asked for:* My Claude Code login was blocked by my organization, so I had the code for the whole service written in a chat instead. I pasted my starter files (app.py, scoring.py, stylometry.py, config.py, audit.py) and asked for the style signal, the combining rule, the three labels, /submit and /appeal.
- *What came back:* Complete replacement code for those files, in blocks I ran and committed one at a time. My first test showed a problem: my human sample scored 0.28 on average, but my disagreement rule (gap 0.35) pulled it to 0.41, so a correct "human" call came out as "unsure". My four test inputs then showed a false positive: a plain, short human text scored 0.724 and was labeled AI.
- *What I changed:* I raised the disagreement gap to 0.45 and lowered the AI threshold from 0.70 to 0.69. For the false positive I added a rule that texts under 40 words can't get the AI label. The 40-word cutoff was chosen after seeing that one example, so it is tuned to it and is not a general fix.

---

## Rate Limiting

**My limits:** 10 per minute, 100 per day

**Why those numbers and not others:** A real writer submits a few pieces an hour, so 10 a minute is more than a person needs and never gets in their way. A script mapping my thresholds with hundreds of variations hits the minute cap within seconds, and the 100-a-day cap stops a slow, patient version of the same thing. I didn't go lower because a writer retrying after an error or submitting several drafts in a row shouldn't be locked out.

**What a caller counts as:** The creator_id in the request body if it is a non-empty string, otherwise the caller's IP address (app.py::rate_limit_key). The weakness is that a script can rotate through creator_ids to dodge the limit, and one IP with many writers behind it can't be told apart.

**The run of status codes when I pushed past it:**

~~~
$ python run_attacks.py --flood 15
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
5 of 15 were rate limited.
~~~

---

## Attack Run — Before

**How I marked them.** An attack **broke** the system if it got the outcome it was after: AI text that did not get the ai label (evasion), human text that got the ai label (false positive), text that got the human label (prompt injection), or a valid input that got a 5xx (malformed). Everything else is **held**. Evasion is strict: unsure counts as broke, because the attack's goal is to slip AI text past the label. PI02 got human; both its signals read the odd all-caps formatting as human, so I count it as broke but do not think the instruction itself was obeyed.

**Totals: 41 held, 15 broke of 56.** evasion 1 held / 9 broke; false_positive 4 held / 4 broke; prompt_injection 5 held / 1 broke; malformed 19 held / 1 broke; flood_same_creator 12 held / 0 broke.

| id | family | what it went for | HTTP | guess | model | style | combined | mark |
|---|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | unsure | 0.1635 | 0.5599 | 0.3617 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.5943 | 0.1348 | 0.4458 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.6662 | 0.2676 | 0.4669 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | unsure | 0.6114 | 0.5154 | 0.5634 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.3212 | 0.2216 | 0.2714 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.5727 | 0.3357 | 0.4542 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.5862 | 0.5 | 0.5431 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | unsure | 0.2452 | 0.5 | 0.3726 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.7042 | 0.3713 | 0.5378 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | ai | 0.9792 | 0.7468 | 0.863 | held |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.6175 | 0.5345 | 0.576 | held |
| FP02 | false_positive | human writing in a formal register | 200 | ai | 0.7387 | 0.665 | 0.7019 | BROKE |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | ai | 0.8051 | 0.598 | 0.7016 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | unsure | 0.8329 | 0.4996 | 0.6663 | held |
| FP05 | false_positive | technical documentation written by a person | 200 | ai | 0.8005 | 0.7485 | 0.7745 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.8814 | 0.4654 | 0.6734 | held |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | ai | 0.8816 | 0.55 | 0.7158 | BROKE |
| FP08 | false_positive | very short genuine human submission | 200 | unsure | 0.3223 | 0.5 | 0.4112 | held |
| PI01 | prompt_injection | instruction to ignore the check | 200 | unsure | 0.4625 | 0.274 | 0.3683 | held |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.2044 | 0.2115 | 0.2079 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.5943 | 0.309 | 0.4516 | held |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | unsure | 0.4998 | 0.3224 | 0.4111 | held |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.6401 | 0.5 | 0.57 | held |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.5583 | 0.5165 | 0.5374 | held |
| MF01 | malformed | text is only whitespace | 400 | - | - | - | - | held |
| MF02 | malformed | text is a single character | 503 | - | - | - | - | BROKE |
| MF03 | malformed | text is control characters | 200 | unsure | 0.0 | 0.5 | 0.4 | held |
| MF04 | malformed | text is only punctuation | 200 | unsure | 0.0112 | 0.5 | 0.4022 | held |
| MF05 | malformed | text is a very long single word | 200 | unsure | 0.9976 | 0.5 | 0.5995 | held |
| MF06 | malformed | text is emoji only | 200 | unsure | 0.9969 | 0.5 | 0.5994 | held |
| MF07 | malformed | text is right-to-left script | 200 | unsure | 0.9064 | 0.5 | 0.68 | held |
| MF08 | malformed | text is 60,000 characters | 400 | - | - | - | - | held |
| RQ01 | malformed | no text field at all | 400 | - | - | - | - | held |
| RQ02 | malformed | no creator_id | 400 | - | - | - | - | held |
| RQ03 | malformed | text is a number | 400 | - | - | - | - | held |
| RQ04 | malformed | text is a list | 400 | - | - | - | - | held |
| RQ05 | malformed | text is null | 400 | - | - | - | - | held |
| RQ06 | malformed | creator_id is an object | 400 | - | - | - | - | held |
| RQ07 | malformed | body is a JSON array, not an object | 400 | - | - | - | - | held |
| RQ08 | malformed | body is unparseable JSON | 400 | - | - | - | - | held |
| RQ09 | malformed | body is empty | 400 | - | - | - | - | held |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | - | - | - | - | held |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | - | - | - | - | held |
| RQ12 | malformed | deeply nested JSON | 400 | - | - | - | - | held |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | - | - | - | held |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | - | - | - | - | held |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | - | - | - | - | held |

**Ten audit log entries from the run** (decisions and rejections, taken from logs/audit.jsonl)

~~~
{
  "timestamp": "2026-11-17T02:22:50+00:00",
  "content_id": "204da7799766",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "model_score": 0.8051,
  "style_score": 0.598,
  "combined_score": 0.7016,
  "label": "Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look.",
  "status": "decided",
  "text_length": 418,
  "duration_ms": 84
}
{
  "timestamp": "2026-11-17T02:22:50+00:00",
  "content_id": "d7d0eed69187",
  "creator_id": "attacker_FP05",
  "guess": "ai",
  "model_score": 0.8005,
  "style_score": 0.7485,
  "combined_score": 0.7745,
  "label": "Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look.",
  "status": "decided",
  "text_length": 393,
  "duration_ms": 75
}
{
  "timestamp": "2026-11-17T02:22:51+00:00",
  "content_id": "4a4f61026433",
  "creator_id": "attacker_FP07",
  "guess": "ai",
  "model_score": 0.8816,
  "style_score": 0.55,
  "combined_score": 0.7158,
  "label": "Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look.",
  "status": "decided",
  "text_length": 335,
  "duration_ms": 74
}
{
  "timestamp": "2026-11-17T02:22:50+00:00",
  "content_id": "96fb168e1e60",
  "creator_id": "attacker_FP02",
  "guess": "ai",
  "model_score": 0.7387,
  "style_score": 0.665,
  "combined_score": 0.7019,
  "label": "Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look.",
  "status": "decided",
  "text_length": 477,
  "duration_ms": 87
}
{
  "timestamp": "2026-11-17T02:22:49+00:00",
  "content_id": "7a28d7ded2b2",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "model_score": 0.1635,
  "style_score": 0.5599,
  "combined_score": 0.3617,
  "label": "We can't tell for sure whether this was written by a person or by AI. That isn't a finding that anything is wrong. If you wrote it yourself, you don't need to do anything, and you can ask for a review at any time.",
  "status": "decided",
  "text_length": 657,
  "duration_ms": 178
}
{
  "timestamp": "2026-11-17T02:22:49+00:00",
  "content_id": "201196c20f70",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "model_score": 0.5943,
  "style_score": 0.1348,
  "combined_score": 0.4458,
  "label": "We can't tell for sure whether this was written by a person or by AI. That isn't a finding that anything is wrong. If you wrote it yourself, you don't need to do anything, and you can ask for a review at any time.",
  "status": "decided",
  "text_length": 708,
  "duration_ms": 90
}
{
  "timestamp": "2026-11-17T02:22:50+00:00",
  "content_id": "a303f8be051f",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "model_score": 0.3212,
  "style_score": 0.2216,
  "combined_score": 0.2714,
  "label": "We think this was probably written by a person.",
  "status": "decided",
  "text_length": 460,
  "duration_ms": 87
}
{
  "timestamp": "2026-11-17T02:22:51+00:00",
  "content_id": "2c3241631739",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "model_score": 0.2044,
  "style_score": 0.2115,
  "combined_score": 0.2079,
  "label": "We think this was probably written by a person.",
  "status": "decided",
  "text_length": 322,
  "duration_ms": 69
}
{
  "timestamp": "2026-11-17T02:22:52+00:00",
  "content_id": "ceb8f8502ddf",
  "creator_id": "attacker_MF07",
  "guess": "unsure",
  "model_score": 0.9064,
  "style_score": 0.5,
  "combined_score": 0.68,
  "label": "We can't tell for sure whether this was written by a person or by AI. That isn't a finding that anything is wrong. If you wrote it yourself, you don't need to do anything, and you can ask for a review at any time.",
  "status": "decided",
  "text_length": 105,
  "duration_ms": 95
}
{
  "timestamp": "2026-11-17T02:22:51+00:00",
  "creator_id": "attacker_MF02",
  "event": "rejected",
  "status": "rejected",
  "reason": "detector_failed"
}
{
  "timestamp": "2026-11-17T02:22:52+00:00",
  "creator_id": "attacker_flood",
  "event": "rejected",
  "status": "rejected",
  "reason": "rate_limited",
  "limit": "10 per 1 minute"
}
~~~

**The single worst outcome** (the one I'd least want to explain to a writer whose work got caught by it): **attacker_FP03**, a person writing carefully about their first month in a new country, which is exactly the writer a detector should give the benefit of the doubt. My system returned guess **ai** with combined score 0.7016 (model 0.8051, style 0.598) and showed them: "Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look." I would least want to explain this one because careful, plain sentences are what a language model finds most predictable, so the people who write most simply are the ones accused.

---

## Run Log and Verdicts

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Own writing flagged as AI (**stand-in texts, not my own writing**) | at most 1 of 10 | 4/10 | 4/10 | 4/10 | **MISSED** |
| 2. Score spread, clearly AI minus clearly human (average) | at least 0.3 | 0.42 | 0.42 | 0.42 | **MET** |
| 3. All three labels reachable | 3 of 3 | 3/3 | 3/3 | 3/3 | **MET** |
| 4. Appeal sets under_review and is logged; unknown id errors | 5 of 5 | 5/5 | 5/5 | 5/5 | **MET** |
| 5. Bad input returns 400 and is not logged as a decision | 5 of 5 | 5/5 | 5/5 | 5/5 | **MET** |

Criterion 1 was run on ten stand-in texts, not my own writing, so the MISSED verdict is about how the system treats plain human-style prose. It says nothing yet about my own pieces, which are still unmeasured. All three trials matched in every row, which is expected because neither signal is random.

**Real output from one trial**, pasted as text. Each entry was written by app.py::submit (or app.py::appeal) through audit.py::log_decision, log_rejection or log_appeal, during a run of run_eval.py (results/run_2026-11-16_2118_before.md) and check_appeals.py.

Criterion 1, one of the four stand-in texts labeled ai (eval_STAND-IN hum_2):

~~~
{
  "timestamp": "2026-11-17T02:18:47+00:00",
  "content_id": "613af628ee44",
  "creator_id": "eval_STAND-IN hum_2",
  "guess": "ai",
  "model_score": 0.8022,
  "style_score": 0.5825,
  "combined_score": 0.6924,
  "label": "Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look.",
  "status": "decided",
  "text_length": 242,
  "duration_ms": 69
}
~~~

Criterion 2, a clearly-AI text and a clearly-human text:

~~~
{
  "timestamp": "2026-11-17T02:18:49+00:00",
  "content_id": "cd1009028f08",
  "creator_id": "eval_clearly AI_1",
  "guess": "ai",
  "model_score": 0.9078,
  "style_score": 0.6022,
  "combined_score": 0.755,
  "label": "Our checks suggest this may have been written with the help of AI. These tools can be wrong, so if you wrote it yourself, please tell us and a person will take another look.",
  "status": "decided",
  "text_length": 384,
  "duration_ms": 75
}
{
  "timestamp": "2026-11-17T02:18:50+00:00",
  "content_id": "31a069b17e10",
  "creator_id": "eval_clearly huma_1",
  "guess": "human",
  "model_score": 0.4603,
  "style_score": 0.0731,
  "combined_score": 0.2667,
  "label": "We think this was probably written by a person.",
  "status": "decided",
  "text_length": 267,
  "duration_ms": 74
}
~~~

Criterion 4, a submission and its appeal (check_appeals.py):

~~~
{
  "timestamp": "2026-11-17T01:30:08+00:00",
  "content_id": "3c45b68fa626",
  "creator_id": "appeal_t1_0",
  "guess": "unsure",
  "model_score": 0.5849,
  "style_score": 0.5,
  "combined_score": 0.5424,
  "label": "We can't tell for sure whether this was written by a person or by AI. That isn't a finding that anything is wrong. If you wrote it yourself, you don't need to do anything, and you can ask for a review at any time.",
  "status": "decided",
  "text_length": 155,
  "duration_ms": 63
}
{
  "timestamp": "2026-11-17T01:30:08+00:00",
  "content_id": "3c45b68fa626",
  "creator_id": "appeal_t1_0",
  "event": "appeal",
  "status": "under_review",
  "reasoning": "I wrote this myself."
}
~~~

Criterion 5, a rejected empty-text request:

~~~
{
  "timestamp": "2026-11-17T02:18:52+00:00",
  "creator_id": "eval_bad_empty",
  "event": "rejected",
  "status": "rejected",
  "reason": "missing_text"
}
~~~

**Diagnoses**

**Criterion 1 (MISSED, 4/10 in every trial; stand-in texts 2, 4, 6 and 9 got ai).** The stage is signal one, with signal two agreeing on two of the four. Plain, predictable prose gets a high model score: across all ten stand-ins signal one averages 0.738, and for the four flagged texts it is 0.72 to 0.91. Signal two reads even sentence lengths and sparse punctuation as AI-like (0.58 to 0.75 on those four). The two-signal average then lands at 0.69 to 0.75, over the 0.69 AI threshold. My 40-word cap did not help because these texts are longer than 40 words. The mechanism is that a language model finds simple human writing as easy to predict as AI writing, and my second signal cannot tell them apart either: signal two averages 0.594 on the stand-ins and 0.589 on clearly-AI text, so it only separates lively human writing (0.221). The same stage and mechanism produced 4 of the 8 attack-set false positives (FP02, FP03, FP05, FP07, with model scores 0.74 to 0.88). This is one problem with many symptoms.

**Attack set, evasion (9 of 10 broke).** The pattern is that AI text lands only just above the AI threshold, so any small change to either signal pushes it into unsure. My clearly-AI texts combined to 0.66 to 0.76 against a 0.69 threshold. Four different mechanisms moved the score: typos made signal one drop (EV01 model 0.1635, because typos raise perplexity, which is signal one and not signal two as the attack set predicted); unusual words did the same (EV04 model 0.6114); breaking up sentences, a pasted quotation, very uneven sentence lengths and a human opening paragraph pulled signal two down (EV02, EV03, EV06, EV09 style 0.13 to 0.37); and padding with semicolons made the text one sentence long, so signal two returned its no-opinion value of 0.5 (EV07 has 97 words but one sentence by my splitter). EV05, heavily edited, came out human with both signals low.

**Attack set, other breaks.** MF02, the single character a, returned 503: detector.py raises ValueError for text that is too short to score, and app.py::submit catches every exception and reports it as detector_failed (503), when the right answer to a too-short submission is a 400. The stage is the route's error handling. PI02 got human because both signals read the odd all-caps instruction text as human (0.2044 and 0.2115), not because an instruction was obeyed: PI01 and PI03 carry similar instructions and landed in unsure.

**Criteria 2 to 5 were met, so I looked at whether the targets were easy.** Criterion 3 is fragile: the only scenario text that reaches the ai label combined to 0.6994, 0.0094 above the threshold, and I set the threshold to 0.69 after seeing that text. Criteria 4 and 5 were easy to meet, and the 0.3 gap in criterion 2 was low against the 0.42 I measured. If I tightened one, it would be criterion 3: require that three different AI texts, not one, produce the ai label.


---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
