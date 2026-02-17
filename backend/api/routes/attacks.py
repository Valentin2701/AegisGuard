from flask import Blueprint, jsonify, request
from ..services.simulation_service import SimulationService
from ..utils.helpers import handle_errors

attacks_bp = Blueprint('attacks', __name__)
simulation_service = SimulationService()

@attacks_bp.route('/attacks', methods=['GET'])
@handle_errors
def get_all_attacks():
    """Get all active attacks"""
    attacks = simulation_service.get_active_attacks()
    return jsonify(attacks), 200

@attacks_bp.route('/attacks/<attack_id>', methods=['GET'])
@handle_errors
def get_attack(attack_id):
    """Get specific attack by ID"""
    attack = simulation_service.get_attack(attack_id)
    if attack:
        return jsonify(attack.to_dict()), 200
    return jsonify({'error': 'Attack not found'}), 404

@attacks_bp.route('/attacks/inject', methods=['POST'])
@handle_errors
def inject_attack():
    """Inject a new attack into the network"""
    data = request.get_json()
    
    required_fields = ['type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    severity_enum = {'Low': 0.3, 'Medium': 0.6, 'High': 0.8, 'Critical': 1.0}
    
    attack = simulation_service.inject_attack(
        attack_type=data['type'],
        severity=severity_enum.get(data.get('severity', 'Medium'), 0.6)
    )
    
    return jsonify(attack.to_dict()), 201

@attacks_bp.route('/attacks/<attack_id>/mitigate', methods=['POST'])
@handle_errors
def mitigate_attack(attack_id):
    """Mitigate an active attack"""
    result = simulation_service.mitigate_attack(attack_id)
    return jsonify(result), 200

@attacks_bp.route('/attacks/history', methods=['GET'])
@handle_errors
def get_attack_history():
    """Get attack history"""
    limit = request.args.get('limit', default=100, type=int)
    history = simulation_service.get_attack_history(limit)
    return jsonify(history), 200