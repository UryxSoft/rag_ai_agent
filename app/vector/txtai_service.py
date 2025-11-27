"""
txtai Service
Semantic search engine using txtai
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TxtaiService:
    """txtai-based semantic search service"""
    
    def __init__(self, index_path: str = None):
        """
        Initialize txtai service
        
        Args:
            index_path: Path to save/load index
        """
        self.index_path = Path(index_path) if index_path else None
        self.embeddings = None
        self._initialize()
    
    def _initialize(self):
        """Initialize txtai embeddings"""
        try:
            from txtai.embeddings import Embeddings
            
            self.embeddings = Embeddings({
                "path": "sentence-transformers/all-MiniLM-L6-v2",
                "content": True
            })
            
            # Load existing index if available
            if self.index_path and self.index_path.exists():
                self.embeddings.load(str(self.index_path))
                logger.info(f"txtai index loaded from {self.index_path}")
            else:
                logger.info("txtai embeddings initialized")
                
        except ImportError:
            logger.error("txtai not installed. Install with: pip install txtai")
            self.embeddings = None
        except Exception as e:
            logger.error(f"Error initializing txtai: {e}")
            self.embeddings = None
    
    def index_documents(self, document_id: str, texts: List[str], 
                       metadata: Optional[Dict] = None) -> bool:
        """Index documents"""
        if not self.embeddings:
            return False
        
        try:
            # Prepare documents for indexing
            documents = [
                {"id": f"{document_id}_{i}", "text": text, "document_id": document_id}
                for i, text in enumerate(texts)
            ]
            
            # Index
            self.embeddings.index(documents)
            
            # Save if path provided
            if self.index_path:
                self.embeddings.save(str(self.index_path))
            
            logger.info(f"Indexed {len(texts)} texts for {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing with txtai: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, 
              document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar texts"""
        if not self.embeddings:
            return []
        
        try:
            results = self.embeddings.search(query, top_k * 2)
            
            formatted = []
            for result in results:
                if document_id and result.get('document_id') != document_id:
                    continue
                
                formatted.append({
                    'text': result.get('text', ''),
                    'score': result.get('score', 0),
                    'document_id': result.get('document_id', '')
                })
                
                if len(formatted) >= top_k:
                    break
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error searching with txtai: {e}")
            return []
