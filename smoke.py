#!/usr/bin/env python3
"""Exercise the observed anonymous REST flow with a handful of safe requests."""

import argparse
import json

from trafiku import TrafikuClient, TrafikuError


def _require(envelope, label, data_type=None):
    if not isinstance(envelope, dict) or envelope.get("success") is not True:
        raise TrafikuError(f"{label} failed: {envelope!r}")
    data = envelope.get("data")
    if data_type is not None and not isinstance(data, data_type):
        raise TrafikuError(f"{label} returned unexpected data")
    return data


def _nearest(stations, longitude, latitude):
    candidates = []
    for station in stations:
        coordinates = station.get("geometry", {}).get("coordinates", [])
        if len(coordinates) == 2:
            distance = (coordinates[0] - longitude) ** 2 + (coordinates[1] - latitude) ** 2
            candidates.append((distance, station))
    if not candidates:
        raise TrafikuError("stations response contained no usable coordinates")
    return min(candidates, key=lambda item: item[0])[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--longitude", type=float, default=21.1655)
    parser.add_argument("--latitude", type=float, default=42.6629)
    parser.add_argument("--base-url")
    args = parser.parse_args()
    client = TrafikuClient(args.base_url) if args.base_url else TrafikuClient()

    stations = _require(client.stations(), "stations", list)
    station = _nearest(stations, args.longitude, args.latitude)
    station_id = station["_id"]
    _require(client.station(station_id), "station", dict)
    incoming = _require(
        client.incoming_buses(station_id, args.longitude, args.latitude), "incoming", dict
    )
    news = _require(client.news(), "news", dict)

    schedule_line = None
    lines = incoming.get("passing_lines", [])
    for line in lines:
        if client.schedule(line["_id"], station_id).get("success") is True:
            schedule_line = line["_id"]
            break

    upcoming = None
    buses = incoming.get("incoming_buses", [])
    if buses:
        upcoming = client.upcoming_stations(
            buses[0]["_id"], args.longitude, args.latitude
        ).get("success")

    print(json.dumps({
        "stations": len(stations),
        "nearest_station": {"_id": station_id, "name": station.get("name")},
        "passing_lines": len(lines),
        "incoming_buses": len(buses),
        "news_items": len(news.get("docs", [])),
        "schedule_line": schedule_line,
        "upcoming_request_succeeded": upcoming,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (TrafikuError, ValueError) as error:
        raise SystemExit(f"smoke test failed: {error}")
