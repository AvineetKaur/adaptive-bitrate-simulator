from src.events.base_event import BaseEvent


class MPDResponseEvent(BaseEvent):
    def __init__(
        self,
        event_time,
        client_id,
        server_id,
        video_name,
        available_qualities,
        segment_duration,
        total_segments
    ):
        super().__init__(
            event_time=event_time,
            event_type="MPD_RESPONSE",
            client_id=client_id,
            server_id=server_id
        )

        self.video_name = video_name
        self.available_qualities = available_qualities
        self.segment_duration = segment_duration
        self.total_segments = total_segments

    def get_event_details(self):
        details = super().get_event_details()

        details.update({
            "video_name": self.video_name,
            "available_qualities": self.available_qualities,
            "segment_duration": self.segment_duration,
            "total_segments": self.total_segments
        })

        return details