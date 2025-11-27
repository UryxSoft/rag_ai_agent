"""
WebSocket Support with Socket.IO
Real-time updates for analysis progress
"""
import logging
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask import request
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Initialize Socket.IO
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True
)


class WebSocketManager:
    """Manage WebSocket connections and broadcasts"""
    
    @staticmethod
    def init_app(app):
        """Initialize Socket.IO with Flask app"""
        socketio.init_app(
            app,
            cors_allowed_origins="*",
            message_queue='redis://redis:6379/3'
        )
        logger.info("WebSocket initialized")
    
    @staticmethod
    def broadcast_task_update(task_id: str, status: Dict[str, Any]):
        """
        Broadcast task update to connected clients
        
        Args:
            task_id: Task identifier
            status: Task status information
        """
        socketio.emit(
            'task_update',
            {
                'task_id': task_id,
                'status': status
            },
            room=task_id
        )
    
    @staticmethod
    def broadcast_analysis_progress(task_id: str, progress: int, message: str):
        """
        Broadcast analysis progress
        
        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            message: Progress message
        """
        socketio.emit(
            'analysis_progress',
            {
                'task_id': task_id,
                'progress': progress,
                'message': message
            },
            room=task_id
        )
    
    @staticmethod
    def send_chat_message(session_id: str, message: str, role: str = 'assistant'):
        """
        Send chat message to client
        
        Args:
            session_id: Chat session ID
            message: Message content
            role: Message role (user/assistant)
        """
        socketio.emit(
            'chat_message',
            {
                'session_id': session_id,
                'message': message,
                'role': role
            },
            room=session_id
        )


# Socket.IO Event Handlers

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {
        'status': 'success',
        'message': 'Connected to WebSocket server',
        'sid': request.sid
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('join_task')
def handle_join_task(data: Dict[str, Any]):
    """
    Join task room for updates
    
    Args:
        data: {'task_id': 'task_xxx'}
    """
    task_id = data.get('task_id')
    if task_id:
        join_room(task_id)
        logger.info(f"Client {request.sid} joined task room: {task_id}")
        emit('joined_task', {
            'task_id': task_id,
            'message': f'Joined task room: {task_id}'
        })


@socketio.on('leave_task')
def handle_leave_task(data: Dict[str, Any]):
    """
    Leave task room
    
    Args:
        data: {'task_id': 'task_xxx'}
    """
    task_id = data.get('task_id')
    if task_id:
        leave_room(task_id)
        logger.info(f"Client {request.sid} left task room: {task_id}")
        emit('left_task', {
            'task_id': task_id,
            'message': f'Left task room: {task_id}'
        })


@socketio.on('join_chat')
def handle_join_chat(data: Dict[str, Any]):
    """
    Join chat session room
    
    Args:
        data: {'session_id': 'session_xxx'}
    """
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logger.info(f"Client {request.sid} joined chat room: {session_id}")
        emit('joined_chat', {
            'session_id': session_id,
            'message': f'Joined chat session: {session_id}'
        })


@socketio.on('chat_input')
def handle_chat_input(data: Dict[str, Any]):
    """
    Handle chat input from client
    
    Args:
        data: {'session_id': 'xxx', 'message': 'user message'}
    """
    session_id = data.get('session_id')
    message = data.get('message')
    
    logger.info(f"Chat input from {request.sid}: {message}")
    
    # Echo back to user
    emit('chat_message', {
        'session_id': session_id,
        'message': message,
        'role': 'user'
    }, room=session_id)
    
    # Trigger AI response (would call actual service)
    # For now, echo back
    emit('chat_message', {
        'session_id': session_id,
        'message': f'Echo: {message}',
        'role': 'assistant'
    }, room=session_id)


@socketio.on('request_task_status')
def handle_task_status_request(data: Dict[str, Any]):
    """
    Request current task status
    
    Args:
        data: {'task_id': 'task_xxx'}
    """
    task_id = data.get('task_id')
    
    # Get task status from Celery
    from celery_worker import get_task_status
    status = get_task_status(task_id)
    
    emit('task_status', {
        'task_id': task_id,
        'status': status
    })


@socketio.on_error()
def error_handler(e):
    """Handle Socket.IO errors"""
    logger.error(f"Socket.IO error: {e}")
    emit('error', {
        'error': str(e),
        'message': 'An error occurred'
    })


@socketio.on_error_default
def default_error_handler(e):
    """Handle all other errors"""
    logger.error(f"Socket.IO default error: {e}")
    emit('error', {
        'error': str(e),
        'message': 'An unexpected error occurred'
    })


# Helper function to emit from outside Socket.IO context
def emit_task_update(task_id: str, update: Dict[str, Any]):
    """
    Emit task update from outside Socket.IO context
    Can be called from Celery tasks
    
    Args:
        task_id: Task identifier
        update: Update data
    """
    socketio.emit(
        'task_update',
        {
            'task_id': task_id,
            **update
        },
        room=task_id,
        namespace='/'
    )