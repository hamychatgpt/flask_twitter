from flask_socketio import SocketIO

socketio = SocketIO()

def init_app(app):
    """Initialize SocketIO with Flask app"""
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register event handlers
    from . import events