from flask import Blueprint, jsonify, request
from ..services.simulation_service import SimulationService
from ..utils.helpers import handle_errors

honeypots_bp = Blueprint('honeypots', __name__)
simulation_service = SimulationService()

@honeypots_bp.route('/honeypots', methods=['GET'])
@handle_errors
def get_all_honeypots():
    """Get all deployed honeypots"""
    honeypots = simulation_service.get_all_honeypots()
    return jsonify(honeypots), 200

@honeypots_bp.route('/honeypots/deploy', methods=['POST'])
@handle_errors
def deploy_honeypot():
    """Deploy a new honeypot"""
    data = request.get_json()
    
    required_fields = ['name', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    honeypot = simulation_service.deploy_honeypot(
        name=data['name'],
        honeypot_type=data['type'],
        ip=data.get('ip'),
        location=data.get('location')
    )
    
    return jsonify(honeypot), 201

@honeypots_bp.route('/honeypots/<honeypot_id>/trigger', methods=['POST'])
@handle_errors
def trigger_honeypot(honeypot_id):
    """Record a honeypot trigger"""
    data = request.get_json()
    result = simulation_service.trigger_honeypot(honeypot_id, data)
    return jsonify(result), 200

@honeypots_bp.route('/honeypots/<honeypot_id>', methods=['DELETE'])
@handle_errors
def remove_honeypot(honeypot_id):
    """Remove a honeypot"""
    result = simulation_service.remove_honeypot(honeypot_id)
    return jsonify(result), 200

@honeypots_bp.route('/honeypots/strategy', methods=['GET'])
@handle_errors
def get_honeypot_strategy():
    """Get current honeypot deployment strategy"""
    strategy = simulation_service.get_honeypot_strategy()
    return jsonify(strategy), 200

@honeypots_bp.route('/honeypots/strategy', methods=['PUT'])
@handle_errors
def update_honeypot_strategy():
    """Update honeypot deployment strategy"""
    data = request.get_json()
    strategy = simulation_service.update_honeypot_strategy(data)
    return jsonify(strategy), 200