"""
Error Handler Middleware
Centralized error handling for the application
"""
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom API error class"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status'] = 'error'
        return rv


def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.error(f"API Error: {error.message} (Status: {error.status_code})")
        return response
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions"""
        response = jsonify({
            'error': error.description,
            'status': 'error',
            'code': error.code
        })
        response.status_code = error.code
        logger.error(f"HTTP Exception: {error.description} (Status: {error.code})")
        return response
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Resource not found',
            'status': 'error'
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors"""
        logger.exception("Internal server error")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(413)
    def handle_file_too_large(error):
        """Handle file size exceeded errors"""
        return jsonify({
            'error': 'File too large',
            'status': 'error',
            'message': 'The uploaded file exceeds the maximum allowed size'
        }), 413
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected errors"""
        logger.exception("Unexpected error")
        return jsonify({
            'error': 'Unexpected error',
            'status': 'error',
            'message': str(error) if app.config.get('DEBUG') else 'An error occurred'
        }), 500
