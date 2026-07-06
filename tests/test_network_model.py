import sys
from pathlib import Path
from pprint import pprint

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.network_model import NetworkModel


network_model = NetworkModel()

network_model.load_client_bandwidth_trace(
    client_id="client_1",
    bandwidth_file_path="data/bandwidth_dataset.csv"
)

bandwidth = network_model.get_bandwidth_at_time(
    client_id="client_1",
    current_time=0.2
)

print("Bandwidth at 0.2 sec:", bandwidth)

download_result = network_model.calculate_download_time(
    client_id="client_1",
    file_size_kbits=700,
    start_time=0.2
)

print("\nDownload result:")
pprint(download_result)