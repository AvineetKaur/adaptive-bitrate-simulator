from src.events.base_event import BaseEvent


class ConnectionEstablishedEvent(BaseEvent):
    def __init__(self, event_time, client_id, server_id):
        super().__init__(
            event_time=event_time,
            event_type="CONNECTION_ESTABLISHED",
            client_id=client_id,
            server_id=server_id
        )