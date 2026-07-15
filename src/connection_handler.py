class ConnectionHandler:
    def __init__(self, connection_id, client_socket, server_socket):
        self.connection_id = connection_id
        self.client_socket = client_socket
        self.server_socket = server_socket
        self.is_connected = False
        self.messages = []

    def establish_connection(self, client, server, event_time, server_id):
        if self.client_socket is not None and self.server_socket is not None:
            self.client_socket.connect(self.server_socket)

        request_event = client.create_connection_request_event(
            event_time=event_time,
            server_id=server_id,
        )

        self.messages.append({
            "direction": "client_to_server",
            "message": request_event,
        })
        print("Connection request sent from client to server")

        established_event = server.handle_connection_request_event(request_event)

        self.messages.append({
            "direction": "server_to_client",
            "message": established_event,
        })
        print("Connection established response sent from server to client")

        client.handle_connection_established_event(established_event)

        self.is_connected = True
        print(f"Connection {self.connection_id} established")
        return established_event

    def send_request_to_server(self, request_event):
        if not self.is_connected  and request_event.event_type != "CONNECTION_REQUEST":
            raise Exception("Connection is not established")

        self.messages.append({
            "direction": "client_to_server",
            "message": request_event
        })

        print("Request sent from client to server")
        return request_event

    def send_response_to_client(self, response_event):
        if not self.is_connected and response_event.event_type!="CONNECTION_ESTABLISHED":
            raise Exception("Connection is not established")

        self.messages.append({
            "direction": "server_to_client",
            "message": response_event
        })

        print("Response sent from server to client")
        return response_event

    def show_messages(self):
        
        for message in self.messages:
            print(message)
    def mark_connected(self):
        self.is_connected = True
        print(
            f"Connection {self.connection_id} established"
        )
