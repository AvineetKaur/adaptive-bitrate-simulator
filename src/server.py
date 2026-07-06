#The server stores video metadata and creates MPD/segment responses.

import csv
from src.socket_model import Socket
from src.events.segment_received_event import SegmentReceivedEvent
from src.events.connection_established_event import ConnectionEstablishedEvent
from src.events.mpd_response_event import MPDResponseEvent

class Server:
    def __init__(self, server_id, ip_address, port):
        self.server_id = server_id
        self.ip_address = ip_address
        self.port = port

        #socket added here
        self.server_socket = Socket(
            owner_id=server_id,
            ip_address=ip_address,
            port=port
        )
        #connected clients
        self.connected_clients=[]

        self.video_segments = {}
        self.video_catalog = {}

        #specify bitrate for different quality
        self.quality_to_bitrate={
            "QualityRate1":800,
            "QualityRate2":1400,
            "QualityRate3":2800
        }

        self.logs = []

    def start_server(self):
        self.server_socket.open()
        print(f"Server {self.server_id} started and listening")

    def load_video_segments_from_dataset(self, dataset_path,video_name,segment_duration=4):
        self.video_segments[video_name]={}
        
        with open(dataset_path, "r") as file:
            reader = csv.DictReader(file)

            for row in reader:
                if not row["segment_id"]:
                    continue

                segment_id = int(row["segment_id"])
                file_name = row["Filename"]

                if segment_id not in self.video_segments[video_name]:
                    self.video_segments[video_name][segment_id] = {}


                for quality_rate, bitrate_kbps in self.quality_to_bitrate.items():
                    size_column = quality_rate + "_size"

                    self.video_segments[video_name][segment_id][bitrate_kbps] = {
                        "segment_id": segment_id,
                        "quality_rate": quality_rate,
                        "bitrate_kbps": bitrate_kbps,
                        "duration_sec": segment_duration,
                        "file_size_kbits": float(row[size_column]),
                        "file_name": file_name
                    }

        
        self.create_video_catalog_entry(
            video_name=video_name,
            segment_duration=segment_duration
        )
        print("Video segments loaded from dataset")
   
    # def load_bandwidth_trace(self, bandwidth_file_path):
    #     with open(bandwidth_file_path, "r") as file:
    #         reader = csv.DictReader(file)
    #         for row in reader:
    #             time_sec = int(row["time_sec"])
    #             bandwidth_kbps = float(row["bandwidth_kbps"])
    #             self.bandwidth_trace[time_sec] = bandwidth_kbps         
    #     print("Bandwidth trace loaded from file")

    def create_video_catalog_entry(self, video_name, segment_duration):

        total_segments = len(self.video_segments[video_name])

        self.video_catalog[video_name] = {
            "available_bitrates": list(self.quality_to_bitrate.values()),
            "segment_duration_sec": segment_duration,
            "total_segments": total_segments
        }

    def handle_connection_request_event(self, request_event):
        client_id=request_event.client_id

        if request_event.server_id != self.server_id:
            raise ValueError(
                f"Connection request intended for {request_event.server_id}, "
                f"but this server is {self.server_id}"
            )
        
        if client_id not in self.connected_clients:
            self.connected_clients.append(client_id)

        response_event=ConnectionEstablishedEvent(
            event_time=request_event.event_time,
            client_id=request_event.client_id,
            server_id=self.server_id
        )

        self.logs.append({
            "action": "CONNECTION_REQUEST_HANDLED",
            "event_time": request_event.event_time,
            "client_id": request_event.client_id,
            "server_id": request_event.server_id,
        })

        return response_event

    def handle_segment_request_event(self, request_event,network_model):
        current_time = request_event.event_time
        client_id = request_event.client_id
        segment_id = request_event.segment_id
        segment_quality = request_event.segment_quality
        video_name = request_event.video_name

        if video_name not in self.video_segments:
             raise ValueError(f"Segment {segment_id} not found.")

        if segment_id not in self.video_segments[video_name]:
             raise ValueError(f"Segment {segment_id} not found.")

        if segment_quality not in self.video_segments[video_name][segment_id]:
            raise ValueError(f"Segment quality {segment_quality} not available for segment {segment_id}")

        

        segment = self.video_segments[video_name][segment_id][segment_quality]

        segment_size = segment["file_size_kbits"]
        segment_duration=segment['duration_sec']
    
        download_result = network_model.calculate_download_time(
            file_size_kbits=segment_size,
            start_time=current_time,
            client_id=client_id
        )

        download_time = download_result["download_time_sec"]
        file_received_time = download_result["file_received_time"]
        

        response_event = SegmentReceivedEvent(
            event_time=file_received_time,
            client_id= client_id,
            server_id =self.server_id,
            segment_id=segment_id,
            segment_quality=segment_quality,
            segment_size=segment_size,
            segment_duration=segment_duration,
            download_time=download_time,
            video_name=video_name,
            request_time=current_time,
            deadline_time=request_event.deadline_time
        )
        
        

        self.logs.append({
            "action": "SEGMENT_REQUEST_HANDLED",
            "request_time": current_time,
            "client_id": client_id,
            "segment_id": segment_id,
            "segment_quality": segment_quality,
            "segment_size": segment_size,
            "download_time_sec": download_time,
            "file_received_time": file_received_time
        })

        return response_event
        
    
    def handle_mpd_request_event(self, event):
        client_id = event.client_id
        video_name = event.video_name

        if video_name not in self.video_catalog:
            raise Exception(f"Video {video_name} not found in server catalog.")

        video_metadata = self.video_catalog[video_name]

        response_event = MPDResponseEvent(
            event_time=event.event_time,
            server_id=self.server_id,
            client_id=client_id,
            video_name=video_name,
            available_qualities=video_metadata["available_bitrates"],
            segment_duration=video_metadata["segment_duration_sec"],
            total_segments=video_metadata["total_segments"]
        )
        self.logs.append({
            "action": "MPD_RESPONSE_CREATED",
            "event_time": event.event_time,
            "client_id": client_id,
            "video_name": video_name
        })

        return response_event


    # def calculate_realistic_download_time(self, file_size_kbits, start_time_sec):
    #     # client idshould be there
    #     remaining_file_size = file_size_kbits
    #     current_time = start_time_sec
    #     while remaining_file_size > 0:
    #         current_second = int(current_time)
    #         if current_second not in self.bandwidth_trace:
    #             raise Exception(f"No bandwidth data available for time {current_second}")
            
    #         bandwidth_kbps = self.bandwidth_trace[current_second]
    #         next_second = current_second + 1
    #         available_time_in_current_second = next_second - current_time
    #         downloadable_kbits = bandwidth_kbps * available_time_in_current_second
            
    #         if downloadable_kbits >= remaining_file_size:
    #             time_needed = remaining_file_size / bandwidth_kbps
    #             file_received_time = current_time + time_needed
    #             download_time_sec = file_received_time - start_time_sec
    #             return {
    #                 "download_time_sec": download_time_sec,
    #                 "file_received_time": file_received_time
    #             }
    #         remaining_file_size = remaining_file_size - downloadable_kbits
    #         current_time = next_second