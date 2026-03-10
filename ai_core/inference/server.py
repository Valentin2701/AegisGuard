from fastapi import FastAPI, HTTPException
import logging
import time
from typing import List
import torch
from torch_geometric.data import Batch

from .schemas import PredictRequest, PredictResponse, FlowInput
from .model_loader import load_model
from ..data.interface import NetworkFlow

# Set logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AegisGuard GNN Inference Server")

# Global variables to hold the model and related components
model = None
feature_extractor = None
graph_builder = None
config = None

@app.on_event("startup")
def startup_event():
    global model, feature_extractor, graph_builder, config
    logger.info("Loading model...")
    model, feature_extractor, graph_builder, config = load_model("ai_core/checkpoints/")
    logger.info("Model loaded successfully.")

def flows_to_networkflow(flow_inputs: List[FlowInput]) -> List[NetworkFlow]:
    """Converts Pydantic models to the internal NetworkFlow."""
    flows = []
    for f in flow_inputs:
        flow = NetworkFlow(
            src_ip=f.src_ip,
            dst_ip=f.dst_ip,
            src_port=f.src_port,
            dst_port=f.dst_port,
            protocol=f.protocol,
            pattern=f.pattern,
            bytes_sent=f.bytes_sent,
            packets_sent=f.packets_sent,
            duration=f.duration,
            timestamp=f.timestamp,
            label=f.label,
            tcp_state=f.tcp_state,
            qos_class=f.qos_class,
            dscp=f.dscp
        )
        flows.append(flow)
    return flows

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = time.time()
    
    # Convert
    flows = flows_to_networkflow(request.flows)
    if not flows:
        raise HTTPException(status_code=400, detail="No flows provided")
    
    graph = graph_builder.build_graph(flows)
    if graph.num_nodes == 0:
        return PredictResponse(
            attack_probability=0.0,
            attack_detected=False,
            num_flows=len(flows),
            num_nodes=0,
            num_edges=0
        )
    
    batch = Batch.from_data_list([graph])
    
    # Inference
    with torch.no_grad():
        logits = model(batch)
        probs = torch.softmax(logits, dim=1)
        attack_prob = probs[0, 1].item()
        attack_detected = attack_prob > 0.5
    
    inference_time = time.time() - start_time
    logger.info(f"Inference took {inference_time:.3f}s, attack_prob={attack_prob:.4f}")
    
    return PredictResponse(
        attack_probability=attack_prob,
        attack_detected=attack_detected,
        num_flows=len(flows),
        num_nodes=graph.num_nodes,
        num_edges=graph.num_edges
    )

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}