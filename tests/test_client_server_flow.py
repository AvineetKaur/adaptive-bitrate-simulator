import unittest

from src.client import Client
from src.server import Server
from src.events.segment_request_event import SegmentRequestEvent
from src.events.segment_received_event import SegmentReceivedEvent


class TestClientServerFlow(unittest.TestCase):

    def test_client_server_one_segment_flow(self):
        client = Client(client_id="client_1")

        server = Server(
            server_id="server_1",
            ip_address="127.0.0.1",
            port=8080
        )

        server.load_video_segments_from_dataset("data/segment_dataset.csv")
        server.load_bandwidth_trace("data/bandwidth_dataset.csv")

        selected_quality = client.select_bitrate(3000)

        request_event = SegmentRequestEvent(
            event_time=0,
            client_id="client_1",
            server_id="server_1",
            segment_id=1,
            segment_quality=selected_quality
        )

        response_event = server.handle_segment_request(request_event)

        self.assertIsInstance(response_event, SegmentReceivedEvent)
        self.assertEqual(response_event.event_type, "SEGMENT_RECEIVED")
        self.assertEqual(response_event.client_id, "client_1")
        self.assertEqual(response_event.server_id, "server_1")
        self.assertEqual(response_event.segment_id, 1)

        client.handle_segment_received_event(response_event)
        print("\n--- REQUEST EVENT ---")
        print(request_event.__dict__)
        print("\n--- RESPONSE EVENT ---")
        print(response_event.__dict__)
        print("\n--- CLIENT BUFFER ---")
        print(client.buffered_segments)
        print("\n--- CLIENT LOGS ---")
        for log in client.logs:
            print(log)
        print("\n--- SERVER LOGS ---")
        for log in server.logs:
            print(log)


        self.assertEqual(client.buffer_level, 4)
        self.assertEqual(len(client.buffered_segments), 1)
        self.assertEqual(client.buffered_segments[0]["segment_id"], 1)
        self.assertEqual(client.buffered_segments[0]["remaining_duration_sec"], 4)


if __name__ == "__main__":
    unittest.main()