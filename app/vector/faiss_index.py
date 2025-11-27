"""
FAISS Index Service
Vector similarity search using FAISS
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


class FAISSService:
    """
    FAISS-based vector similarity search
    CPU-optimized with IVF indexing
    """
    
    def __init__(self, index_path: str = None, dimension: int = 384, 
                 use_ivf: bool = True, nlist: int = 100):
        """
        Initialize FAISS service
        
        Args:
            index_path: Path to save/load index
            dimension: Embedding dimension
            use_ivf: Use IVF (Inverted File) index for faster search
            nlist: Number of clusters for IVF
        """
        self.index_path = Path(index_path) if index_path else None
        self.dimension = dimension
        self.use_ivf = use_ivf
        self.nlist = nlist
        
        self.index = None
        self.embeddings_model = None
        self.document_map = {}  # Maps index positions to document IDs
        
        self._initialize()
    
    def _initialize(self):
        """Initialize FAISS index and embeddings model"""
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
            
            # Load embeddings model
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embeddings model loaded")
            
            # Try to load existing index
            if self.index_path and self.index_path.exists():
                self._load_index()
            else:
                # Create new index
                if self.use_ivf:
                    # IVF index for faster search on large datasets
                    quantizer = faiss.IndexFlatL2(self.dimension)
                    self.index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
                    logger.info(f"Created IVF FAISS index (nlist={self.nlist})")
                else:
                    # Flat index for smaller datasets
                    self.index = faiss.IndexFlatL2(self.dimension)
                    logger.info("Created Flat FAISS index")
            
        except ImportError as e:
            logger.error(f"FAISS or sentence-transformers not installed: {e}")
            self.index = None
        except Exception as e:
            logger.error(f"Error initializing FAISS: {e}")
            self.index = None
    
    def add_documents(self, document_id: str, texts: List[str], 
                     metadata: Optional[Dict] = None) -> bool:
        """
        Add documents to the index
        
        Args:
            document_id: Document identifier
            texts: List of text chunks to index
            metadata: Optional metadata
        
        Returns:
            Success status
        """
        if not self.index or not self.embeddings_model:
            logger.warning("FAISS not initialized")
            return False
        
        try:
            # Generate embeddings
            embeddings = self.embeddings_model.encode(texts, show_progress_bar=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Train index if using IVF and not trained
            if self.use_ivf and not self.index.is_trained:
                logger.info("Training IVF index...")
                self.index.train(embeddings)
            
            # Get current index size for mapping
            start_idx = self.index.ntotal
            
            # Add to index
            self.index.add(embeddings)
            
            # Update document map
            for i, text in enumerate(texts):
                self.document_map[start_idx + i] = {
                    'document_id': document_id,
                    'text': text,
                    'metadata': metadata or {}
                }
            
            logger.info(f"Added {len(texts)} chunks for document {document_id}")
            
            # Save index
            if self.index_path:
                self._save_index()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to FAISS: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, 
              document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar texts
        
        Args:
            query: Search query
            top_k: Number of results to return
            document_id: Optional filter by document ID
        
        Returns:
            List of results with scores and metadata
        """
        if not self.index or not self.embeddings_model:
            logger.warning("FAISS not initialized")
            return []
        
        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_model.encode([query], show_progress_bar=False)
            query_embedding = np.array(query_embedding).astype('float32')
            
            # Search
            distances, indices = self.index.search(query_embedding, top_k * 2)  # Get more for filtering
            
            # Format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                doc_info = self.document_map.get(idx)
                if not doc_info:
                    continue
                
                # Filter by document_id if specified
                if document_id and doc_info['document_id'] != document_id:
                    continue
                
                results.append({
                    'text': doc_info['text'],
                    'document_id': doc_info['document_id'],
                    'score': float(dist),
                    'metadata': doc_info.get('metadata', {})
                })
                
                if len(results) >= top_k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS: {e}")
            return []
    
    def _save_index(self):
        """Save index and document map to disk"""
        if not self.index_path:
            return
        
        try:
            import faiss
            
            # Ensure directory exists
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save document map
            map_path = self.index_path.with_suffix('.pkl')
            with open(map_path, 'wb') as f:
                pickle.dump(self.document_map, f)
            
            logger.info(f"FAISS index saved to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def _load_index(self):
        """Load index and document map from disk"""
        try:
            import faiss
            
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load document map
            map_path = self.index_path.with_suffix('.pkl')
            if map_path.exists():
                with open(map_path, 'rb') as f:
                    self.document_map = pickle.load(f)
            
            logger.info(f"FAISS index loaded from {self.index_path}")
            logger.info(f"Index contains {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            self.index = None
    
    def clear(self):
        """Clear the index"""
        if self.index:
            self.index.reset()
            self.document_map.clear()
            logger.info("FAISS index cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.index:
            return {'status': 'not_initialized'}
        
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': 'IVF' if self.use_ivf else 'Flat',
            'documents': len(set(info['document_id'] for info in self.document_map.values()))
        }
