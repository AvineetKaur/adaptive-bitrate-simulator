import unittest

from src.events.segment_request_event import SegmentRequestEvent
from src.events.segment_received_event import SegmentReceivedEvent


class TestEvents(unittest.TestCase):

    def test_segment_request_event_stores_values(self):
        event = SegmentRequestEvent(
            event_time=0,
            client_id="client_1",
            server_id="server_1",
            segment_id=1,
            segment_quality=1400
        )

        self.assertEqual(event.event_time, 0)
        self.assertEqual(event.event_type, "SEGMENT_REQUEST")
        self.assertEqual(event.client_id, "client_1")
        self.assertEqual(event.server_id, "server_1")
        self.assertEqual(event.segment_id, 1)
        self.assertEqual(event.segment_quality, 1400)

    def test_segment_received_event_stores_values(self):
        event = SegmentReceivedEvent(
            event_time=0.35,
            server_id="server_1",
            client_id="client_1",
            segment_id=1,
            segment_quality=1400,
            segment_size=700,
            segment_duration=4,
            download_time= 0.35
        )

        self.assertEqual(event.event_time, 0.35)
        self.assertEqual(event.event_type, "SEGMENT_RECEIVED")
        self.assertEqual(event.server_id, "server_1")
        self.assertEqual(event.client_id, "client_1")
        self.assertEqual(event.segment_id, 1)
        self.assertEqual(event.segment_quality, 1400)
        self.assertEqual(event.segment_size, 700)
        self.assertEqual(event.segment_duration, 4)
        self.assertEqual(event.download_time, 0.35)


if __name__ == "__main__":
    unittest.main()