#!/usr/bin/env python3
"""
Provenance Guard — the web service.

    python app.py

Then, in another terminal:

    curl -X POST http://127.0.0.1:5000/ping \
      -H "Content-Type: application/json" \
      -d '{"message": "hello"}'

That's the example route. It works right now, before you've written anything.
**Leave it alone** — it's your control. When something breaks later, check that
`/ping` still answers: if it does, the problem is in your handler; if it
doesn't, it's the service itself.

Routes:

    POST /ping        the worked example. Already works. Don't edit it
    POST /submit      ← YOU BUILD THIS (Milestone 3, 4, 5)
    POST /appeal      ← YOU BUILD THIS (Milestone 5)
    GET  /log         the audit log. Already works
    GET  /health      is the service up, and is the model loaded
"""

import hashlib
import time
import uuid

from flask import Flask, jsonify, request

import audit
import config

app = Flask(__name__)


# ── Rate limiting — UNIT 8 ────────────────────────────────────────────────────
# Off until you turn it on. In unit 8, Milestone 1:
#
#   1. Set RATE_LIMITING_ENABLED = True in config.py (or AI201_RATE_LIMITS=1)
#   2. Choose your numbers there
#   3. Uncomment the @limiter.limit(...) line on /submit below
#
# The order doesn't matter. While limiting is off, that decorator is a no-op
# that quietly does nothing, so uncommenting it early costs you nothing — but
# it also means no 429 until you've done step 1.
#
# The storage backend is preconfigured, which stops Flask-Limiter printing a
# warning on every start. In-memory is right for one laptop and wrong for
# anything real — a restart forgets every count.

class _LimiterOff:
    """
    Stands in for the real limiter while rate limiting is off.

    It makes @limiter.limit(...) a decorator that returns the route
    untouched, so uncommenting the line before you flip the setting is
    harmless instead of a crash on startup.
    """

    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()
if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        """
        Who a request counts against.

        Falling back to the caller's address is the easy version. Unit 8's
        stretch asks about per-creator limits instead — and the difference
        matters: one script can look like a thousand callers, and one household
        can look like one.
        """
        payload = request.get_json(silent=True)
        # A body that parses as JSON but isn't an object — a bare list or
        # string — has no .get. Without this guard the key function raises
        # BEFORE the route runs, and a malformed request becomes a 500 that
        # looks like your handler crashed when your handler never ran.
        if not isinstance(payload, dict):
            return get_remote_address()
        creator = payload.get("creator_id")
        return creator if isinstance(creator, str) and creator.strip() else get_remote_address()

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )

    @app.errorhandler(429)
    def rate_limited(exc):
        """
        A rejected request still leaves a trace.

        ⚠️ An attack that shows up only as an absence is one you'll never find.
        """
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {}
        audit.log_rejection(
            creator_id=payload.get("creator_id", "unknown"),
            reason="rate_limited",
            limit=str(exc.description),
        )
        return jsonify({
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }), 429


# ── The worked example. Already works. Don't edit. ────────────────────────────

