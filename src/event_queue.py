import heapq


class EventQueue:
    def __init__(self):
        self.events = []
        self.current_time_sec = 0
        self.previous_event_time_sec = 0
        self.event_counter = 0

    def add_event(self, event):
        heapq.heappush(
            self.events,
            (event.event_time, self.event_counter, event)
        )
        self.event_counter += 1

    def get_next_event(self):
        if not self.events:
            return None

        event_time, _, event = heapq.heappop(self.events)

        self.previous_event_time_sec = self.current_time_sec
        self.current_time_sec = event_time

        return event

    def get_elapsed_time(self):
        return self.current_time_sec - self.previous_event_time_sec

    def has_events(self):
        return len(self.events) > 0