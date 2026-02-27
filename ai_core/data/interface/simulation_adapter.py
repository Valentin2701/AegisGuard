# data/interface/simulation_adapter.py
import socket
import requests
import json
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
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
        self.socket = None
        self.socket_connected = False
        
        self.base_url = rest_api_url
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        self.current_update_id = 0
        self.last_flow_id = 0
        self.flow_buffer = []
        self.buffer_lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        
        self.running = False
        self.update_thread = None
        
        self.endpoints = {
            "attacks": "/attacks",
            "hosts": "/network/nodes",
            "status": "/network/status",
            "flows_since": "/network/flows"
        }
    
    def connect(self):
        self.logger.info("Connecting to simulation...")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.socket_host, self.socket_port))
            self.socket_connected = True
            self.logger.info(f"✅ Socket connected to {self.socket_host}:{self.socket_port}")
        except Exception as e:
            self.logger.error(f"❌ Socket connection failed: {e}")
            raise ConnectionError(f"Cannot connect to simulation socket: {e}")
        
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['status']}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            if response.status_code == 200:
                self.logger.info(f"✅ REST API connected to {self.base_url}")
                self.logger.info(f"Simulation status: {response.json()}")
            else:
                self.logger.warning(f"⚠️ REST API returned status {response.status_code}")
        except Exception as e:
            self.logger.error(f"❌ REST API connection failed: {e}")
            raise ConnectionError(f"Cannot connect to simulation REST API: {e}")
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self.logger.info("✅ Background update thread started")
        
        return True
    
    def disconnect(self):
        self.logger.info("Disconnecting from simulation...")
        
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        
        if self.socket:
            self.socket.close()
            self.socket_connected = False
        
        self.logger.info("✅ Disconnected from simulation")
    
    def _update_loop(self):
        while self.running:
            try:
                if self.socket_connected:
                    self.socket.sendall(b"request_update\n")
                    
                    response = self.socket.recv(1024).decode().strip()
                    self.logger.debug(f"Update response: {response}")
                    
                    self.current_update_id += 1
                    
                    time.sleep(0.5)
                    
                    self._fetch_new_flows()
                
            except socket.error as e:
                self.logger.error(f"Socket error in update loop: {e}")
                self._reconnect_socket()
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
            
            time.sleep(0.5)
    
    def _reconnect_socket(self):
        try:
            self.logger.info("Attempting to reconnect socket...")
            self.socket.close()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.socket_host, self.socket_port))
            self.socket_connected = True
            self.logger.info("✅ Socket reconnected")
        except Exception as e:
            self.logger.error(f"❌ Socket reconnection failed: {e}")
            self.socket_connected = False
            time.sleep(5)
    
    def _fetch_new_flows(self):
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['flows_since']}",
                params={"last_id": self.last_flow_id},
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            
            if response.status_code == 200:
                flows_data = response.json()
                
                with self.buffer_lock:
                    for flow_data in flows_data:
                        flow = self._parse_flow(flow_data)
                        if flow:
                            self.flow_buffer.append(flow)
                            
                            flow_id = flow_data.get('id', 0)
                            self.last_flow_id = flow_id
                
                self.logger.debug(f"Fetched {len(flows_data)} new flows")
            
        except requests.RequestException as e:
            self.logger.error(f"REST API error fetching flows: {e}")
    
    def _parse_flow(self, flow_data: Dict) -> Optional[NetworkFlow]:
        """
        Parses raw flow data from the API into a NetworkFlow object
        """
        try:
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
            
            timestamp = flow_data.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            attack_type = flow_data.get('attack_type', 'normal')
            label = attack_mapping.get(attack_type.lower() if attack_type else "normal", 0)
            
            flow = NetworkFlow(
                id=flow_data.get('id'),
                source_ip=flow_data.get('src_ip'),
                dest_ip=flow_data.get('dst_ip'),
                source_port=int(flow_data.get('src_port', 0)),
                dest_port=int(flow_data.get('dst_port', 0)),
                protocol=flow_data.get('protocol', 'unknown').upper(),
                pattern=flow_data.get('pattern', 'unknown').lower(),
                tcp_state=flow_data.get('tcp_state'),
                bytes_sent=int(flow_data.get('bytes_sent', flow_data.get('bytes_sent', 0))),
                qos_class=flow_data.get('qos_class'),
                dscp=int(flow_data.get('dscp', 0)),
                packets_sent=int(flow_data.get('packets_sent')),
                duration=float(flow_data.get('duration', 0.0)),
                timestamp=timestamp,
                label=label,
            )
            
            return flow
            
        except Exception as e:
            self.logger.error(f"Error parsing flow data: {e}, data: {flow_data}")
            return None
    
    def get_flows(self, window_seconds: int = 5) -> List[NetworkFlow]:
        """
        Returns flows from the buffer that are within the last `window_seconds` seconds
        """
        with self.buffer_lock:
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
                    remaining_flows.append(flow) 
                else:
                    pass
            
            self.flow_buffer = remaining_flows
            
            return recent_flows
    
    def get_attack_labels(self, flows: List[NetworkFlow]) -> List[int]:
        """
        Returns the labesl for each flow in the list (0 = normal, 1+ = attack type)
        """
        return [flow.label for flow in flows]
    
    def force_update(self):
        """
        Force update by sending a command to the simulation via socket
        """
        if self.socket_connected:
            self.socket.sendall(b"request_update\n")
            response = self.socket.recv(1024).decode().strip()
            self.current_update_id += 1
            time.sleep(0.5)
            self._fetch_new_flows()
            return response
        return None
    
    def get_attack_info(self) -> Dict:
        """
        Takes a snapshot of current attacks from the REST API
        """
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
        """
        Takes metrics about hosts from REST API
        """
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
        """
        Takes the status of the simulation from the REST API
        """
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
    
    def send_command(self, command: str, params: Dict = None) -> Dict:
        """
        Sends a command to the simulation via socket and returns the response
        """
        if not self.socket_connected:
            raise ConnectionError("Socket not connected")
        
        cmd_str = command
        if params:
            cmd_str += " " + json.dumps(params)
        
        self.socket.sendall(f"{cmd_str}\n".encode())
        response = self.socket.recv(4096).decode().strip()
        
        try:
            return json.loads(response)
        except:
            return {"response": response}