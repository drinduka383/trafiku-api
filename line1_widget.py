#!/usr/bin/env python3
"""Compact two-way Line 1 arrival widget for Lakrishte and Fakulteti Teknik."""

import os
import re
import sys
import unicodedata

from trafiku import DEFAULT_API_URL, TrafikuClient, TrafikuError


# title, source station, line direction, longitude, latitude
DIRECTIONS = (
    (
        "lakrishte -> fakulteti teknik",
        "5d556ddb8daa9a087b28cc6c",
        "5d552616ee0dd803fc6a55b4",
        21.1504,
        42.6535,
    ),
    (
        "fakulteti teknik -> lakrishte",
        "5d5565af8daa9a087b2847da",
        "5d5525d1ee0dd803fc6a51b9",
        21.166042,
        42.649604,
    ),
)


def _ascii(value, limit=44):
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _eta_key(bus):
    match = re.search(r"\d+(?:\.\d+)?", str(bus.get("distance_from_station_min", "")))
    return float(match.group()) if match else float("inf")


def _bus_row(bus):
    eta = _ascii(bus.get("distance_from_station_min", "--"), 8)
    location = _ascii(bus.get("address") or bus.get("street") or "location unavailable")
    return f"- {eta} min, currently @ {location}"


def render(client):
    sections = []
    for title, station_id, line_id, longitude, latitude in DIRECTIONS:
        envelope = client.incoming_buses(station_id, longitude, latitude)
        if not isinstance(envelope, dict) or envelope.get("success") is not True:
            raise TrafikuError(f"arrival lookup failed for {title}")
        data = envelope.get("data")
        if not isinstance(data, dict):
            raise TrafikuError(f"unexpected arrival data for {title}")
        buses = sorted(
            (bus for bus in data.get("incoming_buses", []) if bus.get("line_id") == line_id),
            key=_eta_key,
        )[:2]
        rows = [_bus_row(bus) for bus in buses]
        rows.extend("- -- min, no live bus reported" for _ in range(2 - len(rows)))
        sections.append(f"{title}:\n" + "\n".join(rows))
    return "\n\n".join(sections)


def main():
    client = TrafikuClient(os.getenv("TRAFIKU_API_URL", DEFAULT_API_URL))
    try:
        print(render(client))
    except (TrafikuError, ValueError) as error:
        print(f"line 1 widget unavailable: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
