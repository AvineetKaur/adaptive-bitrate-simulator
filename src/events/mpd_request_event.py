from src.events.base_event import BaseEvent


class MPDRequestEvent(BaseEvent):
    def __init__(self, event_time, client_id, server_id, video_name):
        super().__init__(
            event_time=event_time,
            event_type="MPD_REQUEST",
            client_id=client_id,
            server_id=server_id
        )

        self.video_name = video_name