"""
RAG Service (Retrieval-Augmented Generation)
Handles document indexing, retrieval, and context generation
"""
import logging
from typing import List, Dict, Any, Optional
from app.utils.cache import cached
from app.utils.text_utils import chunk_text, clean_text

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG Service using FAISS and txtai for retrieval
    Integrates with LLM for context-aware responses
    """
    
    def __init__(self, faiss_service=None, txtai_service=None, llm_service=None):
        """
        Initialize RAG service with vector stores and LLM
        
        Args:
            faiss_service: FAISS index service
            txtai_service: txtai semantic search service
            llm_service: LLM service for generation
        """
        self.faiss = faiss_service
        self.txtai = txtai_service
        self.llm = llm_service
        logger.info("RAG Service initialized")
    
    def index_document(self, document_id: str, text_chunks: List[str], 
                       metadata: Optional[Dict] = None) -> bool:
        """
        Index document chunks into vector stores
        
        Args:
            document_id: Unique document identifier
            text_chunks: List of text chunks to index
            metadata: Optional metadata for the document
        
        Returns:
            Success status
        """
        try:
            # Index in FAISS
            if self.faiss:
                self.faiss.add_documents(document_id, text_chunks, metadata)
            
            # Index in txtai
            if self.txtai:
                self.txtai.index_documents(document_id, text_chunks, metadata)
            
            logger.info(f"Document {document_id} indexed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {e}")
            return False
    
    def prepare_document_for_indexing(self, text: str, chunk_size: int = 512, 
                                     overlap: int = 50) -> List[str]:
        """
        Prepare document text for indexing by chunking
        
        Args:
            text: Document text
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        cleaned_text = clean_text(text)
        chunks = chunk_text(cleaned_text, chunk_size, overlap)
        return chunks
    
    @cached(expiration=3600, key_prefix="rag_retrieve")
    def retrieve_context(self, query: str, top_k: int = 5, 
                        document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query
        
        Args:
            query: Search query
            top_k: Number of results to return
            document_id: Optional filter by document ID
        
        Returns:
            List of relevant chunks with scores
        """
        results = []
        
        try:
            # Retrieve from FAISS (vector similarity)
            if self.faiss:
                faiss_results = self.faiss.search(query, top_k, document_id)
                results.extend(faiss_results)
            
            # Retrieve from txtai (semantic search)
            if self.txtai:
                txtai_results = self.txtai.search(query, top_k, document_id)
                results.extend(txtai_results)
            
            # Deduplicate and re-rank results
            results = self._deduplicate_results(results, top_k)
            
            logger.info(f"Retrieved {len(results)} context chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def generate_answer(self, query: str, context: List[str], 
                       max_tokens: int = 512) -> str:
        """
        Generate answer using LLM with retrieved context
        
        Args:
            query: User question
            context: Retrieved context chunks
            max_tokens: Maximum tokens for response
        
        Returns:
            Generated answer
        """
        if not self.llm:
            logger.warning("LLM service not available")
            return ""
        
        try:
            # Build prompt with context
            context_text = "\n\n".join(context)
            prompt = self._build_rag_prompt(query, context_text)
            
            # Generate response
            answer = self.llm.generate(prompt, max_tokens=max_tokens)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return ""
    
    def answer_question(self, question: str, document_id: Optional[str] = None,
                       top_k: int = 5, max_tokens: int = 512) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve context and generate answer
        
        Args:
            question: User question
            document_id: Optional document to search within
            top_k: Number of context chunks to retrieve
            max_tokens: Maximum tokens for response
        
        Returns:
            Dictionary with answer and sources
        """
        # Retrieve relevant context
        context_results = self.retrieve_context(question, top_k, document_id)
        
        # Extract text from results
        context_texts = [r['text'] for r in context_results]
        
        # Generate answer
        answer = self.generate_answer(question, context_texts, max_tokens)
        
        return {
            'question': question,
            'answer': answer,
            'sources': context_results,
            'context_used': len(context_results)
        }
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build RAG prompt for LLM"""
        prompt = f"""Context information is below:
---------------------
{context}
---------------------

Given the context information and not prior knowledge, answer the question.
If the answer is not in the context, say "I cannot answer based on the provided context."

Question: {query}
Answer:"""
        return prompt
    
    def _deduplicate_results(self, results: List[Dict], top_k: int) -> List[Dict]:
        """
        Deduplicate and re-rank results from multiple sources
        
        Args:
            results: Combined results from multiple retrievers
            top_k: Number of results to keep
        
        Returns:
            Deduplicated and ranked results
        """
        # Simple deduplication by text similarity
        seen_texts = set()
        unique_results = []
        
        for result in sorted(results, key=lambda x: x.get('score', 0), reverse=True):
            text = result.get('text', '')
            text_key = text[:100]  # Use first 100 chars as key
            
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_results.append(result)
            
            if len(unique_results) >= top_k:
                break
        
        return unique_results
    
    def get_document_summary(self, document_id: str, max_length: int = 500) -> str:
        """
        Generate summary of a document using RAG
        
        Args:
            document_id: Document identifier
            max_length: Maximum summary length
        
        Returns:
            Document summary
        """
        try:
            # Retrieve key chunks
            query = "Summarize the main points of this document"
            context_results = self.retrieve_context(query, top_k=10, document_id=document_id)
            
            if not context_results:
                return "No content available for summary"
            
            # Generate summary
            context_texts = [r['text'] for r in context_results]
            prompt = f"""Provide a concise summary of the following text excerpts in {max_length} characters or less:

{chr(10).join(context_texts)}

Summary:"""
            
            summary = self.generate_answer(prompt, context_texts, max_tokens=max_length // 4)
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""
