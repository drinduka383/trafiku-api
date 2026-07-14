# Verified findings

Status date: 2026-07-14. All network checks were low-volume requests matching
normal public-app behavior. No account, token, bypass, or privileged endpoint
was used.

## App and runtime evidence

- Package: `es.appbit.prishtinabuses`
- Current analyzed release: Android `3.1.8` (`versionCode 36`, minSdk 24, targetSdk 36)
- REST base recovered from its Hermes bundle: `https://tu.appbites.dev/api/public`
- Socket base: `wss://tu.appbites.dev`
- Socket path: `/ws/socket.io`
- Socket.IO event: `bus_update`
- Android `3.1.8` XAPK hash: `af919a4cfb7a3301ac04924296c2ce414657a339076bc9357e036b0557e02d05`
- Universal Android `3.0.5` APK hash: `b6e524ed53eab69ce8f7dbe8f61e525be23de5063419101f937415ae7ac37305`
- Decompiled `3.1.8` Hermes output hash: `2c22a8fdab08049d236a0ba44fa5d7a25c861b4c80f81f41b3fbd9658dad0f71`

The hashes for both downloaded app releases matched the distributor's
published values, and Android signature verification succeeded with one
consistent signer. Source listings:

- <https://play.google.com/store/apps/details?id=es.appbit.prishtinabuses>
- <https://apkpure.net/trafiku-urban/es.appbit.prishtinabuses/download>
- <https://apkpure.net/trafiku-urban/es.appbit.prishtinabuses/download/3.0.5>

The current public `3.1.8` split is ARM-only. It installs on an Android 15
x86_64 AVD through native translation but exits at `MainActivity.onCreate`
because SoLoader looks for x86_64 `libreactnative.so`; the split contains only
`lib/arm64-v8a/libreactnative.so`. This is an emulator-ABI limitation, not
evidence of a crash on supported ARM devices. The publisher-signed universal
`3.0.5` build ran natively as x86_64, rendered the map, and showed live buses.
See `evidence/runtime-3.0.5.png`.

## REST verification matrix

| Method | Path | Anonymous result |
| --- | --- | --- |
| GET | `/stations` | `success=true`; 844 stations in the dated snapshot |
| GET | `/stations/{stationId}` | `success=true`; one station object |
| POST | `/stations/{stationId}/incomingBuses` | `success=true`; distance, passing lines, and live arrivals |
| GET | `/schedules/{lineId}/{stationId}` | `success=true` for a valid pair; missing pairs return HTTP 200 with `success=false` |
| GET | `/news/{limit}/{page}` | `success=true`; paginated `docs` object; Android uses `10/1` initially |
| POST | `/buses/{busId}/upcomingStations` | `success=true`; line geometry, passed stations, and upcoming stations |

The POST body observed in the anonymous app flow is:

```json
{
  "location": [21.1655, 42.6629],
  "userId": "unknown"
}
```

Coordinates consistently use GeoJSON order: longitude, then latitude.
Authenticated app sessions may attach a Firebase ID token as
`Authorization: Bearer ...`; all routes above were verified without it.

Observed response cautions:

- Application errors may still use HTTP 200 and `success=false`.
- Distance values are often decimal strings rather than JSON numbers.
- Minute values may be either an integer or text such as `"> 30"`.
- News descriptions contain HTML and must be sanitized before rendering.
- Live bus IDs and positions are transient.
- Unknown fields should be tolerated until the owner freezes a contract.

## Browser and socket behavior

`GET /stations` returned `Access-Control-Allow-Origin: *`. A preflight for the
incoming-buses POST returned HTTP 204 and allowed `content-type` and
`authorization`, so browser clients can technically call the observed API
without a proxy.

The Socket.IO transport connects at:

```text
wss://tu.appbites.dev/ws/socket.io/?EIO=4&transport=websocket
```

`bus_update` carries an array. Fields consumed by Android `3.1.8` include:

- `_id`
- `geometry.coordinates`
- `color`
- `heading`
- `line`
- `name`
- `number`
- `is_visible`

Run `node socket.mjs` to validate the handshake and print one bounded event
summary without storing the live feed.

The repository listener was exercised successfully on 2026-07-14 and received
a `bus_update` array containing 217 bus objects.

## `lak-tek` stop mapping

The four supplied map points resolve to these directional Line 1 stops:

| Role | API station | Line 1 direction |
| --- | --- | --- |
| Lakrishte source | `5d556ddb8daa9a087b28cc6c` — Dardani - Perballe Lakrishtes | `5d552616ee0dd803fc6a55b4` |
| Fakulteti Teknik destination | `5d5560518daa9a087b27f1c1` — Fakulteti Teknik (Kthimi) | `5d552616ee0dd803fc6a55b4` |
| Fakulteti Teknik source | `5d5565af8daa9a087b2847da` — Fakulteti Teknik (Shkuarja) | `5d5525d1ee0dd803fc6a51b9` |
| Lakrishte destination | `5d5566d08daa9a087b2859b1` — Lakrishte | `5d5525d1ee0dd803fc6a51b9` |

`lak_tek.py` returns structured data. Station predictions are merged by bus ID
with an optional `bus_update` payload. A live-only bus is retained only when
the exact boarding station remains in `upcoming_stations`; a station found
only in `passed_stations` is not catchable. `line1_widget.py` only formats that
result and has no route logic of its own.

Consumers choose their own polling, caching, and presentation policy. Neither
module depends on a particular website or device.

## Evidence retained in Git

- `evidence/stations-2026-07-14.json`: complete anonymous `/stations` response;
  SHA-256 `68ebe525b07a5daddd4fa91e1a6ca2a49732481e3378596f00cec0a225882b84`.
- `evidence/runtime-3.0.5.png`: ADB screenshot after a Prishtina emulator
  location fix; SHA-256 `42f39946e687ff68ac43ad2331eb9a11c1b1421e4ab32602a8d33afe90561fbb`.

Generated APKs, extracted application trees, the 896,007-line decompilation,
ADB logs, SDK state, and temporary response captures are represented by the
findings and hashes above rather than committed. This keeps the review repo
portable, secret-free, and suitable for a later public-documentation decision.

## Owner decisions still needed

- Confirm official names and semantics for every field.
- Decide whether caller location and `userId` should remain in a public contract.
- Define authentication and authorization expectations.
- Define rate limits, cache semantics, availability, versioning, and deprecation.
- License transit data and documentation for third-party reuse.
- Decide whether real-time bus positions may be archived or only displayed.
- Publish contact, support, and responsible-disclosure channels.