@app.post("/ping")
def ping():
    """
    Everything a route needs, in six lines.

    JSON arrives as a dict. You pull things out of it. You return a dict and
    the framework turns it into a response. That's the whole idea.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "ok": True,
        "you_sent": payload.get("message"),
        "service": "provenance-guard",
    })


@app.get("/health")
def health():
    """Is the service up, and has the model been downloaded yet?"""
    import detector

    loaded = detector._model is not None
    return jsonify({
        "ok": True,
        "detector_model": config.DETECTOR_MODEL,
        "detector_loaded": loaded,
        "rate_limiting": config.RATE_LIMITING_ENABLED,
        "log_entries": len(audit.read_entries()),
    })


# ── YOU BUILD THIS ────────────────────────────────────────────────────────────

@app.post("/submit")
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute;{config.RATE_LIMIT_PER_DAY}/day")
def submit():
    """Take text, score it with two signals, log the decision, answer."""
    started = time.perf_counter()
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    text = payload.get("text")
    creator_id = payload.get("creator_id")

    def reject(reason, message, status=400):
        who = creator_id if isinstance(creator_id, str) and creator_id.strip() else "unknown"
        audit.log_rejection(
            creator_id=who,
            reason=reason,
            http_status=status,
            duration_ms=round((time.perf_counter() - started) * 1000),
            text_length=len(text) if isinstance(text, str) else None,
        )
        return jsonify({"error": reason, "message": message}), status

    if not isinstance(text, str) or not text.strip():
        return reject("missing_text", "Please send some text to check.")
    if len(text) > config.MAX_TEXT_CHARS:
        return reject(
            "text_too_long",
            f"Text is over the {config.MAX_TEXT_CHARS}-character limit.",
        )
    if not isinstance(creator_id, str) or not creator_id.strip():
        return reject("missing_creator_id", "Please send a creator_id.")

    import detector
    import scoring
    import stylometry

    try:
        model_score = detector.model_signal(text)
    except ValueError:
        return reject(
            "text_too_short",
            "That is too short to check. Please send a few sentences.",
        )
    except Exception:
        return reject(
            "detector_failed",
            "We couldn't check this right now. Please try again.",
            503,
        )
    style_score = stylometry.style_signal(text)
    combined = scoring.combine_signals(model_score, style_score)
    if len(text.split()) < config.MIN_WORDS_FOR_AI and combined >= config.AI_THRESHOLD:
        combined = round(config.AI_THRESHOLD - 0.01, 4)
    guess, label = scoring.score_to_label(combined)

    content_id = uuid.uuid4().hex[:12]
    duration_ms = round((time.perf_counter() - started) * 1000)

    audit.log_decision(
        content_id=content_id,
        creator_id=creator_id,
        guess=guess,
        model_score=round(model_score, 4),
        style_score=round(style_score, 4),
        combined_score=combined,
        label=label,
        status="decided",
        text_length=len(text),
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
        duration_ms=duration_ms,
    )

    return jsonify({
        "content_id": content_id,
        "guess": guess,
        "confidence": combined,
        "label": label,
        "model_score": round(model_score, 4),
        "style_score": round(style_score, 4),
        "combined_score": combined,
    })


@app.post("/appeal")
def appeal():
    """A writer says we got it wrong. Record it and move the item to review."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    content_id = payload.get("content_id")
    reasoning = payload.get("reasoning")

    if not isinstance(content_id, str) or not content_id.strip():
        return jsonify({"error": "missing_content_id",
                        "message": "Please send the content_id you are appealing."}), 400
    if not isinstance(reasoning, str) or not reasoning.strip():
        return jsonify({"error": "missing_reasoning",
                        "message": "Please tell us why you think this is wrong."}), 400

    history = audit.entries_for(content_id.strip())
    if not history:
        return jsonify({"error": "unknown_content_id",
                        "message": "We couldn't find that submission."}), 404

    audit.log_appeal(
        content_id=content_id.strip(),
        creator_id=history[0].get("creator_id", "unknown"),
        reasoning=reasoning.strip(),
    )
    return jsonify({
        "content_id": content_id.strip(),
        "status": "under_review",
        "message": "Thank you. Your appeal has been recorded and a person will review it.",
    })


# ── Already works ─────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    """
    The audit log, most recent last.

        curl "http://127.0.0.1:5000/log?limit=10"

    You need this in unit 8 to paste entries into your README, and you need it
    now to see whether your logging is actually working.
    """
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)
    return jsonify({"count": len(entries), "entries": entries})


@app.before_request
def _start_timer():
    from flask import g
    g.started = time.perf_counter()


def _elapsed_ms():
    from flask import g
    started = getattr(g, "started", None)
    return None if started is None else round((time.perf_counter() - started) * 1000)


# ── One answer shape for every failure ───────────────────────────────────────

@app.errorhandler(Exception)
def unexpected_error(exc):
    """
    Anything nobody planned for still answers in JSON and leaves a log record.

    Without this, an unplanned crash returns an HTML error page and, on
    /submit or /appeal, leaves no trace in the audit log.
    """
    from werkzeug.exceptions import HTTPException

    if isinstance(exc, HTTPException):
        status = exc.code or 500
        reason = exc.name.lower().replace(" ", "_")
        message = exc.description
    else:
        status, reason = 500, "internal_error"
        message = "Something went wrong on our side. Please try again."
    if request.path in ("/submit", "/appeal"):
        audit.log_rejection(
            creator_id="unknown",
            reason=reason,
            http_status=status,
            path=request.path,
            error_type=type(exc).__name__,
            duration_ms=_elapsed_ms(),
        )
    return jsonify({"error": reason, "message": message}), status


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"  detector model:  {config.DETECTOR_MODEL}")
    print(f"  rate limiting:   {'ON' if config.RATE_LIMITING_ENABLED else 'off (unit 8)'}")
    print(f"  audit log:       {config.AUDIT_LOG}")
    print()
    print("Check it's alive:")
    print(f'  curl -X POST http://{config.HOST}:{config.PORT}/ping \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"message\": \"hello\"}'")
    print()
    # debug=True hands out an interactive debugger, so it's local-only — see config.py
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == "__main__":
    main()
