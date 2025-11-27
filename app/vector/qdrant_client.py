"""
Qdrant Client Service
Vector similarity search for images using Qdrant
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Qdrant vector database client for image similarity
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6333,
                 collection_name: str = 'xplagiax_images', use_grpc: bool = False):
        """
        Initialize Qdrant client
        
        Args:
            host: Qdrant host
            port: Qdrant port
            collection_name: Collection name for images
            use_grpc: Use gRPC instead of HTTP
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.use_grpc = use_grpc
        
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Qdrant client and collection"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # Initialize client
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                prefer_grpc=self.use_grpc
            )
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=512,  # Default image embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
            
        except ImportError:
            logger.error("qdrant-client not installed. Install with: pip install qdrant-client")
            self.client = None
        except Exception as e:
            logger.error(f"Error initializing Qdrant: {e}")
            self.client = None
    
    def add_image(self, image_id: str, embedding: np.ndarray, 
                 metadata: Optional[Dict] = None) -> bool:
        """
        Add image embedding to Qdrant
        
        Args:
            image_id: Unique image identifier
            embedding: Image embedding vector
            metadata: Optional metadata
        
        Returns:
            Success status
        """
        if not self.client:
            logger.warning("Qdrant client not initialized")
            return False
        
        try:
            from qdrant_client.models import PointStruct
            
            # Convert embedding to list
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            # Create point
            point = PointStruct(
                id=hash(image_id) & 0x7FFFFFFF,  # Ensure positive integer ID
                vector=embedding,
                payload={
                    'image_id': image_id,
                    **(metadata or {})
                }
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Added image {image_id} to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error adding image to Qdrant: {e}")
            return False
    
    def search_similar(self, query_embedding: np.ndarray, top_k: int = 5,
                      score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar images
        
        Args:
            query_embedding: Query image embedding
            top_k: Number of results to return
            score_threshold: Minimum similarity score
        
        Returns:
            List of similar images with scores
        """
        if not self.client:
            logger.warning("Qdrant client not initialized")
            return []
        
        try:
            # Convert embedding to list
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'image_id': result.payload.get('image_id'),
                    'score': result.score,
                    'metadata': result.payload
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []
    
    def delete_image(self, image_id: str) -> bool:
        """
        Delete image from Qdrant
        
        Args:
            image_id: Image identifier
        
        Returns:
            Success status
        """
        if not self.client:
            return False
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Delete by image_id
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="image_id",
                            match=MatchValue(value=image_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted image {image_id} from Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting image from Qdrant: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.client:
            return {'status': 'not_initialized'}
        
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                'collection_name': self.collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
            
        except Exception as e:
            logger.error(f"Error getting Qdrant stats: {e}")
            return {'status': 'error', 'error': str(e)}
