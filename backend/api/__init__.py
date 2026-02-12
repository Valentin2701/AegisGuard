# Initialize Flask app
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'aegis-guard-secret-key-change-this'
    app.config['CORS_HEADERS'] = 'Content-Type'
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*")
    
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