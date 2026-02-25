from flask import Blueprint, jsonify, request
from ..services.network_service import NetworkService
from ..utils.helpers import handle_errors

network_bp = Blueprint('network', __name__)
network_service = NetworkService()

@network_bp.route('/network/status', methods=['GET'])
@handle_errors
def get_network_status():
    """Get overall network status"""
    status = network_service.get_network_status()
    return jsonify(status), 200

@network_bp.route('/network/nodes', methods=['GET'])
@handle_errors
def get_all_nodes():
    """Get all network nodes"""
    nodes = network_service.get_all_nodes()
    return jsonify(nodes), 200

@network_bp.route('/network/edges', methods=['GET'])
@handle_errors
def get_all_edges():
    """Get all network edges"""
    edges = network_service.get_all_edges()
    return jsonify(edges), 200

@network_bp.route('/network/connections', methods=['GET'])
@handle_errors
def get_all_connections():
    """Get all active connections"""
    connections = network_service.get_all_connections()
    return jsonify(connections), 200

@network_bp.route('/network/flows', methods=['GET'])
@handle_errors
def get_all_flows():
    """Get all network flows"""
    flows = network_service.get_all_flows()
    return jsonify(flows), 200

@network_bp.route('/network/nodes/<node_id>', methods=['GET'])
@handle_errors
def get_node(node_id):
    """Get specific node by ID"""
    node = network_service.get_node(node_id)
    if node:
        return jsonify(node), 200
    return jsonify({'error': 'Node not found'}), 404

@network_bp.route('/network/nodes/status/<status>', methods=['GET'])
@handle_errors
def get_nodes_by_status(status):
    """Get nodes by status (healthy, compromised, quarantined, etc.)"""
    nodes = network_service.get_nodes_by_status(status)
    return jsonify(nodes), 200

@network_bp.route('/network/topology', methods=['GET'])
@handle_errors
def get_network_topology():
    """Get complete network topology"""
    topology = network_service.get_network_topology()
    return jsonify(topology), 200