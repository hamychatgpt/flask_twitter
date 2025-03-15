from flask import current_app
from flask_socketio import emit, join_room, leave_room
from . import socket

@socket.socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    current_app.logger.info('Client connected')
    emit('connect_response', {'status': 'connected'})

@socket.socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    current_app.logger.info('Client disconnected')

@socket.socketio.on('join')
def handle_join(data):
    """Handle client joining a tracking room"""
    tracking_term = data.get('term')
    if tracking_term:
        room = f"track_{tracking_term}"
        join_room(room)
        current_app.logger.info(f'Client joined room: {room}')
        emit('join_response', {'status': 'joined', 'term': tracking_term})

@socket.socketio.on('leave')
def handle_leave(data):
    """Handle client leaving a tracking room"""
    tracking_term = data.get('term')
    if tracking_term:
        room = f"track_{tracking_term}"
        leave_room(room)
        current_app.logger.info(f'Client left room: {room}')
        emit('leave_response', {'status': 'left', 'term': tracking_term})