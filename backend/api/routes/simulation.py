from flask import Blueprint, jsonify, request
from flask_socketio import emit
from .. import socketio
from ..services.simulation_service import SimulationService
from ..utils.helpers import handle_errors

simulation_bp = Blueprint('simulation', __name__)
simulation_service = SimulationService()

@simulation_bp.route('/simulation/control', methods=['POST'])
@handle_errors
def control_simulation():
    """Control simulation state (start, pause, reset)"""
    data = request.get_json()
    
    if 'action' not in data:
        return jsonify({'error': 'Missing action field'}), 400
    
    action = data['action']
    result = simulation_service.control_simulation(action, data)
    
    # Emit WebSocket event
    socketio.emit('simulation_state_change', result)
    
    return jsonify(result), 200

@simulation_bp.route('/simulation/state', methods=['GET'])
@handle_errors
def get_simulation_state():
    """Get current simulation state"""
    state = simulation_service.get_simulation_state()
    return jsonify(state), 200

@simulation_bp.route('/simulation/config', methods=['GET'])
@handle_errors
def get_simulation_config():
    """Get simulation configuration"""
    config = simulation_service.get_simulation_config()
    return jsonify(config), 200

@simulation_bp.route('/simulation/config', methods=['PUT'])
@handle_errors
def update_simulation_config():
    """Update simulation configuration"""
    data = request.get_json()
    config = simulation_service.update_simulation_config(data)
    return jsonify(config), 200

@simulation_bp.route('/simulation/seed', methods=['POST'])
@handle_errors
def seed_simulation():
    """Seed simulation with specific parameters"""
    data = request.get_json()
    result = simulation_service.seed_simulation(data)
    return jsonify(result), 200

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'data': 'Connected to Aegis Guard simulation'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_update')
def handle_update_request(data):
    """Client requests real-time update"""
    simulation_service.update_simulation(data)