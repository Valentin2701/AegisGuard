from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class FlowInput(BaseModel):
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    pattern: str = "unknown"
    bytes_sent: int
    packets_sent: int
    duration: float
    timestamp: datetime
    label: Optional[int] = 0
    tcp_state: Optional[str] = None
    qos_class: Optional[str] = None
    dscp: Optional[int] = None

class PredictRequest(BaseModel):
    flows: List[FlowInput]

class PredictResponse(BaseModel):
    attack_probability: float
    attack_detected: bool
    confidence: Optional[float] = None
    num_flows: int
    num_nodes: int
    num_edges: int