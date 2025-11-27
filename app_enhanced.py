"""
Main Flask Application - Enhanced Version 2.0
Includes all high-priority improvements:
- Celery Integration
- JWT Authentication
- WebSocket Support
- Rate Limiting
- RAGAS Integration
- Async Operations
- SSE Streaming
- Model Versioning
- Prometheus Monitoring
- Swagger Documentation
"""
import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# Import configurations
from config import config

# Import middleware
from app.middleware.rate_limiter import limiter
from app.monitoring.prometheus_metrics import PrometheusMiddleware

# Import WebSocket
from app.websocket.socketio_manager import WebSocketManager, socketio

# Import documentation
from app.docs.swagger_config import swagger_blueprint, api_spec_blueprint

logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """
    Application factory with all enhancements
    
    Args:
        config_name: Configuration environment name
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app()
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/socket.io/*": {"origins": "*"}
    })
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup middleware
    setup_middleware(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Setup documentation
    setup_documentation(app)
    
    logger.info(f"Application created in {app.config['FLASK_ENV']} mode")
    
    return app


def initialize_extensions(app):
    """Initialize Flask extensions"""
    
    # Rate Limiter
    limiter.init_app(app)
    logger.info("Rate limiter initialized")
    
    # WebSocket (Socket.IO)
    WebSocketManager.init_app(app)
    logger.info("WebSocket initialized")
    
    # Prometheus Monitoring
    PrometheusMiddleware(app)
    logger.info("Prometheus monitoring initialized")


def register_blueprints(app):
    """Register all blueprints"""
    
    # Import routes
    from app.routes import (
        auth_routes,
        analysis_routes,
        image_routes,
        similarity_routes,
        ai_detector_routes,
        chat_routes,
        task_routes
    )
    
    # Authentication routes
    app.register_blueprint(auth_routes.bp, url_prefix='/api/auth')
    
    # Analysis routes
    app.register_blueprint(analysis_routes.bp, url_prefix='/api/analysis')
    
    # Image routes
    app.register_blueprint(image_routes.bp, url_prefix='/api/images')
    
    # Similarity routes
    app.register_blueprint(similarity_routes.bp, url_prefix='/api/similarity')
    
    # AI Detection routes
    app.register_blueprint(ai_detector_routes.bp, url_prefix='/api/ai-detect')
    
    # Chat routes
    app.register_blueprint(chat_routes.bp, url_prefix='/api/chat')
    
    # Task management routes
    app.register_blueprint(task_routes.bp, url_prefix='/api/tasks')
    
    logger.info("Blueprints registered")


def setup_middleware(app):
    """Setup custom middleware"""
    
    @app.before_request
    def before_request():
        """Before request handler"""
        pass
    
    @app.after_request
    def after_request(response):
        """After request handler - add headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        from flask import jsonify
        return jsonify({
            'error': 'Resource not found',
            'status': 'error'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import jsonify
        logger.exception("Internal server error")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        from flask import jsonify
        return jsonify({
            'error': 'Rate limit exceeded',
            'status': 'error',
            'message': str(error)
        }), 429


def setup_documentation(app):
    """Setup API documentation"""
    
    # Swagger UI
    app.register_blueprint(swagger_blueprint)
    app.register_blueprint(api_spec_blueprint)
    
    logger.info("API documentation configured at /api/docs")


# Root endpoints
@app.route('/')
def index():
    """Serve frontend"""
    return send_from_directory('app/static', 'index.html')


@app.route('/health')
def health_check():
    """Health check endpoint"""
    from flask import jsonify
    return jsonify({
        'status': 'healthy',
        'service': 'Intelligent Analysis System',
        'version': '2.0.0',
        'features': {
            'celery': True,
            'jwt': True,
            'websocket': True,
            'rate_limiting': True,
            'prometheus': True,
            'swagger': True
        }
    }), 200


@app.route('/api')
def api_info():
    """API information"""
    from flask import jsonify
    return jsonify({
        'service': 'Intelligent Analysis System API',
        'version': '2.0.0',
        'documentation': '/api/docs',
        'health': '/health',
        'metrics': '/metrics',
        'endpoints': {
            'auth': '/api/auth/*',
            'analysis': '/api/analysis/*',
            'tasks': '/api/tasks/*',
            'chat': '/api/chat/*',
            'images': '/api/images/*',
            'similarity': '/api/similarity/*',
            'ai_detect': '/api/ai-detect/*'
        },
        'websocket': '/socket.io/',
        'features': [
            'JWT Authentication',
            'Celery Task Queue',
            'Real-time WebSocket',
            'Rate Limiting per User',
            'RAGAS Evaluation',
            'SSE Streaming',
            'Model Versioning',
            'Prometheus Metrics'
        ]
    }), 200


# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Run with Socket.IO support
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )