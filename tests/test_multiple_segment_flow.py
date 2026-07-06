import sys
from pathlib import Path
from pprint import pprint

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.client import Client
from src.server import Server
from src.connection_handler import ConnectionHandler
from src.network_model import NetworkModel
from src.event_queue import EventQueue


client = Client(client_id="client_1")

server = Server(
    server_id="server_1",
    ip_address="127.0.0.1",
    port=5000
)

network_model = NetworkModel()
event_queue = EventQueue()

server.start_server()

server.load_video_segments_from_dataset(
    dataset_path="data/videos/video_1_segments.csv",
    video_name="video_1",
    segment_duration=4
)

network_model.load_client_bandwidth_trace(
    client_id="client_1",
    bandwidth_file_path="data/traces/client_1_bandwidth.csv"
)

connection = ConnectionHandler(
    connection_id="connection_1",
    client_socket=None,
    server_socket=server.server_socket
)

connection.establish_connection(
    client=client,
    server=server,
    event_time=0,
    server_id="server_1"
)

# MPD flow
mpd_request = client.create_mpd_request_event(
    event_time=0.1,
    server_id="server_1",
    video_name="video_1"
)

connection.send_request_to_server(mpd_request)

mpd_response = server.handle_mpd_request_event(mpd_request)

connection.send_response_to_client(mpd_response)

client.handle_mpd_response_event(mpd_response)


# Multiple segment flow
current_time = 0.2

for segment_id in range(1, client.total_segments + 1):
    print("\n==============================")
    print(f"Requesting segment {segment_id}")
    print("==============================")

    current_bandwidth = network_model.get_bandwidth_at_time(
        client_id="client_1",
        current_time=current_time
    )

    segment_request = client.create_segment_request_event(
        event_time=current_time,
        server_id="server_1",
        segment_id=segment_id,
        current_bandwidth=current_bandwidth
    )

    connection.send_request_to_server(segment_request)

    segment_response = server.handle_segment_request_event(
        request_event=segment_request,
        network_model=network_model
    )

    event_queue.add_event(segment_response)

    while event_queue.has_events():
        event = event_queue.get_next_event()

        elapsed_time = event_queue.get_elapsed_time()

        client.consume_video(elapsed_time)

        if event.event_type == "SEGMENT_RECEIVED":
            connection.send_response_to_client(event)
            client.handle_segment_received_event(event)

    current_time = event_queue.current_time_sec

    print("segment_id:", segment_id)
    print("request_time:", segment_request.event_time)
    print("bandwidth:", current_bandwidth)
    print("selected_quality:", segment_request.segment_quality)
    print("download_time:", segment_response.download_time)
    print("file_received_time:", segment_response.event_time)
    print("buffer_level:", client.buffer_level)
    print("playback_started:", client.playback_started)
    print("playback_position_sec:", client.playback_position_sec)


print("\n==============================")
print("Final client state")
print("==============================")
print("final_simulation_time:", event_queue.current_time_sec)
print("buffer_level:", client.buffer_level)
print("buffered_segments:")
pprint(client.buffered_segments)
print("playback_started:", client.playback_started)
print("playback_position_sec:", client.playback_position_sec)

print("\nClient logs:")
pprint(client.logs)

print("\nServer logs:")
pprint(server.logs)