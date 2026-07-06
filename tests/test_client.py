import unittest

from src.client import Client

class TestClient(unittest.TestCase):

    ## Test cases for select bitrate
    def test_select_bitrate_selects_1400_when_bandwidth_is_2000(self):
        client = Client(client_id="client_1")

        selected_bitrate = client.select_bitrate(2000)

        self.assertEqual(selected_bitrate, 1400)
    
    def test_select_bitrate_selects_800_when_bandwidth_is_1200(self):
        client = Client(client_id="client_1")

        selected_bitrate = client.select_bitrate(1200)

        self.assertEqual(selected_bitrate, 800)

    def test_select_bitrate_raises_error_when_bandwidth_too_low(self):

        client = Client(client_id="client_1")

        with self.assertRaises(ValueError):
            client.select_bitrate(500)

    ## Test Case for add to buffer        
    def test_add_to_buffer_adds_one_segment(self):
        client = Client(client_id="client_1")

        client.add_to_buffer(segment_id=1, segment_duration=4)

        self.assertEqual(client.buffer_level, 4)
        self.assertEqual(len(client.buffered_segments), 1)
        self.assertEqual(client.buffered_segments[0]["segment_id"], 1)
        self.assertEqual(client.buffered_segments[0]["remaining_duration_sec"], 4)

    def test_can_start_playback_returns_true_when_buffer_enough(self):
        client = Client(client_id="client_1")

        client.add_to_buffer(segment_id=1, segment_duration=4)

        result = client.can_start_playback()

        self.assertTrue(result)

    def test_start_playback_if_ready_starts_playback(self):
        client = Client(client_id="client_1")

        client.add_to_buffer(segment_id=1, segment_duration=4)

        result = client.start_playback(current_time=0.35)

        self.assertTrue(result)
        self.assertTrue(client.playback_started)
        
    def test_consume_video_consumes_partial_segment(self):
        client = Client(client_id="client_1")
        client.playback_started = True

        client.add_to_buffer(segment_id=1, segment_duration=4)

        client.consume_video(playback_time=2)

        self.assertEqual(client.buffer_level, 2)
        self.assertEqual(client.playback_position_sec, 2)
        self.assertEqual(client.buffered_segments[0]["remaining_duration_sec"], 2)
if __name__ == "__main__":
    unittest.main()