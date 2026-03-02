# data/interface/simulation_adapter.py
import socketio
import requests
import json
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
from queue import Queue
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .flow_schema import NetworkFlow

class SimulationAdapter:
    def __init__(
        self,
        socket_host: str = "localhost",
        socket_port: int = 8000,
        rest_api_url: str = "http://localhost:8000/api/v1",
        use_https: bool = False,
        api_key: Optional[str] = None,
        verify_ssl: bool = False
    ):
        self.socket_host = socket_host
        self.socket_port = socket_port
        
        self.base_url = rest_api_url
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        
        # REST API headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        # State tracking
        self.current_update_id = 0
        self.last_flow_id = 0
        self.flow_buffer = []
        self.buffer_lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        
        # Socket.IO client
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.socket_connected = False
        
        # Register Socket.IO event handlers
        self._register_socketio_handlers()
        
        # REST API endpoints
        self.endpoints = {
            "attacks": "/attacks",
            "hosts": "/network/nodes",
            "status": "/simulation/state",
            "flows_since": "/network/flows"
        }
        
        # Control flags
        self.running = False
        self.update_thread = None
        
        # Queue for commands (if needed)
        self.command_queue = Queue()
    
    def _register_socketio_handlers(self):
        """Register all Socket.IO event handlers"""
        
        @self.sio.event
        def connect():
            self.logger.info("✅ Socket.IO connected to simulation")
            self.socket_connected = True
        
        @self.sio.event
        def disconnect():
            self.logger.info("🔌 Socket.IO disconnected from simulation")
            self.socket_connected = False
        
        @self.sio.on('connected')
        def on_connected(data):
            self.logger.info(f"Simulation confirmed connection: {data}")
        
        @self.sio.on('error')
        def on_error(message):
            self.logger.error(f"Socket.IO error from simulation: {message}")
    
    def connect(self) -> bool:
        self.logger.info("Connecting to simulation backend...")
        
        # 1. Check REST API
        try:
            resp = requests.get(
                f"{self.base_url}{self.endpoints['status']}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            if resp.status_code == 200:
                self.logger.info("✅ REST API reachable")
                self.logger.debug(f"Status response: {resp.json()}")
            else:
                self.logger.warning(f"⚠️ REST API returned status {resp.status_code}")
        except Exception as e:
            self.logger.error(f"❌ REST API connection failed: {e}")
            raise ConnectionError(f"Cannot connect to REST API: {e}")
        
        # 2. Connect Socket.IO
        scheme = "https" if self.base_url.startswith("https") else "http"
        ws_url = f"{scheme}://{self.socket_host}:{self.socket_port}"
        
        try:
            self.logger.info(f"Connecting Socket.IO to {ws_url}...")
            self.sio.connect(
                ws_url,
                headers=self.headers,
                transports=['websocket'],  # Force websocket transport
                wait_timeout=10
            )
            self.logger.info("✅ Socket.IO connected")
            self.socket_connected = True
        except Exception as e:
            self.logger.error(f"❌ Socket.IO connection failed: {e}")
            raise ConnectionError(f"Cannot connect to Socket.IO: {e}")

        # 3. Start simulation if not already running
        simulation_state = self.get_simulation_status()
        if not simulation_state.get('state', 'paused').lower() == 'running':
            self.logger.info("Starting simulation...")
            resp = requests.post(
                f"{self.base_url}/simulation/control",
                headers=self.headers,
                json={"action": "start"},
                verify=self.verify_ssl,
                timeout=5
            )

            if resp.status_code == 200:
                self.logger.info("✅ Simulation started")
            else:
                self.logger.warning(f"⚠️ Failed to start simulation: {resp.status_code} - {resp.text}")
        
        
        # 4. Start background update thread (optional - can also rely on real-time updates)
        self.running = True
        self.update_thread = threading.Thread(target=self._background_update_loop, daemon=True)
        self.update_thread.start()
        self.logger.info("✅ Background thread started")
        
        return True
    
    def disconnect(self):
        """Disconnect from simulation backend"""
        self.logger.info("Disconnecting from simulation...")
        
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        
        if self.sio.connected:
            self.sio.disconnect()
        
        self.socket_connected = False
        self.logger.info("✅ Disconnected from simulation")
    
    def request_update(self) -> bool:
        if not self.socket_connected:
            self.logger.error("Cannot request update: Socket not connected")
            return False
        
        try:
            # Emit the event (matches your backend handler)
            self.sio.emit('request_update', {'timedelta': 0.5})
            self.logger.debug(f"Sent request_update")
            
            # Increment update counter
            self.current_update_id += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send request_update: {e}")
            return False
    
    def _background_update_loop(self):
        while self.running:
            try:
                if self.socket_connected:
                    # Send update request
                    self.request_update()
                
                time.sleep(0.5) 
                
            except Exception as e:
                self.logger.error(f"Error in background update loop: {e}")
                time.sleep(5)
    
    def _fetch_flows(self) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['flows_since']}",
                params={"last_id": self.last_flow_id, "limit": 1000},
                headers=self.headers,
                verify=self.verify_ssl,
            )

            if response.status_code == 200:
                flows_data = response.json()
                
                for flow_data in flows_data:
                    flow = self._parse_flow(flow_data)
                    if flow:
                        self.flow_buffer.append(flow)
                        flow_id = flow_data.get('id', 0)
                        if flow_id > self.last_flow_id:
                            self.last_flow_id = flow_id
                
                self.logger.debug(f"REST fetch: got {len(flows_data)} flows")
                return flows_data
            
        except requests.RequestException as e:
            self.logger.error(f"REST API error fetching flows: {e}")
        
        return []
    
    def _parse_flow(self, flow_data: Dict) -> Optional[NetworkFlow]:
        """
        Parse raw flow data from API/WebSocket into NetworkFlow object
        """
        try:
            # Attack type to label mapping
            attack_mapping = {
                "normal": 0,
                "port_scan": 1,
                "ddos": 2,
                "malware_spread": 3,
                "arp_spoofing": 4,
                "sql_injection": 5,
                "brute_force": 6,
                "xss": 7,
                "csrf": 8,
                "zero_day": 9,
                None: 0,
                "": 0
            }
            
            # Parse timestamp
            timestamp = flow_data.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        # Fallback to current time if parsing fails
                        timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Determine attack label
            attack_type = flow_data.get('attack_type', 'normal')
            label = attack_mapping.get(attack_type.lower() if attack_type else "normal", 0)
            
            # Handle different field name variations
            src_ip = flow_data.get('src_ip') or flow_data.get('source_ip') or '0.0.0.0'
            dst_ip = flow_data.get('dst_ip') or flow_data.get('dest_ip') or '0.0.0.0'
            src_port = flow_data.get('src_port') or flow_data.get('source_port') or 0
            dst_port = flow_data.get('dst_port') or flow_data.get('dest_port') or 0
            
            # Handle bytes_sent field
            bytes_sent = flow_data.get('bytes_sent')
            if bytes_sent is None:
                bytes_sent = flow_data.get('bytes', 0)
            
            # Handle packets_sent field
            packets_sent = flow_data.get('packets_sent')
            if packets_sent is None:
                packets_sent = flow_data.get('packets', 0)
            
            # Create NetworkFlow object
            flow = NetworkFlow(
                id=flow_data.get('id', 0),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=int(src_port),
                dst_port=int(dst_port),
                protocol=flow_data.get('protocol', 'unknown').upper(),
                bytes_sent=int(bytes_sent),
                packets_sent=int(packets_sent),
                duration=float(flow_data.get('duration', 0.0)),
                timestamp=timestamp,
                label=label,
                # Optional fields
                pattern=flow_data.get('pattern', 'unknown').lower(),
                tcp_state=flow_data.get('tcp_state'),
                qos_class=flow_data.get('qos_class'),
                dscp=int(flow_data.get('dscp', 0))
            )
            
            return flow
            
        except Exception as e:
            self.logger.error(f"Error parsing flow data: {e}, data: {flow_data}")
            return None
    
    def get_flows(self, window_seconds: int = 5) -> List[NetworkFlow]:
        """
        Get flows from the last `window_seconds` seconds
        
        This method is called by the training pipeline to get recent flows
        """
        with self.buffer_lock:
            if not self.flow_buffer:
                self._fetch_flows()
                
                if not self.flow_buffer:
                    return []
            
            current_time = time.time()
            window_start = current_time - window_seconds
            
            recent_flows = []
            remaining_flows = []
            
            for flow in self.flow_buffer:
                flow_time = flow.timestamp.timestamp()
                
                if flow_time >= window_start:
                    recent_flows.append(flow)
                    remaining_flows.append(flow)  # Keep for future windows
                # Flows older than window are discarded
            
            self.flow_buffer = remaining_flows
            
            return recent_flows
    
    def get_attack_labels(self, flows: List[NetworkFlow]) -> List[int]:
        """Get labels for a list of flows"""
        return [flow.label for flow in flows]
    
    def force_update(self) -> bool:
        """
        Force an immediate update request
        """
        return self.request_update({'force': True, 'since_id': self.last_flow_id})
    
    def get_attack_info(self) -> Dict:
        """Get current attack information from REST API"""
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['attacks']}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching attack info: {e}")
        
        return {}
    
    def get_host_metrics(self) -> Dict:
        """Get host metrics from REST API"""
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['hosts']}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching host metrics: {e}")
        
        return {}
    
    def get_simulation_status(self) -> Dict:
        """Get simulation status from REST API"""
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['status']}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching status: {e}")
        
        return {}
    
    def send_command(self, command: str, params: Dict = None) -> bool:
        if not self.socket_connected or not self.sio.connected:
            self.logger.error("Cannot send command: Socket not connected")
            return False
        
        try:
            command_data = {
                'command': command,
                'params': params or {},
                'timestamp': datetime.now().isoformat()
            }
            
            # You can define custom event names for different commands
            self.sio.emit(command, command_data)
            self.logger.debug(f"Sent command: {command}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send command {command}: {e}")
            return False
        print