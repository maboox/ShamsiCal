"""Manual opt-in provider smoke check; never used during ordinary test runs."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shamsical import network
from shamsical.calendar import today

results = {}
for name, function in (
    ("events", lambda: network.read_events(today())),
    ("rss", lambda: network.read_feed("https://www.nasa.gov/feeds/iotd-feed/")),
):
    try:
        value = function()
        results[name] = {"ok": True, "count": len(value)}
    except Exception as error:
        results[name] = {"ok": False, "error": str(error)}
print(json.dumps(results, indent=2))
