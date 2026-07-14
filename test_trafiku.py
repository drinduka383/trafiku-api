import unittest

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


if __name__ == "__main__":
    unittest.main()
