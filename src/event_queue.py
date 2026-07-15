import heapq


class EventQueue:
    def __init__(self):
        self.events = []
        self.current_time_sec = 0
        self.previous_event_time_sec = 0
        self.event_counter = 0

        # Stores queue activity for later JSON/CSV output
        self.logs = []

    def add_event(self, event):
        queue_size_before = len(self.events)

        heapq.heappush(
            self.events,
            (
                event.event_time,
                self.event_counter,
                event
            )
        )

        self.logs.append({
            "source": "event_queue",
            "action": "EVENT_ADDED",
            "event_type": event.event_type,
            "event_time": event.event_time,
            "client_id": event.client_id,
            "server_id": event.server_id,
            "event_counter": self.event_counter,
            "queue_size_before": queue_size_before,
            "queue_size_after": len(self.events),
            "current_simulation_time": self.current_time_sec
        })

        print(
            f"[QUEUE ADD] "
            f"time={event.event_time:.3f} | "
            f"client={event.client_id} | "
            f"event={event.event_type} | "
            f"queue_size={len(self.events)}"
        )

        self.event_counter += 1

    def get_next_event(self):
        if not self.events:
            return None

        queue_size_before = len(self.events)

        event_time, event_counter, event = heapq.heappop(
            self.events
        )

        self.previous_event_time_sec = (
            self.current_time_sec
        )

        self.current_time_sec = event_time

        elapsed_time = (
            self.current_time_sec
            - self.previous_event_time_sec
        )

        self.logs.append({
            "source": "event_queue",
            "action": "EVENT_REMOVED",
            "event_type": event.event_type,
            "event_time": event.event_time,
            "client_id": event.client_id,
            "server_id": event.server_id,
            "event_counter": event_counter,
            "queue_size_before": queue_size_before,
            "queue_size_after": len(self.events),
            "previous_simulation_time":
                self.previous_event_time_sec,
            "current_simulation_time":
                self.current_time_sec,
            "elapsed_time": elapsed_time
        })

        print(
            f"[QUEUE REMOVE] "
            f"time={event.event_time:.3f} | "
            f"elapsed={elapsed_time:.3f} | "
            f"client={event.client_id} | "
            f"event={event.event_type} | "
            f"queue_size={len(self.events)}"
        )

        return event

    def get_elapsed_time(self):
        return (
            self.current_time_sec
            - self.previous_event_time_sec
        )

    def has_events(self):
        return len(self.events) > 0