import asyncio
import logging
import socketio
from fastapi import FastAPI, HTTPException
import torch
from torch_geometric.data import Batch
import time
from typing import List
from .schemas import PredictRequest, PredictResponse, FlowInput
from .model_loader import load_model
from ..data.interface import NetworkFlow

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ----------------------------------------------------------------------
# 1. Create Socket.IO server (ASGI mode)
# ----------------------------------------------------------------------
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

app = FastAPI(title="AegisGuard GNN Inference Server")

# Mount Socket.IO onto the FastAPI app (the ASGI app will be used for running)
# We'll create an ASGI app that combines both later.

# Global variables for model and components
model = None
feature_extractor = None
graph_builder = None
config = None

def flows_to_networkflow(flow_inputs: List[FlowInput]) -> List[NetworkFlow]:
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

# ----------------------------------------------------------------------
# 2. Socket.IO event handlers
# ----------------------------------------------------------------------
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.on('flows')
async def handle_flows(sid, data):
    """
    Receives a list of flows, runs inference, and emits the result back.
    """
    if model is None:
        logger.warning("Model not loaded yet")
        await sio.emit('gnn_error', {'error': 'Model not loaded'}, room=sid)
        return

    flows_data = data.get('flows', [])
    if not flows_data:
        await sio.emit('gnn_error', {'error': 'No flows provided'}, room=sid)
        return

    # Convert to Pydantic models (FlowInput) for validation
    try:
        flow_inputs = [FlowInput(**f) for f in flows_data]
    except Exception as e:
        logger.error(f"Invalid flow data: {e}")
        await sio.emit('gnn_error', {'error': f'Invalid flow data: {e}'}, room=sid)
        return

    # Convert to internal NetworkFlow
    flows = flows_to_networkflow(flow_inputs)

    # Build graph
    graph = graph_builder.build_graph(flows)
    if graph.num_nodes == 0:
        result = {
            'attack_probability': 0.0,
            'attack_detected': False,
            'num_flows': len(flows),
            'num_nodes': 0,
            'num_edges': 0
        }
        await sio.emit('gnn_prediction', result, room=sid)
        return

    # Prepare batch
    batch = Batch.from_data_list([graph])

    # Inference
    with torch.no_grad():
        logits = model(batch)
        probs = torch.softmax(logits, dim=1)
        attack_prob = probs[0, 1].item()

    attack_detected = attack_prob > 0.5  # threshold can be adjusted

    result = {
        'attack_probability': attack_prob,
        'attack_detected': attack_detected,
        'num_flows': len(flows),
        'num_nodes': graph.num_nodes,
        'num_edges': graph.num_edges
    }

    logger.debug(f"Sending result to {sid}: {result}")
    await sio.emit('gnn_prediction', result, room=sid)

# ----------------------------------------------------------------------
# 3. FastAPI routes (for health checks, etc.)
# ----------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    global model, feature_extractor, graph_builder, config
    logger.info("Loading model...")
    # Adjust path to your checkpoints folder
    model, feature_extractor, graph_builder, config = load_model("models/")
    logger.info("Model loaded successfully.")

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

# ----------------------------------------------------------------------
# 4. Combine FastAPI and Socket.IO into a single ASGI application
# ----------------------------------------------------------------------
# Mount Socket.IO app onto the FastAPI app
app.mount('/', socketio.ASGIApp(sio, other_asgi_app=app))

# Alternatively, we can create a new ASGI app that combines them, but mounting is simpler.
# However, note that the order matters: we want FastAPI to handle HTTP routes and Socket.IO to handle WebSocket routes.
# The following works: we create an ASGI app that routes WebSocket to Socket.IO and everything else to FastAPI.

# But the ASGIApp already takes other_asgi_app, so the above is sufficient.