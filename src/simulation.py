from src.client import Client
from src.server import Server
from src.network_model import NetworkModel
from src.connection_handler import ConnectionHandler
from src.event_queue import EventQueue
from src.simulation_logger import SimulationLogger
from src.metrics_generator import MetricsGenerator
from datetime import datetime
from pathlib import Path

class Simulation:
    def __init__(self, config: dict):
        self.config = config

        self.server = None
        self.network_model = NetworkModel()

        self.clients = {}
        self.client_video_map = {}
        self.connections= {}
        self.event_queue = EventQueue()

        self.final_times = {}

        output_log_file = config.get(
            "output_log_file",
            "outputs/logs/simulation_logs.json"
        )
        configured_run_id = config.get("run_id")
        if configured_run_id:
            self.run_id = configured_run_id
        else:
            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            self.run_id = f"run_{timestamp[:-3]}"
        self.run_output_directory = (Path("outputs/runs") / self.run_id)

        self.log_directory = (
            self.run_output_directory / "logs"
            )

        self.metrics_directory = (
            self.run_output_directory / "metrics"
            )           

        self.log_directory.mkdir(
            parents=True,
            exist_ok=True
            )

        self.metrics_directory.mkdir(
            parents=True,
            exist_ok=True
            )       
        combined_log_file = (self.log_directory/ "simulation_logs.json")

        self.logger = SimulationLogger(
            output_file=str(combined_log_file)
        )

        self.metrics_generator = MetricsGenerator(
            input_log_file=str(combined_log_file),
            output_directory=str(
                self.metrics_directory
            )
        )

        print(f"Run ID: {self.run_id}")
        print(
            f"Output folder: "
            f"{self.run_output_directory}"
        )
        

    def setup(self) -> None:
        self._create_server()
        self._load_videos()
        self._create_clients()
        self._create_connection_handler()

    def _create_server(self) -> None:
        server_config = self.config["server"]

        self.server = Server(
            server_id=server_config["server_id"],
            ip_address=server_config["ip_address"],
            port=server_config["port"]
        )

        self.server.start_server()

    def _load_videos(self) -> None:
        for video_config in self.config["videos"]:
            self.server.load_video_segments_from_dataset(
                dataset_path=video_config["dataset_path"],
                video_name=video_config["video_name"],
                segment_duration=video_config["segment_duration"]
            )

            print(
                f"Loaded {video_config['video_name']} from "
                f"{video_config['dataset_path']}"
            )

    def _create_clients(self) -> None:
        for client_config in self.config["clients"]:
            client_id = client_config["client_id"]
            video_name = client_config["video_name"]

            self.clients[client_id] = Client(
                client_id=client_id
            )

            self.client_video_map[client_id] = video_name

            self.network_model.load_client_bandwidth_trace(
                client_id=client_id,
                bandwidth_file_path=client_config["bandwidth_file"]
            )

            print(
                f"Created {client_id}, assigned to {video_name}"
            )

    def _create_connection_handler(self):
        for client_id in self.clients:
            self.connections[client_id] = ConnectionHandler(
            connection_id=f"connection_{client_id}",
            client_socket=None,
            server_socket=self.server.server_socket
            )
    def _schedule_initial_events(self):
        for client_id, client in self.clients.items():
            connection_request = client.create_connection_request_event(
                event_time=0,
                server_id=self.server.server_id
                )
            self.event_queue.add_event(connection_request)

    def run(self):
        self._schedule_initial_events()

        while self.event_queue.has_events():
            event = self.event_queue.get_next_event()
            elapsed_time = self.event_queue.get_elapsed_time()
            self._advance_all_clients(elapsed_time)
            self._dispatch_event(event)
        self._print_summary()
        self._save_logs()
        self._generate_metrics()


    def _print_summary(self) -> None:
        print("\n================================")
        print("SIMULATION COMPLETED")
        print("================================")

        for client_id, client in self.clients.items():
            print("\n------------------------------")
            print(f"Client: {client_id}")
            print(f"Video: {self.client_video_map[client_id]}")
            print(f"Final time: {self.final_times[client_id]:.3f}")
            print(f"Final buffer: {client.buffer_level:.3f}")
            print(
                f"Playback position: "
                f"{client.playback_position_sec:.3f}"
            )
            print(
                f"Quality switches: "
                f"{client.quality_switch_count}"
            )
            print(
                f"Rebuffer time: "
                f"{client.total_rebuffer_time_sec:.3f}"
            )
            print(
                f"Measured bandwidth history: "
                f"{client.bandwidth_history}"
            )

    def _save_logs(self) -> None:

        self.logger.save(
            run_id=self.run_id,
            clients=self.clients,
            server=self.server,
            connections=self.connections,
            event_queue=self.event_queue,
            final_times=self.final_times
        )
    def _generate_metrics(self):
        self.metrics_generator.generate()

    def _advance_all_clients(self, elapsed_time):
        current_time_sec = (self.event_queue.current_time_sec)

        for client in self.clients.values():
            client.consume_video(
                playback_time=elapsed_time,
                current_time_sec=current_time_sec
            )
    def _dispatch_event(self, event):
        if event.event_type == "CONNECTION_REQUEST":
            self._handle_connection_request(event)

        elif event.event_type == "CONNECTION_ESTABLISHED":
            self._handle_connection_established(event)

        elif event.event_type == "MPD_REQUEST":
            self._handle_mpd_request(event)

        elif event.event_type == "MPD_RESPONSE":
            self._handle_mpd_response(event)

        elif event.event_type == "SEGMENT_REQUEST":
            self._handle_segment_request(event)

        elif event.event_type == "SEGMENT_RECEIVED":
            self._handle_segment_received(event)

        else:
            raise ValueError(
            f"Unknown event type: {event.event_type}"
        )

    def _handle_connection_request(self, event):
        connection = self.connections[event.client_id]
        connection.send_request_to_server(event)
        response_event = self.server.handle_connection_request_event(event)
        self.event_queue.add_event(response_event)

    def _handle_connection_established(self, event):

        client = self.clients[event.client_id]
        connection = self.connections[event.client_id]
        connection.send_response_to_client(event)
        connection.mark_connected()
        client.handle_connection_established_event(event)
        video_name = self.client_video_map[event.client_id]
        mpd_request = client.create_mpd_request_event(
            event_time=event.event_time + 0.1,
            server_id=self.server.server_id,
            video_name=video_name)

        self.event_queue.add_event(mpd_request)
    def _handle_mpd_request(self, event):

        connection = self.connections[event.client_id]
        connection.send_request_to_server(event)

        response_event = self.server.handle_mpd_request_event(
            event
        )

        self.event_queue.add_event(response_event)
    def _handle_mpd_response(self, event):
        client = self.clients[event.client_id]
        connection = self.connections[event.client_id]

        connection.send_response_to_client(event)
        client.handle_mpd_response_event(event)
        first_segment_request = client.create_segment_request_event(
            event_time=event.event_time + 0.1,
            server_id=self.server.server_id,
            segment_id=1
        )
        self.event_queue.add_event(first_segment_request)

    def _handle_segment_request(self, event):
        connection = self.connections[event.client_id]
        connection.send_request_to_server(event)
        response_event = self.server.handle_segment_request_event(
            request_event=event,
            network_model=self.network_model
        )

        self.event_queue.add_event(response_event)
    
    def _handle_segment_received(self, event):
        client = self.clients[event.client_id]
        connection = self.connections[event.client_id]

        connection.send_response_to_client(event)

        client.handle_segment_received_event(event)

        next_segment_id = event.segment_id + 1

        if next_segment_id <= client.total_segments:
            next_request = client.create_segment_request_event(
                event_time=event.event_time,
                server_id=self.server.server_id,
                segment_id=next_segment_id
            )

            self.event_queue.add_event(next_request)
        else:
            self.final_times[event.client_id] = event.event_time