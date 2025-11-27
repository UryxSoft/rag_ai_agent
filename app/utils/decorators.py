"""
Utility Decorators
Common decorators for routes and functions
"""
import time
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


def timing_decorator(f):
    """Decorator to measure function execution time"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"{f.__name__} executed in {execution_time:.4f} seconds")
        
        return result
    
    return wrapper


def validate_json(required_fields=None):
    """
    Decorator to validate JSON request data
    
    Usage:
        @validate_json(['file_id', 'analysis_type'])
        def analyze():
            data = request.get_json()
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Content-Type must be application/json',
                    'status': 'error'
                }), 400
            
            data = request.get_json()
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields,
                        'status': 'error'
                    }), 400
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_file_upload(allowed_extensions=None):
    """
    Decorator to validate file uploads
    
    Usage:
        @validate_file_upload(['pdf', 'docx'])
        def upload_document():
            file = request.files['file']
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({
                    'error': 'No file provided',
                    'status': 'error'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'error': 'No file selected',
                    'status': 'error'
                }), 400
            
            if allowed_extensions:
                extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if extension not in allowed_extensions:
                    return jsonify({
                        'error': 'File type not allowed',
                        'allowed_types': list(allowed_extensions),
                        'status': 'error'
                    }), 400
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator


def rate_limit(max_requests=10, window_seconds=60):
    """
    Simple rate limiting decorator
    Note: This is a basic implementation. For production, use Flask-Limiter
    """
    from collections import defaultdict
    from datetime import datetime, timedelta
    
    requests_log = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get client identifier (IP address)
            client_id = request.remote_addr
            
            # Get current time
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old requests
            requests_log[client_id] = [
                req_time for req_time in requests_log[client_id]
                if req_time > window_start
            ]
            
            # Check rate limit
            if len(requests_log[client_id]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'status': 'error',
                    'retry_after': window_seconds
                }), 429
            
            # Log this request
            requests_log[client_id].append(now)
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator


def log_request(f):
    """Decorator to log request details"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        return f(*args, **kwargs)
    
    return wrapper
