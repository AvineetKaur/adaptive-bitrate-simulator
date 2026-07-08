from src.events.segment_request_event import SegmentRequestEvent
from src.events.connection_request_event import ConnectionRequestEvent
from src.socket_model import Socket
from src.events.mpd_request_event import MPDRequestEvent

class Client:
    def __init__(self, client_id):
        self.client_id=client_id

        self.client_socket=Socket(
            owner_id=client_id,
            ip_address="127.0.0.1",
            port=None

        )

        #ABR variables
        self.bandwidth_history=[]
        self.abr_decision_logs = []
        self.throughput_history=[]

        # ABR configuration
        self.low_buffer_threshold = 4
        self.high_buffer_threshold = 12
        self.safety_factor = 0.8


        #connection variables
        self.connected_to_server=False

        # MPD / video metadata
        self.video_name = None
        self.available_qualities = []
        self.segment_duration = None
        self.total_segments = 0
        self.next_segment_id = 1
        
        
        # Playback state
        self.playback_position_sec = 0
        self.playback_started=False

        # Bandwidth estimation state
        self.last_measured_bandwidth_kbps = None

        # QoE tracking
        self.total_rebuffer_time_sec = 0
        self.quality_switch_count = 0
        self.last_selected_bitrate_kbps = None

        # Client logs
        self.logs = []

        # buffer values
        self.max_buffer = 20
        self.buffer_level=0
        self.buffer_threshold=4
        self.buffered_segments = []

    #Check if playback can be started or not
    def can_start_playback(self):
        return self.buffer_level >= self.buffer_threshold
    
    #start playback
    def start_playback(self, current_time):
        if self.playback_started:
            return False
        
        if self.can_start_playback():
            self.playback_started=True
            
            self.logs.append({
                "action": "PLAYBACK_STARTED",
                "current_time": current_time,
                "buffer_level": self.buffer_level
            })
            return True
        
        return False
