import unittest

from src.client import Client
from src.server import Server
from src.socket_model import Socket
from src.connection_handler import ConnectionHandler
from src.events.connection_request_event import ConnectionRequestEvent
from src.events.connection_established_event import ConnectionEstablishedEvent


class TestConnectionEstablishment(unittest.TestCase):

    def setUp(self):
        self.client = Client(client_id="client_1")
        self.server = Server(
            server_id="server_1",
            ip_address="127.0.0.1",
            port=8080,
        )
        self.server.start_server()

        self.client_socket = Socket(
            owner_id="client_1",
            ip_address="127.0.0.1",
            port=5000,
        )
        self.client_socket.open()

        self.connection = ConnectionHandler(
            connection_id="connection_1",
            client_socket=self.client_socket,
            server_socket=self.server.server_socket,
        )

    def test_connection_request_event_stores_values(self):
        event = ConnectionRequestEvent(
            event_time=0,
            client_id="client_1",
            server_id="server_1",
        )

        self.assertEqual(event.event_time, 0)
        self.assertEqual(event.event_type, "CONNECTION_REQUEST")
        self.assertEqual(event.client_id, "client_1")
        self.assertEqual(event.server_id, "server_1")

    def test_connection_established_event_stores_values(self):
        event = ConnectionEstablishedEvent(
            event_time=0,
            client_id="client_1",
            server_id="server_1",
        )

        self.assertEqual(event.event_time, 0)
        self.assertEqual(event.event_type, "CONNECTION_ESTABLISHED")
        self.assertEqual(event.client_id, "client_1")
        self.assertEqual(event.server_id, "server_1")

    def test_server_handles_connection_request(self):
        request_event = ConnectionRequestEvent(
            event_time=1,
            client_id="client_1",
            server_id="server_1",
        )

        response_event = self.server.handle_connection_request(request_event)

        self.assertIsInstance(response_event, ConnectionEstablishedEvent)
        self.assertEqual(response_event.event_type, "CONNECTION_ESTABLISHED")
        self.assertEqual(response_event.client_id, "client_1")
        self.assertEqual(response_event.server_id, "server_1")
        self.assertEqual(len(self.server.logs), 1)
        self.assertEqual(self.server.logs[0]["action"], "CONNECTION_REQUEST_HANDLED")

    def test_establish_connection_full_flow(self):
        established_event = self.connection.establish_connection(
            client=self.client,
            server=self.server,
            event_time=0,
            client_id="client_1",
            server_id="server_1",
        )

        self.assertTrue(self.connection.is_connected)
        self.assertIsInstance(established_event, ConnectionEstablishedEvent)
        self.assertEqual(established_event.event_type, "CONNECTION_ESTABLISHED")
        self.assertEqual(len(self.connection.messages), 2)
        self.assertEqual(
            self.connection.messages[0]["message"].event_type,
            "CONNECTION_REQUEST",
        )
        self.assertEqual(
            self.connection.messages[1]["message"].event_type,
            "CONNECTION_ESTABLISHED",
        )
        self.assertEqual(self.client.logs[0]["action"], "CONNECTION_REQUEST_CREATED")
        self.assertEqual(self.client.logs[1]["action"], "CONNECTION_ESTABLISHED_HANDLED")

    def test_send_request_fails_before_connection(self):
        request_event = ConnectionRequestEvent(
            event_time=0,
            client_id="client_1",
            server_id="server_1",
        )

        with self.assertRaises(Exception):
            self.connection.send_request_to_server(request_event)


if __name__ == "__main__":
    unittest.main()
