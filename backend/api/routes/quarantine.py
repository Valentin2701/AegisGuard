from flask import Blueprint, jsonify, request
from ..services.network_service import NetworkService
from ..utils.helpers import handle_errors

quarantine_bp = Blueprint('quarantine', __name__)
network_service = NetworkService()

@quarantine_bp.route('/quarantine', methods=['GET'])
@handle_errors
def get_quarantined_nodes():
    """Get all quarantined nodes"""
    nodes = network_service.get_quarantined_nodes()
    return jsonify(nodes), 200

@quarantine_bp.route('/quarantine/<node_id>', methods=['POST'])
@handle_errors
def quarantine_node(node_id):
    """Quarantine a specific node"""
    data = request.get_json()
    reason = data.get('reason', 'Security threat detected')
    
    result = network_service.quarantine_node(node_id, reason)
    if result:
        return jsonify(result), 200
    return jsonify({'error': 'Node not found'}), 404

@quarantine_bp.route('/quarantine/<node_id>', methods=['DELETE'])
@handle_errors
def release_node(node_id):
    """Release a node from quarantine"""
    result = network_service.release_node(node_id)
    if result:
        return jsonify(result), 200
    return jsonify({'error': 'Node not found'}), 404

@quarantine_bp.route('/quarantine/logs', methods=['GET'])
@handle_errors
def get_quarantine_logs():
    """Get quarantine action logs"""
    logs = network_service.get_quarantine_logs()
    return jsonify(logs), 200