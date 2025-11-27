"""
Model Versioning System
Manage multiple versions of AI models
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ModelVersion:
    """Model version metadata"""
    model_id: str
    version: str
    model_type: str  # 'text_detector', 'image_detector', 'llm', 'embeddings'
    path: str
    created_at: str
    metrics: Dict[str, float]
    is_active: bool = False
    description: str = ""
    tags: List[str] = None


class ModelRegistry:
    """Central registry for model versions"""
    
    def __init__(self, registry_path: str = 'models/registry.json'):
        """
        Initialize model registry
        
        Args:
            registry_path: Path to registry file
        """
        self.registry_path = Path(registry_path)
        self.models = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from disk"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    for model_id, versions in data.items():
                        self.models[model_id] = [
                            ModelVersion(**v) for v in versions
                        ]
                logger.info(f"Loaded {len(self.models)} models from registry")
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
                self.models = {}
        else:
            logger.info("No existing registry found, starting fresh")
    
    def _save_registry(self):
        """Save registry to disk"""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for model_id, versions in self.models.items():
                data[model_id] = [asdict(v) for v in versions]
            
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Registry saved successfully")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_model(self, model_version: ModelVersion) -> bool:
        """
        Register new model version
        
        Args:
            model_version: Model version to register
        
        Returns:
            Success status
        """
        model_id = model_version.model_id
        
        if model_id not in self.models:
            self.models[model_id] = []
        
        # Check if version already exists
        existing = self.get_version(model_id, model_version.version)
        if existing:
            logger.warning(f"Version {model_version.version} already exists for {model_id}")
            return False
        
        self.models[model_id].append(model_version)
        self._save_registry()
        
        logger.info(f"Registered {model_id} v{model_version.version}")
        return True
    
    def get_version(self, model_id: str, version: str) -> Optional[ModelVersion]:
        """Get specific model version"""
        if model_id not in self.models:
            return None
        
        for model in self.models[model_id]:
            if model.version == version:
                return model
        
        return None
    
    def get_active_version(self, model_id: str) -> Optional[ModelVersion]:
        """Get active version for model"""
        if model_id not in self.models:
            return None
        
        for model in self.models[model_id]:
            if model.is_active:
                return model
        
        # Return latest if no active set
        if self.models[model_id]:
            return self.models[model_id][-1]
        
        return None
    
    def set_active_version(self, model_id: str, version: str) -> bool:
        """Set active version for model"""
        if model_id not in self.models:
            return False
        
        # Deactivate all versions
        for model in self.models[model_id]:
            model.is_active = False
        
        # Activate specified version
        target = self.get_version(model_id, version)
        if target:
            target.is_active = True
            self._save_registry()
            logger.info(f"Set {model_id} v{version} as active")
            return True
        
        return False
    
    def list_versions(self, model_id: str) -> List[ModelVersion]:
        """List all versions for model"""
        return self.models.get(model_id, [])
    
    def list_all_models(self) -> Dict[str, List[ModelVersion]]:
        """List all models and versions"""
        return self.models
    
    def delete_version(self, model_id: str, version: str) -> bool:
        """Delete model version"""
        if model_id not in self.models:
            return False
        
        target = self.get_version(model_id, version)
        if target:
            self.models[model_id].remove(target)
            self._save_registry()
            logger.info(f"Deleted {model_id} v{version}")
            return True
        
        return False
    
    def compare_versions(self, model_id: str, version1: str, 
                        version2: str) -> Dict[str, Any]:
        """Compare two model versions"""
        v1 = self.get_version(model_id, version1)
        v2 = self.get_version(model_id, version2)
        
        if not v1 or not v2:
            return {'error': 'Version not found'}
        
        comparison = {
            'model_id': model_id,
            'version1': version1,
            'version2': version2,
            'metrics_diff': {}
        }
        
        # Compare metrics
        for metric in set(list(v1.metrics.keys()) + list(v2.metrics.keys())):
            val1 = v1.metrics.get(metric, 0)
            val2 = v2.metrics.get(metric, 0)
            comparison['metrics_diff'][metric] = {
                'version1': val1,
                'version2': val2,
                'diff': val2 - val1,
                'percent_change': ((val2 - val1) / val1 * 100) if val1 != 0 else 0
            }
        
        return comparison


class ModelLoader:
    """Load models with versioning support"""
    
    def __init__(self, registry: ModelRegistry):
        """
        Initialize model loader
        
        Args:
            registry: Model registry instance
        """
        self.registry = registry
        self.loaded_models = {}
    
    def load_model(self, model_id: str, version: str = None) -> Any:
        """
        Load model by ID and version
        
        Args:
            model_id: Model identifier
            version: Model version (uses active if not specified)
        
        Returns:
            Loaded model
        """
        if version:
            model_version = self.registry.get_version(model_id, version)
        else:
            model_version = self.registry.get_active_version(model_id)
        
        if not model_version:
            raise ValueError(f"Model {model_id} v{version} not found")
        
        # Check if already loaded
        cache_key = f"{model_id}:{model_version.version}"
        if cache_key in self.loaded_models:
            logger.info(f"Using cached model {cache_key}")
            return self.loaded_models[cache_key]
        
        # Load model based on type
        model = self._load_model_file(model_version)
        
        # Cache loaded model
        self.loaded_models[cache_key] = model
        
        logger.info(f"Loaded model {cache_key}")
        return model
    
    def _load_model_file(self, model_version: ModelVersion) -> Any:
        """Load model from file"""
        # Implementation would depend on model type
        # This is a placeholder
        logger.info(f"Loading model from {model_version.path}")
        
        # Return mock model for now
        return {
            'model_id': model_version.model_id,
            'version': model_version.version,
            'path': model_version.path
        }
    
    def unload_model(self, model_id: str, version: str = None):
        """Unload model from memory"""
        if version:
            cache_key = f"{model_id}:{version}"
        else:
            # Find any loaded version
            cache_key = next(
                (k for k in self.loaded_models if k.startswith(f"{model_id}:")),
                None
            )
        
        if cache_key and cache_key in self.loaded_models:
            del self.loaded_models[cache_key]
            logger.info(f"Unloaded model {cache_key}")


# Global registry instance
model_registry = ModelRegistry()
model_loader = ModelLoader(model_registry)


# Register default models
def register_default_models():
    """Register default model versions"""
    
    # AI Text Detector
    model_registry.register_model(ModelVersion(
        model_id='ai_text_detector',
        version='1.0.0',
        model_type='text_detector',
        path='models/modernbert.bin',
        created_at=datetime.utcnow().isoformat(),
        metrics={'accuracy': 0.92, 'precision': 0.89, 'recall': 0.91},
        is_active=True,
        description='ModernBERT-based AI text detector',
        tags=['text', 'ai-detection', 'production']
    ))
    
    # Phi-3 LLM
    model_registry.register_model(ModelVersion(
        model_id='phi3_llm',
        version='4k-q4',
        model_type='llm',
        path='models/phi-3-mini-4k-instruct-Q4_K_M.gguf',
        created_at=datetime.utcnow().isoformat(),
        metrics={'perplexity': 12.5, 'generation_speed': 25.3},
        is_active=True,
        description='Phi-3 Mini 4K context, Q4 quantization',
        tags=['llm', 'gguf', 'cpu-optimized']
    ))
    
    # Embeddings Model
    model_registry.register_model(ModelVersion(
        model_id='embeddings',
        version='minilm-l6-v2',
        model_type='embeddings',
        path='sentence-transformers/all-MiniLM-L6-v2',
        created_at=datetime.utcnow().isoformat(),
        metrics={'embedding_dimension': 384, 'speed_ms': 15.2},
        is_active=True,
        description='All-MiniLM-L6-v2 sentence embeddings',
        tags=['embeddings', 'sentence-transformers']
    ))


# Initialize default models
register_default_models()