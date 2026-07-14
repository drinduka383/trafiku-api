#!/usr/bin/env python3
"""Structured catchable arrivals for Lakrishte and Fakulteti Teknik."""

import argparse
import json
import os
import re
import sys

from trafiku import DEFAULT_API_URL, TrafikuClient, TrafikuError


DIRECTIONS = (
    {
        "id": "lakrishte-teknik",
        "from": "lakrishte",
        "to": "fakulteti teknik",
        "station_id": "5d556ddb8daa9a087b28cc6c",
        "line_id": "5d552616ee0dd803fc6a55b4",
        "location": (21.1504, 42.6535),
    },
    {
        "id": "teknik-lakrishte",
        "from": "fakulteti teknik",
        "to": "lakrishte",
        "station_id": "5d5565af8daa9a087b2847da",
        "line_id": "5d5525d1ee0dd803fc6a51b9",
        "location": (21.166042, 42.649604),
    },
)


def _eta(value):
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else float("inf")


def _line_id(bus):
    line = bus.get("line")
    return bus.get("line_id") or (line.get("_id") if isinstance(line, dict) else None)


def _row(bus, eta, location, source):
    return {"id": bus["_id"], "eta_min": eta, "location": location, "source": source}


def _incoming(client, direction):
    response = client.incoming_buses(direction["station_id"], *direction["location"])
    data = response.get("data") if isinstance(response, dict) and response.get("success") is True else None
    if not isinstance(data, dict) or not isinstance(data.get("incoming_buses"), list):
        raise TrafikuError(f"arrival lookup failed for {direction['id']}")
    return data["incoming_buses"]


def _live_row(client, direction, bus):
    try:
        response = client.upcoming_stations(bus["_id"], *direction["location"])
    except (KeyError, TrafikuError, ValueError):
        return None
    data = response.get("data") if isinstance(response, dict) and response.get("success") is True else None
    upcoming = data.get("upcoming_stations") if isinstance(data, dict) else None
    if not isinstance(upcoming, list):
        return None
    boarding = next((
        stop for stop in upcoming
        if isinstance(stop, dict) and stop.get("_id") == direction["station_id"]
    ), None)
    if not boarding:
        return None
    next_stop = upcoming[0].get("name") if upcoming and isinstance(upcoming[0], dict) else None
    return _row(bus, boarding.get("distance_to_station_min"), next_stop, "route_progress")


def arrivals(client, live_buses=(), limit=2):
    """Return predictions plus still-catchable buses from a bus_update payload."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    directions = []
    for direction in DIRECTIONS:
        rows = []
        seen = set()
        for bus in _incoming(client, direction):
            if not isinstance(bus, dict) or _line_id(bus) != direction["line_id"] or not bus.get("_id"):
                continue
            seen.add(bus["_id"])
            rows.append(_row(
                bus,
                bus.get("distance_from_station_min"),
                bus.get("address") or bus.get("street"),
                "station_prediction",
            ))
        for bus in live_buses:
            if (
                not isinstance(bus, dict)
                or _line_id(bus) != direction["line_id"]
                or bus.get("is_visible") is False
                or not bus.get("_id")
                or bus["_id"] in seen
            ):
                continue
            row = _live_row(client, direction, bus)
            if row:
                seen.add(bus["_id"])
                rows.append(row)
        rows.sort(key=lambda row: _eta(row["eta_min"]))
        directions.append({
            "id": direction["id"],
            "from": direction["from"],
            "to": direction["to"],
            "boarding_station_id": direction["station_id"],
            "line_id": direction["line_id"],
            "buses": rows[:limit],
        })
    return {"success": True, "data": {"route": "lak-tek", "directions": directions}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--base-url", default=os.getenv("TRAFIKU_API_URL", DEFAULT_API_URL))
    args = parser.parse_args()
    try:
        result = arrivals(TrafikuClient(args.base_url), limit=args.limit)
    except (TrafikuError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
