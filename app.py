"""
Main Flask Application Entry Point
Sistema de Análisis Inteligente - MVP with Advanced Features
"""
import os
import logging
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from config import Config

# Import all route blueprints
from app.routes import (
    analysis_routes,
    image_routes,
    similarity_routes,
    ai_detector_routes,
    chat_routes,
    auth_routes
)

# Import middleware
from app.middleware.error_handler import register_error_handlers
from app.middleware.auth_middleware import require_api_key

# Import new features
from app.auth import init_jwt_manager, init_user_store
from app.websocket import init_socketio
from app.rate_limiter import init_rate_limiter
from app.ragas_integration import init_ragas_evaluator
from app.model_versioning import init_model_registry
from app.swagger_docs import init_swagger
from app.metrics import init_metrics_middleware, metrics_endpoint
from app.utils.cache import cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize configuration
    Config.init_app()
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize cache
    cache.init_app(app)
    
    # Initialize JWT authentication
    init_jwt_manager(app)
    init_user_store(cache.client)
    
    # Initialize WebSocket
    socketio = init_socketio(app)
    
    # Initialize rate limiter
    init_rate_limiter(cache.client)
    
    # Initialize RAGAS evaluator
    # init_ragas_evaluator()  # Initialize when LLM service is ready
    
    # Initialize model registry
    init_model_registry()
    
    # Initialize Swagger documentation
    init_swagger(app)
    
    # Initialize metrics middleware
    init_metrics_middleware(app)
    
    # Register blueprints
    app.register_blueprint(auth_routes.bp, url_prefix='/api/auth')
    app.register_blueprint(analysis_routes.bp, url_prefix='/api/analysis')
    app.register_blueprint(image_routes.bp, url_prefix='/api/images')
    app.register_blueprint(similarity_routes.bp, url_prefix='/api/similarity')
    app.register_blueprint(ai_detector_routes.bp, url_prefix='/api/ai-detect')
    app.register_blueprint(chat_routes.bp, url_prefix='/api/chat')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'intelligent-analysis-system',
            'version': '2.0.0',
            'features': {
                'jwt_auth': True,
                'websocket': True,
                'celery': True,
                'rate_limiting': True,
                'ragas': True,
                'prometheus': True,
                'swagger': True
            }
        }), 200
    
    # Metrics endpoint for Prometheus
    @app.route('/metrics', methods=['GET'])
    def metrics():
        """Prometheus metrics endpoint"""
        return metrics_endpoint()
    
    # Root endpoint - Serve HTML interface
    @app.route('/', methods=['GET'])
    def root():
        """Serve main HTML interface"""
        return render_template('index.html')
    
    # API info endpoint
    @app.route('/api', methods=['GET'])
    def api_info():
        """API information endpoint"""
        return jsonify({
            'service': 'Intelligent Analysis System API',
            'version': '2.0.0',
            'endpoints': {
                'health': '/health',
                'metrics': '/metrics',
                'docs': '/api/docs',
                'auth': '/api/auth/*',
                'analysis': '/api/analysis/*',
                'images': '/api/images/*',
                'similarity': '/api/similarity/*',
                'ai_detect': '/api/ai-detect/*',
                'chat': '/api/chat/*'
            },
            'features': [
                'JWT Authentication',
                'WebSocket Real-time Updates',
                'Celery Task Queue',
                'Rate Limiting per User',
                'RAGAS RAG Evaluation',
                'Prometheus Monitoring',
                'Model Versioning',
                'Swagger Documentation',
                'SSE Streaming'
            ],
            'documentation': '/api/docs'
        }), 200
    
    logger.info(f"Application initialized in {app.config['FLASK_ENV']} mode")
    logger.info("✅ JWT Authentication enabled")
    logger.info("✅ WebSocket support enabled")
    logger.info("✅ Rate limiting enabled")
    logger.info("✅ Prometheus metrics enabled")
    logger.info("✅ Swagger documentation available at /api/docs")
    logger.info("✅ Web interface available at /")
    
    return app, socketio


# Create app and socketio instances
app, socketio = create_app()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=Config.DEBUG
    )