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

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



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
