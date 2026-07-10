import json
from pathlib import Path


def load_config(config_path):
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Simulation configuration file not found: {config_file}"
        )

    with open(config_file, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config


def validate_config(config):
    required_sections = [
        "server",
        "videos",
        "clients"
    ]

    for section in required_sections:
        if section not in config:
            raise ValueError(
                f"Missing required configuration section: {section}"
            )

    server_config = config["server"]

    required_server_fields = [
        "server_id",
        "ip_address",
        "port"
    ]

    for field in required_server_fields:
        if field not in server_config:
            raise ValueError(
                f"Server configuration is missing field: {field}"
            )

    available_videos = set()
    video_names = set()

    for video in config["videos"]:
        required_video_fields = [
            "video_name",
            "dataset_path",
            "segment_duration"
        ]

        for field in required_video_fields:
            if field not in video:
                raise ValueError(
                    f"Video configuration is missing field: {field}"
                )

        video_name = video["video_name"]

        if video_name in video_names:
            raise ValueError(
                f"Duplicate video name found: {video_name}"
            )

        video_names.add(video_name)
        available_videos.add(video_name)

        video_path = Path(video["dataset_path"])

        if not video_path.exists():
            raise FileNotFoundError(
                f"Video dataset not found: {video_path}"
            )

        if video["segment_duration"] <= 0:
            raise ValueError(
                f"Segment duration must be greater than zero for {video_name}"
            )

    client_ids = set()

    for client in config["clients"]:
        required_client_fields = [
            "client_id",
            "video_name",
            "bandwidth_file"
        ]

        for field in required_client_fields:
            if field not in client:
                raise ValueError(
                    f"Client configuration is missing field: {field}"
                )

        client_id = client["client_id"]

        if client_id in client_ids:
            raise ValueError(
                f"Duplicate client ID found: {client_id}"
            )

        client_ids.add(client_id)

        bandwidth_path = Path(
            client["bandwidth_file"]
        )

        if not bandwidth_path.exists():
            raise FileNotFoundError(
                f"Bandwidth dataset not found: {bandwidth_path}"
            )

        if client["video_name"] not in available_videos:
            raise ValueError(
                f"{client_id} is assigned to unknown video "
                f"{client['video_name']}"
            )

    print("Configuration validated successfully.")