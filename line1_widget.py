#!/usr/bin/env python3
"""Compact ASCII consumer of the lak-tek arrivals API."""

import os
import sys
import unicodedata

from lak_tek import arrivals
from trafiku import DEFAULT_API_URL, TrafikuClient, TrafikuError


def _ascii(value, limit=44):
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def render(result):
    sections = []
    for direction in result["data"]["directions"]:
        rows = []
        for bus in direction["buses"][:2]:
            eta = _ascii(bus.get("eta_min", "--"), 8)
            location = _ascii(bus.get("location") or "location unavailable")
            rows.append(f"- {eta} min, currently @ {location}")
        rows.extend("- -- min, no additional approaching bus" for _ in range(2 - len(rows)))
        sections.append(f"{direction['from']} -> {direction['to']}:\n" + "\n".join(rows))
    return "\n\n".join(sections)


def main():
    try:
        result = arrivals(TrafikuClient(os.getenv("TRAFIKU_API_URL", DEFAULT_API_URL)))
    except (TrafikuError, ValueError) as error:
        print(f"line 1 widget unavailable: {error}", file=sys.stderr)
        return 1
    print(render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
