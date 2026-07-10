import json
from pathlib import Path
from typing import Any


class SimulationLogger:
    def __init__(self, output_file: str):
        self.output_file = Path(output_file)

    def save(
        self,
        clients: dict,
        server: Any,
        connection: Any,
        final_times: dict
    ) -> None:
        combined_logs = []

        # Client logs
        for client_id, client in clients.items():
            for log in client.logs:
                combined_logs.append({
                    "source": "client",
                    "client_id": client_id,
                    **log
                })

        # Server logs
        for log in server.logs:
            combined_logs.append({
                "source": "server",
                **log
            })

        # Connection messages
        for message in connection.messages:
            event_details = message["message"].get_event_details()

            combined_logs.append({
                "source": "connection",
                "direction": message["direction"],
                "event_time": event_details.get("event_time"),
                "event_type": event_details.get("event_type"),
                "client_id": event_details.get("client_id"),
                "server_id": event_details.get("server_id"),
                "message": event_details
            })

        # Final summary for every client
        for client_id, client in clients.items():
            combined_logs.append({
                "source": "simulation",
                "action": "CLIENT_SIMULATION_COMPLETED",
                "client_id": client_id,
                "video_name": client.video_name,
                "final_time": final_times[client_id],
                "final_buffer_level": client.buffer_level,
                "playback_position_sec": client.playback_position_sec,
                "quality_switch_count": client.quality_switch_count,
                "total_rebuffer_time_sec": client.total_rebuffer_time_sec,
                "bandwidth_history": client.bandwidth_history.copy()
            })

        combined_logs.sort(
            key=self._get_log_time
        )

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(self.output_file, "w", encoding="utf-8") as file:
            json.dump(
                combined_logs,
                file,
                indent=4
            )

        print(
            f"\nSimulation logs saved to: {self.output_file}"
        )

    @staticmethod
    def _get_log_time(log: dict) -> float:
        possible_time_fields = [
            "event_time",
            "request_time",
            "file_received_time",
            "current_time",
            "final_time"
        ]

        for field in possible_time_fields:
            value = log.get(field)

            if isinstance(value, (int, float)):
                return float(value)

        return 0.0