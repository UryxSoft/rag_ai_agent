"""
LLM Model Loader
Handles loading and inference with Phi-3 models (GGUF/ONNX)
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class Phi3Model:
    """
    Phi-3 Model wrapper for GGUF/ONNX formats
    CPU-optimized inference
    """
    
    def __init__(self, model_path: str, max_tokens: int = 2048, 
                 temperature: float = 0.7, context_length: int = 4096):
        """
        Initialize Phi-3 model
        
        Args:
            model_path: Path to model file (.gguf or .onnx)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            context_length: Maximum context length
        """
        self.model_path = Path(model_path)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.context_length = context_length
        self.model = None
        self.tokenizer = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the model based on file extension"""
        try:
            if not self.model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                logger.info("Running in mock mode for development")
                self.model = None
                return
            
            extension = self.model_path.suffix.lower()
            
            if extension == '.gguf':
                self._load_gguf_model()
            elif extension == '.onnx':
                self._load_onnx_model()
            else:
                logger.warning(f"Unsupported model format: {extension}")
                self.model = None
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
    
    def _load_gguf_model(self):
        """Load GGUF model using llama-cpp-python"""
        try:
            from llama_cpp import Llama
            
            logger.info(f"Loading GGUF model from {self.model_path}")
            
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.context_length,
                n_batch=512,
                n_threads=4,  # CPU threads
                verbose=False
            )
            
            logger.info("GGUF model loaded successfully")
            
        except ImportError:
            logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading GGUF model: {e}")
            self.model = None
    
    def _load_onnx_model(self):
        """Load ONNX model using onnxruntime"""
        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
            
            logger.info(f"Loading ONNX model from {self.model_path}")
            
            # Initialize ONNX runtime session
            self.model = ort.InferenceSession(
                str(self.model_path),
                providers=['CPUExecutionProvider']
            )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
            
            logger.info("ONNX model loaded successfully")
            
        except ImportError:
            logger.error("Required packages not installed. Install with: pip install onnxruntime transformers")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading ONNX model: {e}")
            self.model = None
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None,
                temperature: Optional[float] = None, **kwargs) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (overrides default)
            temperature: Sampling temperature (overrides default)
            **kwargs: Additional generation parameters
        
        Returns:
            Generated text
        """
        if not self.model:
            # Mock response for development
            return self._mock_generate(prompt)
        
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        try:
            if isinstance(self.model, object) and hasattr(self.model, '__call__'):
                # GGUF model (llama-cpp)
                response = self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["</s>", "\n\n\n"],
                    **kwargs
                )
                return response['choices'][0]['text'].strip()
            else:
                # ONNX model
                return self._generate_onnx(prompt, max_tokens, temperature)
                
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return ""
    
    def _generate_onnx(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using ONNX model"""
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="np")
            
            # Run inference
            # Note: Actual ONNX inference would require more complex implementation
            # This is a simplified version
            logger.warning("ONNX generation not fully implemented")
            return self._mock_generate(prompt)
            
        except Exception as e:
            logger.error(f"Error in ONNX generation: {e}")
            return ""
    
    def _mock_generate(self, prompt: str) -> str:
        """Generate mock response for development"""
        logger.debug("Using mock generation (model not loaded)")
        
        # Simple mock responses based on prompt keywords
        prompt_lower = prompt.lower()
        
        if 'summary' in prompt_lower or 'summarize' in prompt_lower:
            return "This document discusses important topics and presents key findings. The main points are well-structured and the content is comprehensive."
        elif 'insight' in prompt_lower or 'analyze' in prompt_lower:
            return "Key insights: The document shows strong organization and clear arguments. Potential areas of concern include similarity with existing content."
        elif 'question' in prompt_lower or 'answer' in prompt_lower:
            return "Based on the provided context, the answer appears to relate to the main themes discussed in the document."
        else:
            return "The analysis indicates significant findings that warrant further review."
    
    def chat(self, messages: list, max_tokens: Optional[int] = None) -> str:
        """
        Chat-style generation with message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated response
        """
        # Format messages into a single prompt
        prompt = self._format_chat_prompt(messages)
        return self.generate(prompt, max_tokens)
    
    def _format_chat_prompt(self, messages: list) -> str:
        """Format chat messages into prompt"""
        formatted = []
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                formatted.append(f"System: {content}")
            elif role == 'user':
                formatted.append(f"User: {content}")
            elif role == 'assistant':
                formatted.append(f"Assistant: {content}")
        
        formatted.append("Assistant:")
        return "\n\n".join(formatted)
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None


class LLMService:
    """
    High-level LLM service
    Manages model lifecycle and provides convenient methods
    """
    
    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM service
        
        Args:
            model_path: Path to model file
            config: Optional configuration
        """
        config = config or {}
        
        self.model = Phi3Model(
            model_path=model_path,
            max_tokens=config.get('max_tokens', 2048),
            temperature=config.get('temperature', 0.7),
            context_length=config.get('context_length', 4096)
        )
        
        logger.info("LLM Service initialized")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        return self.model.generate(prompt, **kwargs)
    
    def chat(self, messages: list, **kwargs) -> str:
        """Chat-style generation"""
        return self.model.chat(messages, **kwargs)
    
    def is_available(self) -> bool:
        """Check if LLM is available"""
        return self.model.is_loaded()
