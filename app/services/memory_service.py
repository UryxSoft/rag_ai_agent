"""
Memory Service using mem0
Manages persistent memory for document analysis and chat
"""
import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Memory management service using mem0
    Stores and retrieves analysis memories for context-aware chat
    """
    
    def __init__(self, api_url: str = None, api_key: str = None, enabled: bool = True):
        """
        Initialize memory service
        
        Args:
            api_url: mem0 API URL
            api_key: mem0 API key
            enabled: Whether memory is enabled
        """
        self.api_url = api_url
        self.api_key = api_key
        self.enabled = enabled
        
        # In-memory storage for MVP (replace with actual mem0 integration)
        self._memory_store = {}
        
        logger.info(f"Memory Service initialized (enabled: {enabled})")
    
    def create_memory(self, document_id: str, analysis_results: Dict[str, Any],
                     metadata: Optional[Dict] = None) -> str:
        """
        Create a new memory from analysis results
        
        Args:
            document_id: Document identifier
            analysis_results: Complete analysis results
            metadata: Optional metadata
        
        Returns:
            Memory ID
        """
        try:
            # Generate unique memory ID
            memory_id = f"mem_{uuid.uuid4().hex[:12]}"
            
            # Structure memory data
            memory_data = {
                'memory_id': memory_id,
                'document_id': document_id,
                'created_at': datetime.utcnow().isoformat(),
                'analysis_results': analysis_results,
                'metadata': metadata or {},
                'chat_history': []
            }
            
            # Store memory
            self._memory_store[memory_id] = memory_data
            
            logger.info(f"Memory created: {memory_id} for document {document_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            return ""
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve memory by ID
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            Memory data or None if not found
        """
        if not self.enabled:
            return None
        
        memory = self._memory_store.get(memory_id)
        
        if not memory:
            logger.warning(f"Memory not found: {memory_id}")
            return None
        
        return memory
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing memory
        
        Args:
            memory_id: Memory identifier
            updates: Updates to apply
        
        Returns:
            Success status
        """
        if not self.enabled:
            return False
        
        try:
            if memory_id not in self._memory_store:
                logger.warning(f"Memory not found for update: {memory_id}")
                return False
            
            # Update memory
            self._memory_store[memory_id].update(updates)
            self._memory_store[memory_id]['updated_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Memory updated: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False
    
    def add_chat_interaction(self, memory_id: str, question: str, 
                            answer: str, context: List[str] = None) -> bool:
        """
        Add chat interaction to memory
        
        Args:
            memory_id: Memory identifier
            question: User question
            answer: System answer
            context: Context used for answer
        
        Returns:
            Success status
        """
        if not self.enabled:
            return False
        
        try:
            memory = self.get_memory(memory_id)
            if not memory:
                return False
            
            # Create interaction record
            interaction = {
                'timestamp': datetime.utcnow().isoformat(),
                'question': question,
                'answer': answer,
                'context': context or []
            }
            
            # Add to chat history
            memory['chat_history'].append(interaction)
            
            # Update memory
            return self.update_memory(memory_id, {'chat_history': memory['chat_history']})
            
        except Exception as e:
            logger.error(f"Error adding chat interaction: {e}")
            return False
    
    def get_chat_history(self, memory_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get chat history for a memory
        
        Args:
            memory_id: Memory identifier
            limit: Maximum number of interactions to return
        
        Returns:
            List of chat interactions
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return []
        
        chat_history = memory.get('chat_history', [])
        return chat_history[-limit:] if limit else chat_history
    
    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories by query
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching memories
        """
        if not self.enabled:
            return []
        
        # Simple keyword search (replace with semantic search in production)
        query_lower = query.lower()
        matching_memories = []
        
        for memory_id, memory in self._memory_store.items():
            # Search in document content
            analysis = memory.get('analysis_results', {})
            doc_analysis = analysis.get('document_analysis', {})
            
            # Convert to string for searching
            memory_text = json.dumps(doc_analysis).lower()
            
            if query_lower in memory_text:
                matching_memories.append({
                    'memory_id': memory_id,
                    'document_id': memory.get('document_id'),
                    'created_at': memory.get('created_at'),
                    'metadata': memory.get('metadata', {})
                })
            
            if len(matching_memories) >= limit:
                break
        
        return matching_memories
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            Success status
        """
        if not self.enabled:
            return False
        
        try:
            if memory_id in self._memory_store:
                del self._memory_store[memory_id]
                logger.info(f"Memory deleted: {memory_id}")
                return True
            
            logger.warning(f"Memory not found for deletion: {memory_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    def get_context_for_chat(self, memory_id: str) -> str:
        """
        Get formatted context for chat from memory
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            Formatted context string
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return ""
        
        # Extract key information
        analysis = memory.get('analysis_results', {})
        
        context_parts = []
        
        # Document info
        if 'document_analysis' in analysis:
            doc = analysis['document_analysis']
            context_parts.append(f"Document: {doc.get('page_count', 0)} pages")
        
        # Similarity findings
        if 'similarity' in analysis:
            sim = analysis['similarity']
            context_parts.append(f"Similarity matches: {sim.get('total_matches', 0)}")
        
        # AI detection findings
        if 'ai_detection' in analysis:
            ai = analysis['ai_detection']
            context_parts.append(
                f"AI Detection: {ai.get('overall_classification', 'Unknown')} "
                f"({ai.get('average_confidence', 0):.1f}% confidence)"
            )
        
        # Insights
        if 'insights' in analysis:
            insights = analysis['insights']
            if 'insights' in insights:
                context_parts.append(f"Key Insights: {insights['insights']}")
        
        return "\n".join(context_parts)
    
    def list_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all memories
        
        Args:
            limit: Maximum number of memories to return
        
        Returns:
            List of memory summaries
        """
        if not self.enabled:
            return []
        
        memories = []
        for memory_id, memory in list(self._memory_store.items())[:limit]:
            memories.append({
                'memory_id': memory_id,
                'document_id': memory.get('document_id'),
                'created_at': memory.get('created_at'),
                'chat_count': len(memory.get('chat_history', [])),
                'metadata': memory.get('metadata', {})
            })
        
        return memories
