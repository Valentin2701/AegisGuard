from flask import Blueprint, jsonify, request
from ..services.simulation_service import SimulationService
from ..utils.helpers import handle_errors

metrics_bp = Blueprint('metrics', __name__)
simulation_service = SimulationService()

@metrics_bp.route('/metrics', methods=['GET'])
@handle_errors
def get_metrics():
    """Get current metrics"""
    metrics = simulation_service.get_current_metrics()
    return jsonify(metrics), 200

@metrics_bp.route('/metrics/history', methods=['GET'])
@handle_errors
def get_metrics_history():
    """Get historical metrics"""
    timeframe = request.args.get('timeframe', default='3m')
    metrics = simulation_service.get_metrics_history(timeframe)
    return jsonify(metrics), 200

@metrics_bp.route('/metrics/traffic', methods=['GET'])
@handle_errors
def get_traffic_metrics():
    """Get network traffic metrics"""
    traffic = simulation_service.get_traffic_metrics()
    return jsonify(traffic), 200

@metrics_bp.route('/metrics/threats', methods=['GET'])
@handle_errors
def get_threat_metrics():
    """Get threat level metrics"""
    threats = simulation_service.get_threat_metrics()
    return jsonify(threats), 200

@metrics_bp.route('/metrics/performance', methods=['GET'])
@handle_errors
def get_performance_metrics():
    """Get system performance metrics"""
    performance = simulation_service.get_performance_metrics()
    return jsonify(performance), 200