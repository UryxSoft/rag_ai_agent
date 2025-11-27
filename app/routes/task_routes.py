"""
Task Management Routes
Celery task status and control
"""
import logging
from flask import Blueprint, jsonify
from app.auth.jwt_manager import require_jwt_token
from celery_worker import get_task_status, cancel_task

logger = logging.getLogger(__name__)

bp = Blueprint('tasks', __name__)


@bp.route('/<task_id>', methods=['GET'])
@require_jwt_token
def get_task(task_id):
    """
    Get task status
    
    GET /api/tasks/<task_id>
    """
    try:
        status = get_task_status(task_id)
        
        return jsonify({
            'status': 'success',
            'task_id': task_id,
            **status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return jsonify({
            'error': 'Failed to get task status',
            'status': 'error'
        }), 500


@bp.route('/<task_id>/cancel', methods=['POST'])
@require_jwt_token
def cancel_task_route(task_id):
    """
    Cancel running task
    
    POST /api/tasks/<task_id>/cancel
    """
    try:
        result = cancel_task(task_id)
        
        logger.info(f"Task cancelled: {task_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Task cancelled',
            **result
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        return jsonify({
            'error': 'Failed to cancel task',
            'status': 'error'
        }), 500


@bp.route('/list', methods=['GET'])
@require_jwt_token
def list_tasks():
    """
    List user's tasks
    
    GET /api/tasks/list
    """
    try:
        # In production, would query from database
        # For now, return mock data
        return jsonify({
            'status': 'success',
            'tasks': [],
            'total': 0
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return jsonify({
            'error': 'Failed to list tasks',
            'status': 'error'
        }), 500