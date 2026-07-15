from src.events.base_event import Event


class PlaybackCompletedEvent(Event):
    def __init__(
        self,
        event_time,
        client_id,
        server_id
    ):
        super().__init__(
            event_time=event_time,
            event_type="PLAYBACK_COMPLETED",
            client_id=client_id,
            server_id=server_id
        )