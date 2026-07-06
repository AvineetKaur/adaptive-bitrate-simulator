from src.server import Server
from src.socket_model import Socket
from src.connection_handler import ConnectionHandler
from src.events.base_event import Event, SEGMENT_REQUEST

server = Server(
    server_id="server_1",
    ip_address="127.0.0.1",
    port=8000
)

server.start_server()

client_socket = Socket(
    owner_id="client_1",
    ip_address="127.0.0.1",
    port=5000
)

client_socket.open()

connection = ConnectionHandler(
    connection_id="connection_1",
    client_socket=client_socket,
    server_socket=server.server_socket
)

connection.establish_connection()

server.load_video_segments_from_dataset(
    dataset_path="data/segment_dataset.csv"
)

server.update_network_state(
    bandwidth_kbps=2800,
    latency_sec=0
)

request_event = Event(
    event_time=2,
    event_type=SEGMENT_REQUEST,
    data={
        "client_id": "client_1",
        "segment_id": 1,
        "bitrate_kbps": 1400
    }
)

request_to_server = connection.send_request_to_server(request_event)

response_event = server.handle_event(request_to_server)

connection.send_response_to_client(response_event)

print("Final outcome:")
print(response_event)