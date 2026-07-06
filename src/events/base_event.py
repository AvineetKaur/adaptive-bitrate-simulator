class BaseEvent:
    def __init__(self, event_time, event_type, client_id, server_id):
        self.event_time = event_time
        self.event_type = event_type
        self.client_id = client_id
        self.server_id = server_id

    def get_event_details(self):
        return {
            "event_time": self.event_time,
            "event_type": self.event_type,
            "client_id": self.client_id,
            "server_id": self.server_id
        }

    def __repr__(self):
        return (
            f"Event("
            f"time={self.event_time}, "
            f"type={self.event_type}, "
            f"client={self.client_id}, "
            f"server={self.server_id}"
            f")"
        )