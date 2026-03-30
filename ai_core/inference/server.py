from datetime import datetime

import socketio
import torch
from fastapi import FastAPI
import logging
from .model_loader import load_model
from .schemas import PredictResponse
from ..data import NetworkFlow

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI(title="AegisGuard GNN Inference Server (WebSocket)")
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Global variables
model = None
feature_extractor = None
graph_builder = None
config = None

@app.on_event("startup")
def startup_event():
    global model, feature_extractor, graph_builder, config
    logging.info("Loading model...")
    model, feature_extractor, graph_builder, config = load_model("models/")
    logging.info("Model loaded.")

@sio.event
async def connect(sid, environ):
    logging.info(f"GNN client connected: {sid}")

@sio.event
async def disconnect(sid):
    logging.info(f"GNN client disconnected: {sid}")

@sio.on('flows')
async def handle_flows(sid, data):
    """
    Takes a list of flows from the simulation backend, processes them through the GNN model, and emits back the prediction results.
    """
    if model is None:
        await sio.emit('gnn_error', {'error': 'Model not loaded'}, room=sid)
        return

    try:
        flows_data = data.get('flows', [])
        if not flows_data:
            await sio.emit('gnn_error', {'error': 'No flows provided'}, room=sid)
            return

        # Convert to NetworkFlow objects
        flows = []
        for f in flows_data:
            flow = NetworkFlow(
                src_ip=f['src_ip'],
                dst_ip=f['dst_ip'],
                src_port=f['src_port'],
                dst_port=f['dst_port'],
                protocol=f['protocol'],
                pattern=f.get('pattern', 'unknown'),
                bytes_sent=f['bytes_sent'],
                packets_sent=f['packets_sent'],
                duration=f['duration'],
                timestamp=datetime.fromisoformat(f['timestamp']),
                label=f.get('label', 0),
                tcp_state=f.get('tcp_state'),
                qos_class=f.get('qos_class'),
                dscp=f.get('dscp')
            )
            flows.append(flow)

        # Build graph and predict
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
        from torch_geometric.data import Batch
        batch = Batch.from_data_list([graph])

        with torch.no_grad():
            logits = model(batch)
            probs = torch.softmax(logits, dim=1)
            attack_prob = probs[0, 1].item()

        result = {
            'attack_probability': attack_prob,
            'attack_detected': attack_prob > 0.5,
            'num_flows': len(flows),
            'num_nodes': graph.num_nodes,
            'num_edges': graph.num_edges
        }

        # Send result back to backend simulation
        await sio.emit('gnn_prediction', result, room=sid)

    except Exception as e:
        logging.error(f"Error processing flows: {e}")
        await sio.emit('gnn_error', {'error': str(e)}, room=sid)

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}