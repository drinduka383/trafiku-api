#!/usr/bin/env python3
"""Dependency-free client for the observed Trafiku Urban public HTTP API."""

import argparse
import json
import math
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


DEFAULT_API_URL = "https://tu.appbites.dev/api/public"


class TrafikuError(RuntimeError):
    """A request or client-validation failure."""


def _identifier(value):
    value = str(value).strip()
    if not value:
        raise ValueError("identifier cannot be empty")
    return quote(value, safe="")


def _positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _user_context(longitude, latitude, user_id="unknown"):
    if isinstance(longitude, bool) or isinstance(latitude, bool):
        raise ValueError("coordinates must be numbers")
    longitude, latitude = float(longitude), float(latitude)
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    return {"location": [longitude, latitude], "userId": str(user_id or "unknown")}


class TrafikuClient:
    def __init__(self, base_url=DEFAULT_API_URL, token=None, timeout=15):
        base_url = base_url.rstrip("/")
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be an HTTP(S) URL")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = base_url
        self.token = token
        self.timeout = timeout

    def _request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Accept": "application/json", "User-Agent": "trafiku-api-research/0.1"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except HTTPError as error:
            detail = error.read(65536).decode("utf-8", "replace").strip()
            try:
                detail = json.loads(detail)
            except (json.JSONDecodeError, TypeError):
                pass
            raise TrafikuError(f"HTTP {error.code}: {detail or error.reason}") from None
        except (URLError, TimeoutError) as error:
            raise TrafikuError(f"request failed: {error}") from None
        except json.JSONDecodeError as error:
            raise TrafikuError(f"server returned invalid JSON: {error}") from None

    def stations(self):
        return self._request("GET", "/stations")

    def station(self, station_id):
        return self._request("GET", f"/stations/{_identifier(station_id)}")

    def incoming_buses(self, station_id, longitude, latitude, user_id="unknown"):
        path = f"/stations/{_identifier(station_id)}/incomingBuses"
        return self._request("POST", path, _user_context(longitude, latitude, user_id))

    def schedule(self, line_id, station_id):
        line_id, station_id = _identifier(line_id), _identifier(station_id)
        return self._request("GET", f"/schedules/{line_id}/{station_id}")

    def news(self, limit=10, page=1):
        limit, page = _positive_int(limit, "limit"), _positive_int(page, "page")
        return self._request("GET", f"/news/{limit}/{page}")

    def upcoming_stations(self, bus_id, longitude, latitude, user_id="unknown"):
        path = f"/buses/{_identifier(bus_id)}/upcomingStations"
        return self._request("POST", path, _user_context(longitude, latitude, user_id))


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("TRAFIKU_API_URL", DEFAULT_API_URL))
    parser.add_argument("--timeout", type=float, default=15)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stations")

    station = commands.add_parser("station")
    station.add_argument("station_id")

    incoming = commands.add_parser("incoming")
    incoming.add_argument("station_id")
    incoming.add_argument("longitude", type=float)
    incoming.add_argument("latitude", type=float)

    schedule = commands.add_parser("schedule")
    schedule.add_argument("line_id")
    schedule.add_argument("station_id")

    news = commands.add_parser("news")
    news.add_argument("--limit", type=int, default=10)
    news.add_argument("--page", type=int, default=1)

    upcoming = commands.add_parser("upcoming")
    upcoming.add_argument("bus_id")
    upcoming.add_argument("longitude", type=float)
    upcoming.add_argument("latitude", type=float)
    return parser


def main():
    args = _parser().parse_args()
    client = TrafikuClient(args.base_url, os.getenv("TRAFIKU_TOKEN"), args.timeout)
    try:
        if args.command == "stations":
            result = client.stations()
        elif args.command == "station":
            result = client.station(args.station_id)
        elif args.command == "incoming":
            result = client.incoming_buses(args.station_id, args.longitude, args.latitude)
        elif args.command == "schedule":
            result = client.schedule(args.line_id, args.station_id)
        elif args.command == "news":
            result = client.news(args.limit, args.page)
        else:
            result = client.upcoming_stations(args.bus_id, args.longitude, args.latitude)
    except (TrafikuError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
