from pprint import pprint
from src.server import Server

server = Server(
    server_id="server_1",
    ip_address="127.0.0.1",
    port=5000
)

server.start_server()

server.load_video_segments_from_dataset(
    dataset_path="data/videos/video_1_segments.csv",
    video_name="video_1",
    segment_duration=4
)

print("\nVideo catalog:")
pprint(server.video_catalog)

print("\nSegment 1 at 800 kbps:")
pprint(server.video_segments["video_1"][1][800])

print("\nServer logs:")
pprint(server.logs)