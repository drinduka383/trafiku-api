import unittest

from lak_tek import DIRECTIONS, arrivals
from line1_widget import render
from trafiku import TrafikuClient


class RecordingClient(TrafikuClient):
    def __init__(self):
        super().__init__()
        self.request = None

    def _request(self, method, path, payload=None):
        self.request = method, path, payload
        return {"success": True}


class ClientContractTest(unittest.TestCase):
    def test_paths_payload_and_coordinate_validation(self):
        client = RecordingClient()
        client.incoming_buses("station/one", 21.1, 42.6)
        self.assertEqual(client.request, (
            "POST",
            "/stations/station%2Fone/incomingBuses",
            {"location": [21.1, 42.6], "userId": "unknown"},
        ))
        client.schedule("line one", "station/two")
        self.assertEqual(client.request[1], "/schedules/line%20one/station%2Ftwo")
        with self.assertRaises(ValueError):
            client.upcoming_stations("bus", 181, 42.6)


class LakTekTest(unittest.TestCase):
    def test_live_snapshot_drops_stale_hidden_passed_and_off_route_buses(self):
        class FakeClient:
            def __init__(self):
                self.routes = []

            def incoming_buses(self, station_id, _longitude, _latitude):
                buses = []
                if station_id == DIRECTIONS[0]["station_id"]:
                    buses = [
                        {"_id": "predicted", "line_id": DIRECTIONS[0]["line_id"],
                         "distance_from_station_min": 3, "address": "M9"},
                        {"_id": "wrong-line", "line_id": "other", "distance_from_station_min": 1},
                    ]
                return {"success": True, "data": {"incoming_buses": buses}}

            def upcoming_stations(self, bus_id, _longitude, _latitude):
                self.routes.append(bus_id)
                stops = [{"_id": "next", "name": "Dardania"}]
                if bus_id in {"approaching", "off-route"}:
                    stops.append({"_id": DIRECTIONS[0]["station_id"], "distance_to_station_min": 7})
                return {"success": True, "data": {
                    "line_geometry": {"type": "LineString", "coordinates": [
                        [21.0, 42.0], [21.1, 42.0],
                    ]},
                    "passed_stations": [{"_id": DIRECTIONS[0]["station_id"]}],
                    "upcoming_stations": stops,
                }}

        client = FakeClient()
        line_id = DIRECTIONS[0]["line_id"]
        result = arrivals(client, [
            {"_id": "predicted", "line": {"_id": line_id}, "is_visible": False},
            {"_id": "approaching", "line": {"_id": line_id}, "is_visible": True,
             "geometry": {"coordinates": [21.05, 42.0005]}},
            {"_id": "passed", "line": {"_id": line_id}, "is_visible": True,
             "geometry": {"coordinates": [21.05, 42.0005]}},
            {"_id": "off-route", "line": {"_id": line_id}, "is_visible": True,
             "geometry": {"coordinates": [21.05, 42.01]}},
            {"_id": "hidden", "line": {"_id": line_id}, "is_visible": False},
        ])
        self.assertEqual(
            [bus["id"] for bus in result["data"]["directions"][0]["buses"]],
            ["approaching"],
        )
        self.assertEqual(client.routes, ["approaching", "passed", "off-route"])
        self.assertEqual(render(result), """lakrishte -> fakulteti teknik:
- 7 min, currently @ Dardania
- -- min, no additional approaching bus

fakulteti teknik -> lakrishte:
- -- min, no additional approaching bus
- -- min, no additional approaching bus""")
        fallback = arrivals(client)
        self.assertEqual(fallback["data"]["directions"][0]["buses"][0]["id"], "predicted")


if __name__ == "__main__":
    unittest.main()
