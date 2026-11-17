# Running Provenance Guard

Local only (Path B). The detector model is GPT-2, about 550 MB, so I did not host it.

**You need:** Python 3.13 (what I ran it with), about 2 GB free disk, and internet on the first run only, to download the model.

1. Clone and enter the repo:

        git clone https://github.com/AishNiroula/ai201-project4-provenance-guard-starter-v2026.git
        cd ai201-project4-provenance-guard-starter-v2026

2. Create the environment and install the pinned dependencies:

        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt

3. Start the service (one command):

        python app.py

   The first request is slow (the model loads); after that each request takes a fraction of a second.

4. Check it is alive, in a second terminal:

        curl -X POST http://127.0.0.1:5000/ping -H "Content-Type: application/json" -d '{"message": "hello"}'

**If port 5000 is busy:** on macOS, AirPlay Receiver can hold it (System Settings, turn off AirPlay Receiver), or an old copy of this server is still running (`pkill -f "python app.py"`).

**Tests:** `python cap_check.py mytrial --no-appeals` runs the capstone criteria without a server. Drop `--no-appeals` while the server is running to include the appeals check.

**Record of a run from a fresh clone:** results/clean_checkout_run.txt.
