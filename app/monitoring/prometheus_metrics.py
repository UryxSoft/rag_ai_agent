"""
Prometheus Monitoring Integration
Metrics collection and exposure
"""
import logging
import time
from functools import wraps
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry
)
from flask import Response, request

logger = logging.getLogger(__name__)

# Create registry
registry = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# Analysis metrics
ANALYSIS_COUNT = Counter(
    'analysis_total',
    'Total document analyses',
    ['analysis_type', 'status'],
    registry=registry
)

ANALYSIS_DURATION = Histogram(
    'analysis_duration_seconds',
    'Analysis duration in seconds',
    ['analysis_type'],
    registry=registry
)

# AI Model metrics
AI_DETECTION_COUNT = Counter(
    'ai_detection_total',
    'Total AI detections',
    ['model', 'classification'],
    registry=registry
)

AI_DETECTION_CONFIDENCE = Histogram(
    'ai_detection_confidence',
    'AI detection confidence scores',
    ['model'],
    registry=registry
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

# Vector store metrics
VECTOR_SEARCH_DURATION = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration',
    ['store_type'],
    registry=registry
)

VECTOR_SEARCH_RESULTS = Histogram(
    'vector_search_results_count',
    'Number of results from vector search',
    ['store_type'],
    registry=registry
)

# Task queue metrics
TASK_QUEUE_SIZE = Gauge(
    'task_queue_size',
    'Current task queue size',
    ['queue_name'],
    registry=registry
)

TASK_PROCESSING_TIME = Histogram(
    'task_processing_time_seconds',
    'Task processing time',
    ['task_type'],
    registry=registry
)

# System metrics
ACTIVE_USERS = Gauge(
    'active_users',
    'Currently active users',
    registry=registry
)

MODEL_LOAD_TIME = Histogram(
    'model_load_time_seconds',
    'Model load time',
    ['model_id', 'version'],
    registry=registry
)

# Application info
APP_INFO = Info(
    'app_info',
    'Application information',
    registry=registry
)

APP_INFO.info({
    'version': '2.0.0',
    'environment': 'production'
})


class MetricsManager:
    """Centralized metrics management"""
    
    @staticmethod
    def track_request():
        """Decorator to track HTTP requests"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                method = request.method
                endpoint = request.endpoint or 'unknown'
                
                # Track in-progress
                REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
                
                # Track duration
                start_time = time.time()
                
                try:
                    response = f(*args, **kwargs)
                    status = getattr(response, 'status_code', 200)
                    
                    # Track completion
                    REQUEST_COUNT.labels(
                        method=method,
                        endpoint=endpoint,
                        status=status
                    ).inc()
                    
                    return response
                    
                finally:
                    duration = time.time() - start_time
                    REQUEST_DURATION.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(duration)
                    
                    REQUEST_IN_PROGRESS.labels(
                        method=method,
                        endpoint=endpoint
                    ).dec()
            
            return wrapped
        return decorator
    
    @staticmethod
    def track_analysis(analysis_type: str):
        """Track analysis execution"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = f(*args, **kwargs)
                    status = 'success'
                    return result
                    
                except Exception as e:
                    status = 'error'
                    raise
                    
                finally:
                    duration = time.time() - start_time
                    
                    ANALYSIS_COUNT.labels(
                        analysis_type=analysis_type,
                        status=status
                    ).inc()
                    
                    ANALYSIS_DURATION.labels(
                        analysis_type=analysis_type
                    ).observe(duration)
            
            return wrapped
        return decorator
    
    @staticmethod
    def track_ai_detection(model: str, is_ai: bool, confidence: float):
        """Track AI detection result"""
        classification = 'ai' if is_ai else 'human'
        
        AI_DETECTION_COUNT.labels(
            model=model,
            classification=classification
        ).inc()
        
        AI_DETECTION_CONFIDENCE.labels(model=model).observe(confidence)
    
    @staticmethod
    def track_cache_access(cache_type: str, hit: bool):
        """Track cache hit/miss"""
        if hit:
            CACHE_HITS.labels(cache_type=cache_type).inc()
        else:
            CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    @staticmethod
    def track_vector_search(store_type: str, duration: float, result_count: int):
        """Track vector search"""
        VECTOR_SEARCH_DURATION.labels(store_type=store_type).observe(duration)
        VECTOR_SEARCH_RESULTS.labels(store_type=store_type).observe(result_count)
    
    @staticmethod
    def update_queue_size(queue_name: str, size: int):
        """Update task queue size"""
        TASK_QUEUE_SIZE.labels(queue_name=queue_name).set(size)
    
    @staticmethod
    def track_task_processing(task_type: str, duration: float):
        """Track task processing time"""
        TASK_PROCESSING_TIME.labels(task_type=task_type).observe(duration)
    
    @staticmethod
    def update_active_users(count: int):
        """Update active user count"""
        ACTIVE_USERS.set(count)
    
    @staticmethod
    def track_model_load(model_id: str, version: str, duration: float):
        """Track model loading time"""
        MODEL_LOAD_TIME.labels(model_id=model_id, version=version).observe(duration)


def metrics_endpoint():
    """Endpoint to expose Prometheus metrics"""
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


class PrometheusMiddleware:
    """Flask middleware for automatic request tracking"""
    
    def __init__(self, app=None):
        """Initialize middleware"""
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Add metrics endpoint
        app.add_url_rule('/metrics', 'metrics', metrics_endpoint)
        
        logger.info("Prometheus middleware initialized")
    
    def before_request(self):
        """Track request start"""
        request._prom_start_time = time.time()
        
        method = request.method
        endpoint = request.endpoint or 'unknown'
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    
    def after_request(self, response):
        """Track request completion"""
        if hasattr(request, '_prom_start_time'):
            duration = time.time() - request._prom_start_time
            method = request.method
            endpoint = request.endpoint or 'unknown'
            status = response.status_code
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            REQUEST_IN_PROGRESS.labels(
                method=method,
                endpoint=endpoint
            ).dec()
        
        return response