# Cost of one /submit

| Measure | Value |
|---|---|
| Average over 10 warm HTTP requests | 0.068 s |
| Fastest / slowest of the 10 | 0.064 s / 0.071 s |
| Cold start: import app | 0.1 s |
| Cold start: first request (loads the model) | 2.0 s |
| Peak memory of a process that loaded the model | 906 MB |
| GPT-2 weights on disk (Hugging Face cache) | 551 MB |
| Money per request | 0 (the model runs on this machine, no API) |
| 100 requests (the daily rate limit) | 6.8 s of compute |

Runs (seconds): 0.069, 0.071, 0.068, 0.071, 0.070, 0.070, 0.067, 0.064, 0.065, 0.065
