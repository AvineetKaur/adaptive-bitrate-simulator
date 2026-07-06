import sys
from pathlib import Path
from pprint import pprint

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.client import Client
from src.server import Server
from src.connection_handler import ConnectionHandler


client = Client(client_id="client_1")

server = Server(
    server_id="server_1",
    ip_address="127.0.0.1",
    port=5000
)

server.start_server()

server.load_video_segments_from_dataset(
    dataset_path="data/videos/video_1_segments.csv",
    video_name="video_1",
    segment_duration=4
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

mpd_request = client.create_mpd_request_event(
    event_time=0.1,
    server_id="server_1",
    video_name="video_1"
)

connection.send_request_to_server(mpd_request)

mpd_response = server.handle_mpd_request_event(mpd_request)

connection.send_response_to_client(mpd_response)

client.handle_mpd_response_event(mpd_response)

print("\nClient MPD state:")
print("video_name:", client.video_name)
print("available_bitrates:", client.available_qualities)
print("segment_duration:", client.segment_duration)
print("total_segments:", client.total_segments)

print("\nMPD response event:")
pprint(mpd_response.get_event_details())

print("\nConnection messages:")
connection.show_messages()

print("\nClient logs:")
pprint(client.logs)

print("\nServer logs:")
pprint(server.logs)