import unittest

from line1_widget import DIRECTIONS, render
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


class Line1WidgetTest(unittest.TestCase):
    def test_filters_sorts_and_pads_each_direction(self):
        class FakeClient:
            def incoming_buses(self, station_id, _longitude, _latitude):
                if station_id != DIRECTIONS[0][1]:
                    return {"success": True, "data": {"incoming_buses": []}}
                line_id = DIRECTIONS[0][2]
                return {"success": True, "data": {"incoming_buses": [
                    {"line_id": line_id, "distance_from_station_min": 9, "address": "Lakrishtë"},
                    {"line_id": "another-line", "distance_from_station_min": 1, "address": "wrong"},
                    {"line_id": line_id, "distance_from_station_min": 3, "address": "Rr. Nëna Terezë"},
                ]}}

        self.assertEqual(render(FakeClient()), """lakrishte -> fakulteti teknik:
- 3 min, currently @ Rr. Nena Tereze
- 9 min, currently @ Lakrishte

fakulteti teknik -> lakrishte:
- -- min, no live bus reported
- -- min, no live bus reported""")


if __name__ == "__main__":
    unittest.main()
