class Socket:
    def __init__(self,owner_id,ip_address,port):
        self.owner_id = owner_id
        self.ip_address = ip_address
        self.port = port
        self.is_open = False
        self.connected_to = None
    
    def open(self):
        self.is_open=True
        print(f"{self.owner_id} socket opened at {self.ip_address}:{self.port}")

    def connect(self,other_socket):
        if not self.is_open:
            raise Exception(f"{self.owner_id} socket is not open")
         
        if not other_socket.is_open:
            raise Exception(f"{other_socket.owner_id} socket is not open")
        
        self.connected_to = other_socket
        other_socket.connected_to = self

        print(f"{self.owner_id} connected to {other_socket.owner_id}")
    
    def close(self):
        self.is_open = False
        self.connected_to = None
        print(f"{self.owner_id} socket closed")