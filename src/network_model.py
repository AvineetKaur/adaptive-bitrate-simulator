#This owns the bandwidth traces.

import csv
class NetworkModel:
    def __init__(self):
        self.client_bandwidth_traces = {}

    def load_client_bandwidth_trace(self, client_id, bandwidth_file_path):
        bandwidth_trace = {}

        with open(bandwidth_file_path, "r") as file:
            reader = csv.DictReader(file)

            for row in reader:
                time_sec = int(row["time_sec"])
                bandwidth_kbps = float(row["bandwidth_kbps"])
                bandwidth_trace[time_sec] = bandwidth_kbps

        self.client_bandwidth_traces[client_id] = bandwidth_trace

    def get_bandwidth_at_time(self, client_id, current_time):
        if client_id not in self.client_bandwidth_traces:
            raise Exception(f"No bandwidth trace found for client {client_id}")

        current_second = int(current_time)
        bandwidth_trace = self.client_bandwidth_traces[client_id]

        if current_second not in bandwidth_trace:
            raise Exception(
                f"No bandwidth data for client {client_id} at time {current_second}"
            )

        return bandwidth_trace[current_second]

    def calculate_download_time(self, client_id, file_size_kbits, start_time):
        remaining_file_size = file_size_kbits
        current_time = start_time

        while remaining_file_size > 0:
            current_second = int(current_time)

            bandwidth_kbps = self.get_bandwidth_at_time(
                client_id=client_id,
                current_time=current_time
            )

            next_second = current_second + 1
            available_time_in_current_second = next_second - current_time

            downloadable_kbits = bandwidth_kbps * available_time_in_current_second

            if downloadable_kbits >= remaining_file_size:
                time_needed = remaining_file_size / bandwidth_kbps
                file_received_time = current_time + time_needed
                download_time_sec = file_received_time - start_time

                return {
                    "download_time_sec": download_time_sec,
                    "file_received_time": file_received_time
                }

            remaining_file_size -= downloadable_kbits
            current_time = next_second