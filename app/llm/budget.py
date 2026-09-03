"""Spend guard for the hosted AI provider.

Three independent caps, all env-configurable, all deterministic:

  * a lifetime budget in USD (`AI_BUDGET_USD`, default 4.00) estimated from the
    token usage the API reports, persisted as JSON next to the assessments;
  * a daily call cap (`AI_DAILY_CALLS`, default 25) so a restart that wipes the
    spend file can never turn into an expensive day;
  * a per-client daily cap (`AI_CALLS_PER_IP_DAY`, default 8) and a per-client
    cooldown (`AI_COOLDOWN_SECONDS`, default 20), in memory.

When any cap is hit the service degrades to the *replay* provider (pre-recorded
drafts) and says so in the status — the demo keeps working, it just stops
costing money. The persisted counter is best-effort: on an ephemeral container
it resets with the container, which is why the hard guarantee should also be
set as a spend limit on the API key in the Anthropic Console.

Prices below are the public Claude API rates (USD per million tokens) for the
model the provider uses; cache reads are 0.1x, cache writes 1.25x input.
"""

import json
import os
import threading
import time
from datetime import date
from pathlib import Path

# (input, output, cache_read, cache_write) USD per million tokens
PRICES = {
    "claude-sonnet-5": (2.00, 10.00, 0.20, 2.50),
    "claude-haiku-4-5": (1.00, 5.00, 0.10, 1.25),
    "claude-opus-5": (5.00, 25.00, 0.50, 6.25),
}
_DEFAULT_PRICE = PRICES["claude-sonnet-5"]

_LOCK = threading.Lock()
_IP_CALLS: dict[str, dict[str, int]] = {}   # day -> ip -> calls
_IP_LAST: dict[str, float] = {}               # ip -> monotonic time of last call


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return int(default)


def budget_usd():
    return _env_float("AI_BUDGET_USD", 4.0)


def daily_cap():
    return _env_int("AI_DAILY_CALLS", 25)


def per_ip_cap():
    return _env_int("AI_CALLS_PER_IP_DAY", 8)


def cooldown_seconds():
    return _env_float("AI_COOLDOWN_SECONDS", 20.0)


def _spend_path():
    base = os.environ.get("AIACT_DATA_DIR") or str(
        Path(__file__).resolve().parent.parent.parent / "data")
    return Path(base) / "ai_spend.json"


def _load():
    p = _spend_path()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d, dict):
            return d
    except (OSError, ValueError):
        pass
    return {"spent_usd": 0.0, "calls": 0, "days": {}}


def _save(d):
    p = _spend_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, p)


def estimate_cost(usage, model="claude-sonnet-5"):
    """USD for one response from its `usage` (dict or SDK object)."""
    price_in, price_out, price_read, price_write = PRICES.get(model, _DEFAULT_PRICE)

    def g(key):
        v = usage.get(key) if isinstance(usage, dict) else getattr(usage, key, None)
        return int(v or 0)

    return (g("input_tokens") * price_in + g("output_tokens") * price_out
            + g("cache_read_input_tokens") * price_read
            + g("cache_creation_input_tokens") * price_write) / 1_000_000


def record(usage, model="claude-sonnet-5"):
    """Add one call's cost to the persisted counter; returns the new state."""
    cost = estimate_cost(usage, model)
    today = date.today().isoformat()
    with _LOCK:
        d = _load()
        d["spent_usd"] = round(float(d.get("spent_usd", 0.0)) + cost, 6)
        d["calls"] = int(d.get("calls", 0)) + 1
        days = d.setdefault("days", {})
        days[today] = int(days.get(today, 0)) + 1
        # keep the day map small
        for k in sorted(days)[:-7]:
            days.pop(k, None)
        _save(d)
    return state()


def state():
    d = _load()
    today = date.today().isoformat()
    spent = float(d.get("spent_usd", 0.0))
    calls_today = int(d.get("days", {}).get(today, 0))
    return {
        "budget_usd": budget_usd(),
        "spent_usd": round(spent, 4),
        "remaining_usd": round(max(budget_usd() - spent, 0.0), 4),
        "calls_total": int(d.get("calls", 0)),
        "calls_today": calls_today,
        "daily_cap": daily_cap(),
        "per_ip_cap": per_ip_cap(),
        "cooldown_seconds": cooldown_seconds(),
        "exhausted": spent >= budget_usd() or calls_today >= daily_cap(),
    }


def allow(ip=None):
    """(ok, reason). Checks the lifetime budget, the daily cap and the per-IP cap
    without recording anything."""
    st = state()
    if st["spent_usd"] >= st["budget_usd"]:
        return False, "budget"
    if st["calls_today"] >= st["daily_cap"]:
        return False, "daily_cap"
    if ip:
        today = date.today().isoformat()
        with _LOCK:
            n = _IP_CALLS.get(today, {}).get(ip, 0)
        if n >= per_ip_cap():
            return False, "per_ip_cap"
        with _LOCK:
            last = _IP_LAST.get(ip)
        if last is not None and time.monotonic() - last < cooldown_seconds():
            return False, "cooldown"
    return True, ""


def note_ip(ip):
    if not ip:
        return
    today = date.today().isoformat()
    with _LOCK:
        for k in [k for k in _IP_CALLS if k != today]:
            _IP_CALLS.pop(k, None)
        day = _IP_CALLS.setdefault(today, {})
        day[ip] = day.get(ip, 0) + 1
        _IP_LAST[ip] = time.monotonic()
        if len(_IP_LAST) > 5000:          # bounded memory
            for k in list(_IP_LAST)[:1000]:
                _IP_LAST.pop(k, None)


def reset_for_tests():
    with _LOCK:
        _IP_CALLS.clear()
        _IP_LAST.clear()
    p = _spend_path()
    if p.exists():
        p.unlink()
