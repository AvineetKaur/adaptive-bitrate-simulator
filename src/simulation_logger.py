import json
from pathlib import Path
from typing import Any


class SimulationLogger:
    def __init__(self, output_file: str):
        self.output_file = Path(output_file)

    def save(
        self,
        run_id: str,
        clients: dict,
        server: Any,
        connections: dict,
        event_queue: Any,
        final_times: dict
    ) -> None:
        combined_logs = []

        # One separate list for every client's logs
        client_logs = {
            client_id: []
            for client_id in clients
        }

        # ==========================================
        # Client logs
        # ==========================================

        for client_id, client in clients.items():
            for log in client.logs:
                log_entry = {
                    "run_id": run_id,
                    "source": "client",
                    "client_id": client_id,
                    **log
                }

                combined_logs.append(log_entry)
                client_logs[client_id].append(log_entry)

        # ==========================================
        # Server logs
        # ==========================================

        for log in server.logs:
            log_entry = {
                "run_id": run_id,
                "source": "server",
                **log
            }

            combined_logs.append(log_entry)

            client_id = log.get("client_id")

            if client_id in client_logs:
                client_logs[client_id].append(
                    log_entry
                )

        # ==========================================
        # EventQueue logs
        # ==========================================

        for log in event_queue.logs:
            log_entry = {
                "run_id": run_id,
                **log
            }

            combined_logs.append(log_entry)

            client_id = log.get("client_id")

            if client_id in client_logs:
                client_logs[client_id].append(
                    log_entry
                )

        # ==========================================
        # Connection messages
        # ==========================================

        for client_id, connection in connections.items():
            for message in connection.messages:
                event_details = (
                    message["message"]
                    .get_event_details()
                )

                log_entry = {
                    "run_id": run_id,
                    "source": "connection",
                    "connection_id":
                        connection.connection_id,
                    "client_id": client_id,
                    "direction":
                        message["direction"],
                    "event_time":
                        event_details.get(
                            "event_time"
                        ),
                    "event_type":
                        event_details.get(
                            "event_type"
                        ),
                    "server_id":
                        event_details.get(
                            "server_id"
                        ),
                    "message":
                        event_details
                }

                combined_logs.append(log_entry)
                client_logs[client_id].append(
                    log_entry
                )

        # ==========================================
        # Final summary for every client
        # ==========================================

        for client_id, client in clients.items():

            # Average measured bandwidth
            if client.bandwidth_history:
                average_measured_bandwidth = (
                    sum(client.bandwidth_history)
                    / len(client.bandwidth_history)
                )
            else:
                average_measured_bandwidth = 0

            # Average estimated throughput
            if client.throughput_history:
                average_estimated_throughput = (
                    sum(client.throughput_history)
                    / len(client.throughput_history)
                )
            else:
                average_estimated_throughput = 0

            # Quality-switch metrics
            if client.quality_switch_magnitudes:
                average_switch_magnitude = (
                    sum(
                        client.quality_switch_magnitudes
                    )
                    / len(
                        client.quality_switch_magnitudes
                    )
                )

                maximum_switch_magnitude = max(
                    client.quality_switch_magnitudes
                )
            else:
                average_switch_magnitude = 0
                maximum_switch_magnitude = 0

            # Stall metrics
            if client.stall_durations_sec:
                average_stall_duration = (
                    sum(client.stall_durations_sec)
                    / len(client.stall_durations_sec)
                )

                maximum_stall_duration = max(
                    client.stall_durations_sec
                )
            else:
                average_stall_duration = 0
                maximum_stall_duration = 0

            summary_log = {
                "run_id": run_id,
                "source": "simulation",
                "action":
                    "CLIENT_SIMULATION_COMPLETED",

                "client_id": client_id,
                "video_name": client.video_name,

                "final_simulation_time_sec":
                    final_times.get(client_id, 0),

                "playback_position_sec":
                    client.playback_position_sec,

                "final_buffer_level_sec":
                    client.buffer_level,

                "playback_started":
                    client.playback_started,

                # Quality metrics
                "quality_switch_count":
                    client.quality_switch_count,

                "upward_switch_count":
                    client.upward_switch_count,

                "downward_switch_count":
                    client.downward_switch_count,

                "average_switch_magnitude_kbps":
                    average_switch_magnitude,

                "maximum_switch_magnitude_kbps":
                    maximum_switch_magnitude,

                # Stall metrics
                "stall_count":
                    client.stall_count,

                "total_rebuffer_time_sec":
                    client.total_rebuffer_time_sec,

                "average_stall_duration_sec":
                    average_stall_duration,

                "maximum_stall_duration_sec":
                    maximum_stall_duration,

                # Bandwidth metrics
                "average_measured_bandwidth_kbps":
                    average_measured_bandwidth,

                "average_estimated_throughput_kbps":
                    average_estimated_throughput,

                # Histories
                "bandwidth_history":
                    client.bandwidth_history.copy(),

                "throughput_history":
                    client.throughput_history.copy(),

                "stall_durations_sec":
                    client.stall_durations_sec.copy(),

                "quality_switch_magnitudes":
                    client.quality_switch_magnitudes.copy()
            }

            # Add this client's summary to both places
            combined_logs.append(summary_log)
            client_logs[client_id].append(
                summary_log
            )

        # ==========================================
        # Sort combined logs
        # ==========================================

        combined_logs.sort(
            key=self._get_log_time
        )

        # ==========================================
        # Create output folder
        # ==========================================

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # ==========================================
        # Save combined simulation log
        # ==========================================

        with open(
            self.output_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                combined_logs,
                file,
                indent=4
            )

        print(
            f"\nSimulation logs saved to: "
            f"{self.output_file}"
        )

        # ==========================================
        # Save one JSON file per client
        # ==========================================

        for client_id, logs in client_logs.items():
            logs.sort(
                key=self._get_log_time
            )

            client_log_file = (
                self.output_file.parent
                / f"{client_id}_logs.json"
            )

            with open(
                client_log_file,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    logs,
                    file,
                    indent=4
                )

            print(
                f"Client log saved to: "
                f"{client_log_file}"
            )

    @staticmethod
    def _get_log_time(log: dict) -> float:
        possible_time_fields = [
            "event_time",
            "request_time",
            "file_received_time",
            "current_time",
            "current_simulation_time",
            "final_time",
            "final_simulation_time_sec"
        ]

        for field in possible_time_fields:
            value = log.get(field)

            if isinstance(value, (int, float)):
                return float(value)

        return 0.0