# select bitrate on the basis of history bandwidth
    def select_bitrate(self):
        estimated_throughput = self.calculate_throughput()
        if estimated_throughput is None:
            selected_bitrate = self.available_qualities[0]

            self.last_selected_bitrate_kbps = selected_bitrate

            self.logs.append({
                "action": "ABR_QUALITY_SELECTED",
                "reason": "NO_BANDWIDTH_HISTORY_START_LOW",
                "selected_quality": selected_bitrate,
                "buffer_level": self.buffer_level
            })

            self.abr_decision_logs.append({
                "reason": "NO_BANDWIDTH_HISTORY_START_LOW",
                "estimated_throughput": None,
                "available_qualities": self.available_qualities,
                "selected_quality": selected_bitrate,
                "buffer_level": self.buffer_level
            })
            return selected_bitrate

        selected_bitrate = self.available_qualities[0]

        for bitrate in self.available_qualities:
            if bitrate <= estimated_throughput:
                selected_bitrate = bitrate

        if self.last_selected_bitrate_kbps is not None:
            if selected_bitrate != self.last_selected_bitrate_kbps:
                self.quality_switch_count += 1

        self.last_selected_bitrate_kbps = selected_bitrate

        self.logs.append({
            "action": "ABR_QUALITY_SELECTED",
            "estimated_throughput": estimated_throughput,
            "available_qualities": self.available_qualities,
            "selected_quality": selected_bitrate,
            "buffer_level": self.buffer_level
        })

        self.abr_decision_logs.append({
            "estimated_throughput": estimated_throughput,
            "available_qualities": self.available_qualities,
            "selected_quality": selected_bitrate,
            "buffer_level": self.buffer_level
        })

        return selected_bitrate   
    
    # select the best bitrate as per the bandwidth
    def select_bitrate_old(self, current_bandwidth):
        if current_bandwidth<=self.available_qualities[0]:
            raise ValueError(
                  "Bandwidth too low."
            ) 
        safe_bandwidth=current_bandwidth*0.8
        for bitrate in self.available_qualities:
            if bitrate<=safe_bandwidth:
                selected_bitrate=bitrate
        
        if self.last_selected_bitrate_kbps is not None:
            if selected_bitrate!=self.last_selected_bitrate_kbps:
                self.quality_switch_count+=1

        self.last_selected_bitrate_kbps = selected_bitrate
        
        self.logs.append({
            "action":"BITRATE_SELECTED",
            "safe_bandwidth_kbps": safe_bandwidth,
            "selected_bitrate_kbps": selected_bitrate
        })

        return selected_bitrate
    
    #This will calculate the throughput

    def get_average_previous_bandwidth(self, window_size=3):
        if not self.bandwidth_history:
            return None

        recent_bandwidths = self.bandwidth_history[-window_size:]
        average_bandwidth = sum(recent_bandwidths) / len(recent_bandwidths)

        return average_bandwidth


    def calculate_throughput(self):
        average_previous_bandwidth = self.get_average_previous_bandwidth(window_size=3)

        if average_previous_bandwidth is None:
            self.logs.append({
                "action": "THROUGHPUT_ESTIMATION",
                "reason": "NO_PREVIOUS_BANDWIDTH",
                "estimated_throughput": None,
                "buffer_level": self.buffer_level
            })

            return None

        estimated_throughput = average_previous_bandwidth * self.safety_factor
        buffer_state = "MEDIUM"

        if self.buffer_level < self.low_buffer_threshold:
            estimated_throughput = estimated_throughput * 0.7
            buffer_state = "LOW"

        elif self.buffer_level > self.high_buffer_threshold:
            estimated_throughput = estimated_throughput * 1.1
            buffer_state = "HIGH"

        self.throughput_history.append(estimated_throughput)

        self.logs.append({
            "action": "THROUGHPUT_ESTIMATION",
            "average_previous_bandwidth": average_previous_bandwidth,
            "safety_factor": self.safety_factor,
            "buffer_level": self.buffer_level,
            "buffer_state": buffer_state,
            "estimated_throughput": estimated_throughput
        })

        return estimated_throughput
    #add segment to buffer
    #client will hold sending event request if the buffer level is full.

    def add_to_buffer(self,segment_id,segment_duration):
        if self.buffer_level+ segment_duration > self.max_buffer:
            raise ValueError(
                f"Cannot add segment {segment_id}. "
                f"Buffer limit exceeded."
                f"segment duration is {segment_duration} sec, "
                f"max buffer is {self.max_buffer} sec."
            )
        self.buffered_segments.append({
        "segment_id": segment_id,
        "remaining_duration_sec": segment_duration
        })
        self.buffer_level += segment_duration
        self.logs.append({
            "action": "SEGMENT_ADDED_TO_BUFFER",
            "segment_id": segment_id,
            "segment_duration_sec": segment_duration,
            "buffer_level_sec": self.buffer_level,
            "max_buffer_sec": self.max_buffer,
            "buffered_segments": self.buffered_segments.copy()
        })

    def consume_video(self, playback_time):
        if not self.playback_started:
            return 0

        remaining_time = playback_time
        rebuffer_time = 0

        while remaining_time > 0:
            if len(self.buffered_segments) == 0:
                rebuffer_time = remaining_time
                self.total_rebuffer_time_sec += rebuffer_time
                self.buffer_level = 0
                return rebuffer_time

            current_segment = self.buffered_segments[0]
            segment_time = current_segment["remaining_duration_sec"]

            if remaining_time < segment_time:
                current_segment["remaining_duration_sec"] = segment_time - remaining_time
                self.buffer_level -= remaining_time
                self.playback_position_sec += remaining_time
                remaining_time = 0

            else:   
                remaining_time -= segment_time
                self.buffer_level -= segment_time
                self.playback_position_sec += segment_time
                self.buffered_segments.pop(0)

        return rebuffer_time   
  
    #create segment request for server
    def create_segment_request_event (self,event_time,server_id,segment_id,current_bandwidth):
        selected_quality=self.select_bitrate()
        deadline_time = event_time + self.buffer_level


        request_event=SegmentRequestEvent(
            event_time=event_time,
            client_id=self.client_id,
            server_id=server_id,
            video_name=self.video_name,
            segment_id=segment_id,
            segment_quality=selected_quality,
            deadline_time=deadline_time
        )
        self.logs.append({
            "action": "SEGMENT_REQUEST_CREATED",
            "event_time": event_time,
            "server_id": server_id,
            "client_id": self.client_id,
            "video_name": self.video_name,
            "segment_id": segment_id,
            "segment_quality": selected_quality,
            "deadline_time": deadline_time
        })
        return request_event
    
    #handle segment received from server
    def handle_segment_received_event(self, segment_event):
        measured_bandwidth_kbps = (segment_event.segment_size / segment_event.download_time)

        self.last_measured_bandwidth_kbps = measured_bandwidth_kbps
        self.bandwidth_history.append(measured_bandwidth_kbps)

        self.add_to_buffer(segment_id=segment_event.segment_id,
                           segment_duration=segment_event.segment_duration)
        self.start_playback(segment_event.event_time)
        self.logs.append({
            "action": "SEGMENT_RECEIVED_HANDLED",
            "segment_id": segment_event.segment_id,
            "bitrate_kbps": segment_event.segment_quality,
            "file_size_kbits": segment_event.segment_size,
            "download_time_sec": segment_event.download_time,
            "measured_bandwidth_kbps": self.last_measured_bandwidth_kbps,
            "buffer_level": self.buffer_level,
            "playback_started": self.playback_started
    })
    
    #connection request to server
    def create_connection_request_event(self, event_time, server_id):
        connection_event=ConnectionRequestEvent(
          event_time=event_time,
          server_id=server_id
      )
        self.logs.append({
            "action": "CONNECTION_REQUEST_CREATED",
            "event_time": event_time,
            "client_id": self.client_id,
            "server_id": server_id
        })
        return connection_event
    
    #handle connection acccepted 
    def handle_connection_established_event(self, event):
        self.connected_to_server = True

        self.logs.append({
            "action": "CONNECTION_ESTABLISHED",
            "event_time": event.event_time,
            "client_id": self.client_id,
            "server_id": event.server_id
        })
    
    #create mpd request to server
    def create_mpd_request_event(self, event_time, server_id, video_name):
        if not self.connected_to_server:
            raise Exception("Client is not connected to server.")

        event = MPDRequestEvent(
            event_time=event_time,
            client_id=self.client_id,
            server_id=server_id,
            video_name=video_name
        )

        self.logs.append({
            "action": "MPD_REQUEST_CREATED",
            "event_time": event_time,
            "client_id": self.client_id,
            "server_id": server_id,
            "video_name": video_name
        })

        return event
    
    #handle mpd response from server
    def handle_mpd_response_event(self, event):
        self.video_name = event.video_name
        self.available_qualities  = sorted(event.available_qualities)
        self.segment_duration = event.segment_duration
        self.total_segments = event.total_segments

        self.logs.append({
            "action": "MPD_RESPONSE_RECEIVED",
            "event_time": event.event_time,
            "client_id": self.client_id,
            "video_name": self.video_name,
            "available_qualities": self.available_qualities,
            "segment_duration": self.segment_duration,
            "total_segments": self.total_segments
        })



        
      #1. client connect to server(tcp connection)
      #2. after connection established: client request for video information(request for mpd file for a, filename(input variable))
      #take into consideration about the different encodings the mpd file.
      #3. respondse form server mpd file.
      #----loop----(handled through event list)
      # 4. clinet request first segment
      #5. server will psend the segment
      #6. server trigger response SegmentRequestEvent
      #7. calculation of deadline depening on buffer level.
      #8. test for more users.(has its own trace file, vidoe files.)

    #   --------------------------------------------------------------------
    

    # agentic

    # explore library: what are the options, how to build shared memory . crewAI.,
    # autogen, langchain(explore)

    