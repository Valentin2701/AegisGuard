import socketio
import logging
from ..config import Config

logger = logging.getLogger(__name__)

class GNNClient:
    """Socket.IO Client for server connection"""

    def __init__(self, server_url=None):
        self.server_url = server_url or Config.GNN_SERVER_URL
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.connected = False
        self.main_sio = None
        self._register_handlers()

    def _register_handlers(self):
        @self.sio.event
        def connect():
            self.connected = True
            logger.info("✅ Connected to GNN inference server")

        @self.sio.event
        def disconnect():
            self.connected = False
            logger.warning("🔌 Disconnected from GNN inference server")

        @self.sio.on('gnn_prediction')
        def on_gnn_prediction(data):
            logger.debug(f"Received GNN prediction: {data}")
            if self.main_sio:
                # Send prediction to client
                self.main_sio.emit('gnn_prediction', data)

        @self.sio.on('gnn_error')
        def on_gnn_error(data):
            logger.error(f"GNN error: {data}")
            if self.main_sio:
                self.main_sio.emit('gnn_error', data)

    def connect(self, main_sio=None):
        """
        Connects to GNN server
        :param main_sio: главният Socket.IO сървър (flask-socketio), за да можем да изпращаме резултати на фронтенда
        """
        self.main_sio = main_sio
        try:
            self.sio.connect(self.server_url, wait_timeout=5)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to GNN server: {e}")
            return False

    def disconnect(self):
        if self.connected:
            self.sio.disconnect()

    def send_flows(self, flows_data):
        """
        Sends a flow to GNN server
        :param flows_data: list of flows (dict)
        """
        if not self.connected:
            logger.warning("GNN client not connected, cannot send flows")
            return False
        try:
            self.sio.emit('flows', {'flows': flows_data})
            return True
        except Exception as e:
            logger.error(f"Error sending flows to GNN: {e}")
            return False