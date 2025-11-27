"""
Configuration Module for Intelligent Analysis System MVP
"""
import os
from pathlib import Path


class Config:
    """Base configuration for the Intelligent Analysis MVP."""
    
    # Environment
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # --- Database and Vector Services ---
    # OpenSearch/FAISS
    OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
    OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', 9200))
    OPENSEARCH_INDEX_DOCS = os.getenv('OPENSEARCH_INDEX_DOCS', 'xplagiax_documents')
    OPENSEARCH_USE_SSL = os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true'
    OPENSEARCH_VERIFY_CERTS = os.getenv('OPENSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
    
    # Qdrant (Images)
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
    QDRANT_COLLECTION_IMAGES = os.getenv('QDRANT_COLLECTION_IMAGES', 'xplagiax_images')
    QDRANT_USE_GRPC = os.getenv('QDRANT_USE_GRPC', 'false').lower() == 'true'
    
    # Redis (Cache)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    CACHE_EXPIRATION_SECONDS = int(os.getenv('CACHE_EXPIRATION_SECONDS', 3600))
    
    # --- AI Models Configuration (CPU-Only) ---
    # Base models directory
    MODELS_DIR = Path(os.getenv('MODELS_DIR', 'models'))
    
    # AI Text Detection (ModernBERT)
    MODERNBERT_MODEL_PATH = MODELS_DIR / 'modernbert.bin'
    MODERNBERT_MODEL2_PATH = MODELS_DIR / 'Model_groups_3class_seed12'
    MODERNBERT_MODEL3_PATH = MODELS_DIR / 'Model_groups_3class_seed22'
    
    # Phi-3 for RAG and Chat (GGUF/ONNX)
    PHI3_TEXT_MODEL_PATH = os.getenv(
        'PHI3_TEXT_MODEL_PATH', 
        str(MODELS_DIR / 'phi-3-mini-4k-instruct-Q4_K_M.gguf')
    )
    PHI3_MAX_TOKENS = int(os.getenv('PHI3_MAX_TOKENS', 2048))
    PHI3_TEMPERATURE = float(os.getenv('PHI3_TEMPERATURE', 0.7))
    PHI3_CONTEXT_LENGTH = int(os.getenv('PHI3_CONTEXT_LENGTH', 4096))
    
    # Embeddings (CPU Optimized - Sentence-Transformer)
    EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
    EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 384))
    EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', 32))
    
    # Image Detection (SigLIP CPU)
    IMAGE_MODEL_IDENTIFIER = os.getenv(
        'IMAGE_MODEL_IDENTIFIER', 
        'Ateeqq/ai-vs-human-image-detector'
    )
    IMAGE_EMBEDDING_DIMENSION = int(os.getenv('IMAGE_EMBEDDING_DIMENSION', 512))
    
    # --- FAISS Configuration ---
    FAISS_INDEX_PATH = MODELS_DIR / 'faiss_index.bin'
    FAISS_USE_IVF = os.getenv('FAISS_USE_IVF', 'true').lower() == 'true'
    FAISS_NLIST = int(os.getenv('FAISS_NLIST', 100))
    FAISS_NPROBE = int(os.getenv('FAISS_NPROBE', 10))
    
    # --- txtai Configuration ---
    TXTAI_INDEX_PATH = MODELS_DIR / 'txtai_index'
    
    # --- CrewAI / mem0 ---
    MEM0_API_KEY = os.getenv('MEM0_API_KEY', 'mem0-mock-key')
    MEM0_API_URL = os.getenv('MEM0_API_URL', 'http://localhost:8080')
    MEM0_ENABLED = os.getenv('MEM0_ENABLED', 'true').lower() == 'true'
    
    # --- File Storage ---
    UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', '/mnt/user-data/uploads'))
    OUTPUT_FOLDER = Path(os.getenv('OUTPUT_FOLDER', '/mnt/user-data/outputs'))
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 
        'epub', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'webp'
    }
    
    # --- MinIO Configuration ---
    MINIO_ENABLED = os.getenv('MINIO_ENABLED', 'false').lower() == 'true'
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_BUCKET_DOCUMENTS = os.getenv('MINIO_BUCKET_DOCUMENTS', 'documents')
    MINIO_BUCKET_IMAGES = os.getenv('MINIO_BUCKET_IMAGES', 'images')
    MINIO_USE_SSL = os.getenv('MINIO_USE_SSL', 'false').lower() == 'true'
    
    # --- API Security ---
    API_KEY = os.getenv('API_KEY', 'SECURE_AND_COMPLEX_API_KEY_100M_MVP')
    REQUIRE_API_KEY = os.getenv('REQUIRE_API_KEY', 'true').lower() == 'true'
    
    # --- Processing Configuration ---
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 10))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 300))  # 5 minutes
    
    # --- Batch Processing ---
    BATCH_SIZE_TEXT = int(os.getenv('BATCH_SIZE_TEXT', 32))
    BATCH_SIZE_IMAGES = int(os.getenv('BATCH_SIZE_IMAGES', 16))
    
    # --- Logging ---
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    @staticmethod
    def init_app():
        """Initialize application directories and validate configuration."""
        # Create necessary directories
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Validate critical paths in production
        if Config.FLASK_ENV == 'production':
            if not Config.PHI3_TEXT_MODEL_PATH:
                raise ValueError("PHI3_TEXT_MODEL_PATH must be set in production")
        
        print(f"✓ Configuration initialized for {Config.FLASK_ENV} environment")
    
    @staticmethod
    def validate():
        """Validate configuration and external services."""
        issues = []
        
        # Check model files existence (warning only in dev)
        if Config.FLASK_ENV != 'development':
            if not Path(Config.PHI3_TEXT_MODEL_PATH).exists():
                issues.append(f"Phi-3 model not found at {Config.PHI3_TEXT_MODEL_PATH}")
        
        if issues:
            warning_msg = "\n".join(issues)
            print(f"⚠️  Configuration warnings:\n{warning_msg}")
        
        return len(issues) == 0


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    @staticmethod
    def init_app():
        Config.init_app()
        # Additional production-specific initialization
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format=Config.LOG_FORMAT,
            filename=Config.LOG_FILE
        )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
