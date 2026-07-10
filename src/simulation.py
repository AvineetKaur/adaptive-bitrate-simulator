from src.client import Client
from src.server import Server
from src.network_model import NetworkModel
from src.connection_handler import ConnectionHandler
from src.event_queue import EventQueue
from src.simulation_logger import SimulationLogger
from src.metrics_generator import MetricsGenerator


class Simulation:
    def __init__(self, config: dict):
        self.config = config

        self.server = None
        self.network_model = NetworkModel()

        self.clients = {}
        self.client_video_map = {}
        self.connection = None
        self.final_times = {}

        output_log_file = config.get(
            "output_log_file",
            "outputs/logs/simulation_logs.json"
        )

        self.logger = SimulationLogger(
            output_file=output_log_file
        )
        output_metrics_directory = config.get(
            "output_metrics_directory",
            "outputs/metrics")

        self.metrics_generator = MetricsGenerator(
            input_log_file=output_log_file,
            output_directory=output_metrics_directory)
        

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

    def _create_connection_handler(self) -> None:
        self.connection = ConnectionHandler(
            connection_id="shared_connection",
            client_socket=None,
            server_socket=self.server.server_socket
        )

    def run(self) -> None:
        for client_id, client in self.clients.items():
            video_name = self.client_video_map[client_id]

            print("\n================================")
            print(f"Running client: {client_id}")
            print(f"Watching video: {video_name}")
            print("================================")

            final_time = self._run_client_flow(
                client=client,
                video_name=video_name
            )

            self.final_times[client_id] = final_time

        self._print_summary()
        self._save_logs()
        self._generate_metrics()

    def _run_client_flow(
        self,
        client: Client,
        video_name: str
    ) -> float:
        event_queue = EventQueue()

        # 1. Connection flow
        self.connection.establish_connection(
            client=client,
            server=self.server,
            event_time=0,
            server_id=self.server.server_id
        )

        # 2. MPD flow
        mpd_request = client.create_mpd_request_event(
            event_time=0.1,
            server_id=self.server.server_id,
            video_name=video_name
        )

        self.connection.send_request_to_server(
            mpd_request
        )

        mpd_response = self.server.handle_mpd_request_event(
            mpd_request
        )

        self.connection.send_response_to_client(
            mpd_response
        )

        client.handle_mpd_response_event(
            mpd_response
        )

        # 3. Segment flow
        current_time = 0.2

        for segment_id in range(
            1,
            client.total_segments + 1
        ):
            print(
                f"\n{client.client_id} requesting "
                f"{video_name}, segment {segment_id}"
            )

            segment_request = client.create_segment_request_event(
                event_time=current_time,
                server_id=self.server.server_id,
                segment_id=segment_id
            )

            self.connection.send_request_to_server(
                segment_request
            )

            segment_response = (
                self.server.handle_segment_request_event(
                    request_event=segment_request,
                    network_model=self.network_model
                )
            )

            event_queue.add_event(
                segment_response
            )

            while event_queue.has_events():
                event = event_queue.get_next_event()

                elapsed_time = event_queue.get_elapsed_time()

                client.consume_video(
                    elapsed_time
                )

                if event.event_type == "SEGMENT_RECEIVED":
                    self.connection.send_response_to_client(
                        event
                    )

                    client.handle_segment_received_event(
                        event
                    )

                    print(
                        f"Segment {event.segment_id} received | "
                        f"quality={event.segment_quality} | "
                        f"arrival={event.event_time:.3f} | "
                        f"buffer={client.buffer_level:.3f}"
                    )

            current_time = event_queue.current_time_sec

        return event_queue.current_time_sec

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
            clients=self.clients,
            server=self.server,
            connection=self.connection,
            final_times=self.final_times
        )
    def _generate_metrics(self):
        self.metrics_generator.generate()