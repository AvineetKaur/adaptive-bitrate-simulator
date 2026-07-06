from src.events.base_event import BaseEvent


class SegmentReceivedEvent(BaseEvent):
    def __init__(
        self,
        event_time,
        client_id,
        server_id,
        video_name,
        segment_id,
        segment_quality,
        segment_size,
        segment_duration,
        download_time,
        request_time,
        deadline_time
    ):
        super().__init__(
            event_time=event_time,
            event_type="SEGMENT_RECEIVED",
            client_id=client_id,
            server_id=server_id
        )

        self.video_name = video_name
        self.segment_id = segment_id
        self.segment_quality = segment_quality
        self.segment_size = segment_size
        self.segment_duration = segment_duration
        self.download_time = download_time
        self.request_time = request_time
        self.deadline_time = deadline_time

    def get_event_details(self):
        details = super().get_event_details()

        details.update({
            "video_name": self.video_name,
            "segment_id": self.segment_id,
            "segment_quality": self.segment_quality,
            "segment_size": self.segment_size,
            "segment_duration": self.segment_duration,
            "download_time": self.download_time,
            "request_time": self.request_time,
            "deadline_time": self.deadline_time
        })

        return details