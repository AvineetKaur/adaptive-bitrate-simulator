import unittest

from src.server import Server
from src.events.segment_request_event import SegmentRequestEvent
from src.events.segment_received_event import SegmentReceivedEvent


class TestServer(unittest.TestCase):

    def test_server_object_is_created(self):
        server = Server(
            server_id="server_1",
            ip_address="127.0.0.1",
            port=8080
        )

        self.assertEqual(server.server_id, "server_1")
        self.assertEqual(server.ip_address, "127.0.0.1")
        self.assertEqual(server.port, 8080)
        self.assertEqual(server.video_segments, {})
        self.assertEqual(server.bandwidth_trace, {})
        self.assertEqual(server.logs, [])

    def test_load_bandwidth_trace_from_file(self):
        server = Server(
            server_id="server_1",
            ip_address="127.0.0.1",
            port=8080
        )

        server.load_bandwidth_trace("data/bandwidth_dataset.csv")

        self.assertEqual(server.bandwidth_trace[0], 3000.0)
        self.assertEqual(server.bandwidth_trace[1], 2500.0)
        self.assertEqual(server.bandwidth_trace[2], 1800.0)
        self.assertEqual(server.bandwidth_trace[3], 1000.0)

    def test_handle_segment_request_returns_segment_received_event(self):
        server = Server(
            server_id="server_1",
            ip_address="127.0.0.1",
            port=8080
        )

        server.load_video_segments_from_dataset("data/segment_dataset.csv")
        server.load_bandwidth_trace("data/bandwidth_dataset.csv")

        request_event = SegmentRequestEvent(
            event_time=0,
            client_id="client_1",
            server_id="server_1",
            segment_id=1,
            segment_quality=1400
        )

        response_event = server.handle_segment_request(request_event)

        print("\n--- RESPONSE EVENT ---")
        print(response_event.__dict__)

        print("\n--- SERVER LOGS ---")
        for log in server.logs:
            print(log)

        self.assertIsInstance(response_event, SegmentReceivedEvent)
        self.assertEqual(response_event.event_type, "SEGMENT_RECEIVED")
        self.assertEqual(response_event.server_id, "server_1")
        self.assertEqual(response_event.client_id, "client_1")
        self.assertEqual(response_event.segment_id, 1)
        self.assertEqual(response_event.segment_quality, 1400)
        self.assertEqual(response_event.segment_size, 700.0)
        self.assertEqual(response_event.segment_duration, 4)
        self.assertAlmostEqual(response_event.download_time, 0.2333, places=4)
        self.assertAlmostEqual(response_event.event_time, 0.2333, places=4)

    def test_handle_segment_request_raises_error_for_missing_segment(self):
        server = Server(
            server_id="server_1",
            ip_address="127.0.0.1",
            port=8080
        )

        server.load_video_segments_from_dataset("data/segment_dataset.csv")
        server.load_bandwidth_trace("data/bandwidth_dataset.csv")

        request_event = SegmentRequestEvent(
            event_time=0,
            client_id="client_1",
            server_id="server_1",
            segment_id=99,
            segment_quality=1400
        )

        with self.assertRaises(ValueError):
            server.handle_segment_request(request_event)
if __name__ == "__main__":
    unittest.main()