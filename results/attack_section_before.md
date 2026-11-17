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
