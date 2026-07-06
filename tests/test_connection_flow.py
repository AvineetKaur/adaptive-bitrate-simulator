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

print("\nClient connection state:")
print("connected_to_server:", client.connected_to_server)

print("\nServer connected clients:")
pprint(server.connected_clients)

print("\nConnection state:")
print("is_connected:", connection.is_connected)

print("\nConnection messages:")
connection.show_messages()

print("\nClient logs:")
pprint(client.logs)

print("\nServer logs:")
pprint(server.logs)