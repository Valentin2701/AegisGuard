import random
from backend.simulation.attack_generator import AttackGenerator
from backend.simulation.network_graph import NetworkGraph
from backend.simulation.traffic_generator import TrafficGenerator
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

class SimulationState:
    def __init__(self):
        self.network = NetworkGraph()
        self.network.create_small_office_network()
        
        self.traffic_generator = TrafficGenerator(self.network)
        self.attack_generator = AttackGenerator(self.network)
        
        self.is_running = False
        self.start_time = None

    def update(self, timedelta):
        """Advance the simulation by one step"""
        if self.is_running:
            self.attack_generator.update(time_delta=timedelta)
            self.traffic_generator.generate_packets(time_delta=timedelta)
            edge = random.choice(list(self.network.edges.values()))
            self.traffic_generator.create_connection(edge.source_id, edge.target_id, None)

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = '5uper53cr3tk3y22432354'
    app.config['CORS_HEADERS'] = 'Content-Type'
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*")

    # Initialize simulation state
    app.simulation_state = SimulationState()
    
    # Register blueprints
    from .routes.network import network_bp
    from .routes.attacks import attacks_bp
    from .routes.agents import agents_bp
    from .routes.honeypots import honeypots_bp
    from .routes.quarantine import quarantine_bp
    from .routes.metrics import metrics_bp
    from .routes.simulation import simulation_bp
    
    app.register_blueprint(network_bp, url_prefix='/api/v1')
    app.register_blueprint(attacks_bp, url_prefix='/api/v1')
    app.register_blueprint(agents_bp, url_prefix='/api/v1')
    app.register_blueprint(honeypots_bp, url_prefix='/api/v1')
    app.register_blueprint(quarantine_bp, url_prefix='/api/v1')
    app.register_blueprint(metrics_bp, url_prefix='/api/v1')
    app.register_blueprint(simulation_bp, url_prefix='/api/v1')
    
    return app