# Trafiku Urban API research

Internal, unofficial documentation and portable test tools for the HTTP and
Socket.IO interfaces used by the public Trafiku Urban Android app
(`es.appbit.prishtinabuses`). This repository is a company-review draft, not a
promise of API stability or permission for public redistribution.

No Android device or emulator is required. The REST API is ordinary JSON over
HTTPS, and its observed CORS policy allows browser origins (`*`).

## Quick start

Requirements: Python 3.9+ for REST; Node.js 22+ for the dependency-free
WebSocket smoke test.

```sh
python3 -m unittest -v
python3 smoke.py
node socket.mjs
```

The `lak-tek` branch also provides the commute-specific JSON query and its
portable ASCII consumer:

```sh
python3 lak_tek.py
python3 line1_widget.py
```

`lak_tek.arrivals(client, live_buses)` merges station predictions with an
optional `bus_update` payload. A live-only bus is returned only while the
exact boarding stop remains in `upcoming_stations`.

Query individual routes:

```sh
python3 trafiku.py stations
python3 trafiku.py station STATION_ID
python3 trafiku.py incoming STATION_ID 21.1655 42.6629
python3 trafiku.py schedule LINE_ID STATION_ID
python3 trafiku.py news --limit 10 --page 1
python3 trafiku.py upcoming BUS_ID 21.1655 42.6629
```

The client defaults to `https://tu.appbites.dev/api/public`. Override it with
`TRAFIKU_API_URL` or `--base-url`. Observed public routes work anonymously. If
company testing later requires an authenticated request, provide a short-lived
token through `TRAFIKU_TOKEN`; never commit it or put it on the command line.

Any web runtime with `fetch` can call the same API:

```js
const response = await fetch("https://tu.appbites.dev/api/public/stations");
const { success, data: stations } = await response.json();
```

## Repository contents

- `openapi.json` — importable OpenAPI 3.1 contract for the six verified routes.
- `trafiku.py` — dependency-free Python library and CLI.
- `smoke.py` — safe live flow using a station nearest central Prishtina.
- `socket.mjs` — dependency-free Engine.IO/Socket.IO `bus_update` listener.
- `lak_tek.py` — JSON-ready, two-way catchable-arrival query for one commute (`lak-tek` only).
- `line1_widget.py` — compact ASCII consumer of that query (`lak-tek` only).
- `test_trafiku.py` — offline client-contract and catchability checks.
- `RESEARCH.md` — evidence, observed behavior, limits, and publication questions.
- `evidence/` — bounded runtime screenshot and dated public station snapshot.

## Publication gate

Before making this repository public, the API owner should confirm:

1. the endpoint and field names are intended as a supported public contract;
2. authentication, rate limits, caching, versioning, uptime, and deprecation policy;
3. licensing and privacy terms for station, schedule, vehicle, and location data;
4. whether the current host is permanent and suitable for third-party clients;
5. an explicit license for this repository.

APK files, extracted assets, decompiled source, tokens, keys, emulator state,
and raw logs are intentionally excluded. Their hashes and provenance are kept
in `RESEARCH.md` so the work remains reproducible without turning a future
public documentation repository into an application mirror.
