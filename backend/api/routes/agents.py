from flask import Blueprint, jsonify, request
from ..services.simulation_service import SimulationService
from ..utils.helpers import handle_errors

agents_bp = Blueprint('agents', __name__)
simulation_service = SimulationService()

@agents_bp.route('/agents', methods=['GET'])
@handle_errors
def get_all_agents():
    """Get all AI agents"""
    agents = simulation_service.get_all_agents()
    return jsonify(agents), 200

@agents_bp.route('/agents/actions', methods=['GET'])
@handle_errors
def get_agent_actions():
    """Get recent agent actions"""
    limit = request.args.get('limit', default=50, type=int)
    actions = simulation_service.get_agent_actions(limit)
    return jsonify(actions), 200

@agents_bp.route('/agents/<agent_id>', methods=['GET'])
@handle_errors
def get_agent(agent_id):
    """Get specific agent by ID"""
    agent = simulation_service.get_agent(agent_id)
    if agent:
        return jsonify(agent), 200
    return jsonify({'error': 'Agent not found'}), 404

@agents_bp.route('/agents/<agent_id>/decisions', methods=['GET'])
@handle_errors
def get_agent_decisions(agent_id):
    """Get decision history for a specific agent"""
    decisions = simulation_service.get_agent_decisions(agent_id)
    return jsonify(decisions), 200