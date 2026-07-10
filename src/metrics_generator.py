import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


class MetricsGenerator:
    def __init__(
        self,
        input_log_file,
        output_directory
    ):
        self.input_log_file = Path(input_log_file)
        self.output_directory = Path(output_directory)

    def generate(self):
        logs = self._load_logs()

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        segment_rows, summary_rows = self._build_metrics(logs)

        self._save_segment_metrics(segment_rows)
        self._save_summary_metrics(summary_rows)
        self._save_flat_event_logs(logs)

        print(
            f"Metrics CSV files saved to: "
            f"{self.output_directory}"
        )

    def _load_logs(self):
        if not self.input_log_file.exists():
            raise FileNotFoundError(
                f"Simulation log not found: "
                f"{self.input_log_file}"
            )

        with open(
            self.input_log_file,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def _build_metrics(self, logs):
        logs_by_client = defaultdict(list)

        for entry in logs:
            client_id = entry.get("client_id")

            if client_id:
                logs_by_client[client_id].append(entry)

        segment_rows = []
        summary_rows = []

        for client_id in sorted(logs_by_client):
            client_logs = logs_by_client[client_id]

            mpd_log = next(
                (
                    entry
                    for entry in client_logs
                    if entry.get("action")
                    == "MPD_RESPONSE_RECEIVED"
                ),
                {}
            )

            video_name = mpd_log.get("video_name")
            total_segments = mpd_log.get(
                "total_segments",
                0
            )
            segment_duration = mpd_log.get(
                "segment_duration"
            )

            throughput_logs = self._filter_logs(
                client_logs,
                action="THROUGHPUT_ESTIMATION",
                source="client"
            )

            abr_logs = self._filter_logs(
                client_logs,
                action="ABR_QUALITY_SELECTED",
                source="client"
            )

            request_logs = self._filter_logs(
                client_logs,
                action="SEGMENT_REQUEST_CREATED",
                source="client"
            )

            received_logs = self._filter_logs(
                client_logs,
                action="SEGMENT_RECEIVED_HANDLED",
                source="client"
            )

            buffer_logs = self._filter_logs(
                client_logs,
                action="SEGMENT_ADDED_TO_BUFFER",
                source="client"
            )

            server_logs = self._filter_logs(
                client_logs,
                action="SEGMENT_REQUEST_HANDLED",
                source="server"
            )

            simulation_summary = next(
                (
                    entry
                    for entry in client_logs
                    if entry.get("source") == "simulation"
                    and entry.get("action")
                    == "CLIENT_SIMULATION_COMPLETED"
                ),
                {}
            )

            request_by_segment = {
                entry["segment_id"]: entry
                for entry in request_logs
                if entry.get("segment_id") is not None
            }

            received_by_segment = {
                entry["segment_id"]: entry
                for entry in received_logs
                if entry.get("segment_id") is not None
            }

            buffer_by_segment = {
                entry["segment_id"]: entry
                for entry in buffer_logs
                if entry.get("segment_id") is not None
            }

            server_by_segment = {
                entry["segment_id"]: entry
                for entry in server_logs
                if entry.get("segment_id") is not None
            }

            client_segment_rows = []

            for segment_id in range(
                1,
                total_segments + 1
            ):
                throughput_log = (
                    throughput_logs[segment_id - 1]
                    if segment_id - 1
                    < len(throughput_logs)
                    else {}
                )

                abr_log = (
                    abr_logs[segment_id - 1]
                    if segment_id - 1
                    < len(abr_logs)
                    else {}
                )

                request_log = request_by_segment.get(
                    segment_id,
                    {}
                )

                received_log = received_by_segment.get(
                    segment_id,
                    {}
                )

                buffer_log = buffer_by_segment.get(
                    segment_id,
                    {}
                )

                server_log = server_by_segment.get(
                    segment_id,
                    {}
                )

                request_time = request_log.get(
                    "event_time",
                    server_log.get("request_time")
                )

                received_time = server_log.get(
                    "file_received_time"
                )

                deadline_time = request_log.get(
                    "deadline_time"
                )

                deadline_missed = None

                if (
                    received_time is not None
                    and deadline_time is not None
                ):
                    deadline_missed = (
                        received_time > deadline_time
                    )

                row = {
                    "client_id": client_id,
                    "video_name": video_name,
                    "segment_id": segment_id,
                    "request_time_sec": request_time,
                    "received_time_sec": received_time,
                    "deadline_time_sec": deadline_time,
                    "deadline_missed": deadline_missed,
                    "selected_quality_kbps": (
                        request_log.get(
                            "segment_quality",
                            received_log.get(
                                "bitrate_kbps",
                                abr_log.get(
                                    "selected_quality"
                                )
                            )
                        )
                    ),
                    "file_size_kbits": received_log.get(
                        "file_size_kbits",
                        server_log.get("segment_size")
                    ),
                    "download_time_sec": received_log.get(
                        "download_time_sec",
                        server_log.get(
                            "download_time_sec"
                        )
                    ),
                    "measured_bandwidth_kbps":
                        received_log.get(
                            "measured_bandwidth_kbps"
                        ),
                    "average_previous_bandwidth_kbps":
                        throughput_log.get(
                            "average_previous_bandwidth"
                        ),
                    "estimated_throughput_kbps":
                        abr_log.get(
                            "estimated_throughput",
                            throughput_log.get(
                                "estimated_throughput"
                            )
                        ),
                    "buffer_state":
                        throughput_log.get(
                            "buffer_state"
                        ),
                    "buffer_level_after_segment_sec":
                        received_log.get(
                            "buffer_level",
                            buffer_log.get(
                                "buffer_level_sec"
                            )
                        ),
                    "playback_started":
                        received_log.get(
                            "playback_started"
                        )
                }

                segment_rows.append(row)
                client_segment_rows.append(row)

            summary_rows.append(
                self._build_client_summary(
                    client_id=client_id,
                    video_name=video_name,
                    segment_duration=segment_duration,
                    segment_rows=client_segment_rows,
                    simulation_summary=simulation_summary
                )
            )

        return segment_rows, summary_rows

    @staticmethod
    def _filter_logs(
        logs,
        action,
        source=None
    ):
        return [
            entry
            for entry in logs
            if entry.get("action") == action
            and (
                source is None
                or entry.get("source") == source
            )
        ]

    @staticmethod
    def _build_client_summary(
        client_id,
        video_name,
        segment_duration,
        segment_rows,
        simulation_summary
    ):
        qualities = [
            row["selected_quality_kbps"]
            for row in segment_rows
            if row["selected_quality_kbps"]
            is not None
        ]

        measured_bandwidths = [
            row["measured_bandwidth_kbps"]
            for row in segment_rows
            if row["measured_bandwidth_kbps"]
            is not None
        ]

        estimated_throughputs = [
            row["estimated_throughput_kbps"]
            for row in segment_rows
            if row["estimated_throughput_kbps"]
            is not None
        ]

        download_times = [
            row["download_time_sec"]
            for row in segment_rows
            if row["download_time_sec"]
            is not None
        ]

        buffer_levels = [
            row["buffer_level_after_segment_sec"]
            for row in segment_rows
            if row["buffer_level_after_segment_sec"]
            is not None
        ]

        calculated_switch_count = sum(
            1
            for index in range(
                1,
                len(qualities)
            )
            if qualities[index]
            != qualities[index - 1]
        )

        first_request = min(
            (
                row["request_time_sec"]
                for row in segment_rows
                if row["request_time_sec"]
                is not None
            ),
            default=None
        )

        first_received = min(
            (
                row["received_time_sec"]
                for row in segment_rows
                if row["received_time_sec"]
                is not None
            ),
            default=None
        )

        startup_delay = None

        if (
            first_request is not None
            and first_received is not None
        ):
            startup_delay = (
                first_received - first_request
            )

        return {
            "client_id": client_id,
            "video_name": video_name,
            "total_segments": len(segment_rows),
            "total_video_duration_sec": (
                len(segment_rows)
                * segment_duration
                if segment_duration is not None
                else None
            ),
            "average_selected_quality_kbps": (
                statistics.mean(qualities)
                if qualities
                else None
            ),
            "minimum_selected_quality_kbps": (
                min(qualities)
                if qualities
                else None
            ),
            "maximum_selected_quality_kbps": (
                max(qualities)
                if qualities
                else None
            ),
            "quality_switch_count":
                simulation_summary.get(
                    "quality_switch_count",
                    calculated_switch_count
                ),
            "average_measured_bandwidth_kbps": (
                statistics.mean(
                    measured_bandwidths
                )
                if measured_bandwidths
                else None
            ),
            "average_estimated_throughput_kbps": (
                statistics.mean(
                    estimated_throughputs
                )
                if estimated_throughputs
                else None
            ),
            "total_download_time_sec": (
                sum(download_times)
                if download_times
                else None
            ),
            "average_download_time_sec": (
                statistics.mean(download_times)
                if download_times
                else None
            ),
            "startup_delay_sec": startup_delay,
            "deadline_miss_count": sum(
                1
                for row in segment_rows
                if row["deadline_missed"] is True
            ),
            "average_buffer_after_segment_sec": (
                statistics.mean(buffer_levels)
                if buffer_levels
                else None
            ),
            "final_buffer_level_sec":
                simulation_summary.get(
                    "final_buffer_level"
                ),
            "playback_position_sec":
                simulation_summary.get(
                    "playback_position_sec"
                ),
            "total_rebuffer_time_sec":
                simulation_summary.get(
                    "total_rebuffer_time_sec"
                ),
            "simulation_completion_time_sec":
                simulation_summary.get(
                    "final_time"
                )
        }

    def _save_segment_metrics(
        self,
        rows
    ):
        if not rows:
            return

        output_file = (
            self.output_directory
            / "segment_metrics.csv"
        )

        self._write_csv(
            output_file,
            rows
        )

    def _save_summary_metrics(
        self,
        rows
    ):
        if not rows:
            return

        output_file = (
            self.output_directory
            / "client_summary_metrics.csv"
        )

        self._write_csv(
            output_file,
            rows
        )

    def _save_flat_event_logs(
        self,
        logs
    ):
        output_file = (
            self.output_directory
            / "flat_event_logs.csv"
        )

        all_columns = sorted(
            {
                key
                for entry in logs
                for key in entry.keys()
            }
        )

        flattened_rows = []

        for entry in logs:
            row = {}

            for column in all_columns:
                value = entry.get(column)

                if isinstance(
                    value,
                    (dict, list)
                ):
                    value = json.dumps(value)

                row[column] = value

            flattened_rows.append(row)

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=all_columns
            )

            writer.writeheader()
            writer.writerows(
                flattened_rows
            )

    @staticmethod
    def _write_csv(
        output_file,
        rows
    ):
        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(
                    rows[0].keys()
                )
            )

            writer.writeheader()
            writer.writerows(rows)