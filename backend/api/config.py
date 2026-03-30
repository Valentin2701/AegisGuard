import os

class Config:
    GNN_SERVER_URL = os.getenv('GNN_SERVER_URL', 'http://localhost:8001')