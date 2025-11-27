"""
Server-Sent Events (SSE) Support
Streaming responses for chat
"""
import logging
import json
import time
from flask import Response, stream_with_context
from typing import Generator, Dict, Any
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class SSEManager:
    """Manage Server-Sent Events streaming"""
    
    @staticmethod
    def create_sse_response(data: Dict[str, Any]) -> str:
        """
        Format data as SSE message
        
        Args:
            data: Data to send
        
        Returns:
            Formatted SSE message
        """
        return f"data: {json.dumps(data)}\n\n"
    
    @staticmethod
    def stream_generator(generator_func) -> Generator:
        """
        Wrap generator function for SSE streaming
        
        Args:
            generator_func: Generator function that yields data
        
        Yields:
            SSE-formatted messages
        """
        try:
            for data in generator_func():
                yield SSEManager.create_sse_response(data)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield SSEManager.create_sse_response({
                'error': str(e),
                'type': 'error'
            })
    
    @staticmethod
    def create_stream_response(generator) -> Response:
        """
        Create Flask Response for SSE streaming
        
        Args:
            generator: Data generator
        
        Returns:
            Flask Response object
        """
        return Response(
            stream_with_context(SSEManager.stream_generator(generator)),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )


class ChatStreamManager:
    """Manage chat response streaming"""
    
    def __init__(self, llm_service=None):
        """Initialize chat stream manager"""
        self.llm_service = llm_service
    
    def stream_chat_response(self, question: str, context: str,
                            memory_id: str = None) -> Generator:
        """
        Stream chat response word by word
        
        Args:
            question: User question
            context: Context for answer
            memory_id: Memory ID for context
        
        Yields:
            Response chunks
        """
        # Send start event
        yield {
            'type': 'start',
            'message': 'Generating response...',
            'memory_id': memory_id
        }
        
        # Generate response (mock implementation)
        response_text = self._generate_response(question, context)
        
        # Stream word by word
        words = response_text.split()
        for i, word in enumerate(words):
            yield {
                'type': 'token',
                'content': word + ' ',
                'index': i
            }
            time.sleep(0.05)  # Simulate streaming delay
        
        # Send end event
        yield {
            'type': 'end',
            'message': 'Response complete',
            'full_response': response_text
        }
    
    def stream_analysis_progress(self, task_id: str) -> Generator:
        """
        Stream analysis progress
        
        Args:
            task_id: Task identifier
        
        Yields:
            Progress updates
        """
        from celery_worker import get_task_status
        
        while True:
            status = get_task_status(task_id)
            
            yield {
                'type': 'progress',
                'task_id': task_id,
                'state': status['state'],
                'progress': status.get('progress', 0),
                'status': status.get('status', ''),
                'current_step': status.get('current_step', '')
            }
            
            # Check if complete
            if status['state'] in ['SUCCESS', 'FAILURE']:
                break
            
            time.sleep(1)  # Poll every second
    
    def _generate_response(self, question: str, context: str) -> str:
        """Generate response (would use actual LLM)"""
        if self.llm_service:
            # Use actual LLM service
            prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
            return self.llm_service.generate(prompt)
        else:
            # Mock response
            return f"Based on the context provided, here's an answer to your question: {question}. This is a mock response that would be replaced with actual LLM generation in production."


class EventQueue:
    """Thread-safe event queue for SSE"""
    
    def __init__(self):
        """Initialize event queue"""
        self.queues = {}
    
    def create_queue(self, session_id: str) -> Queue:
        """Create queue for session"""
        queue = Queue()
        self.queues[session_id] = queue
        return queue
    
    def get_queue(self, session_id: str) -> Queue:
        """Get queue for session"""
        return self.queues.get(session_id)
    
    def remove_queue(self, session_id: str):
        """Remove queue for session"""
        if session_id in self.queues:
            del self.queues[session_id]
    
    def send_event(self, session_id: str, event: Dict[str, Any]):
        """Send event to session queue"""
        queue = self.get_queue(session_id)
        if queue:
            queue.put(event)
    
    def stream_events(self, session_id: str, timeout: int = 30) -> Generator:
        """
        Stream events from queue
        
        Args:
            session_id: Session identifier
            timeout: Timeout in seconds
        
        Yields:
            Events from queue
        """
        queue = self.get_queue(session_id)
        if not queue:
            return
        
        start_time = time.time()
        
        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                yield {
                    'type': 'timeout',
                    'message': 'Connection timeout'
                }
                break
            
            try:
                # Get event with short timeout to check for disconnection
                event = queue.get(timeout=1)
                yield event
                
                # Check for end event
                if event.get('type') == 'end':
                    break
                    
            except Empty:
                # Send keep-alive
                yield {
                    'type': 'keepalive',
                    'timestamp': time.time()
                }


# Global event queue instance
event_queue = EventQueue()


def stream_chat(question: str, context: str, memory_id: str = None,
                llm_service=None) -> Response:
    """
    Create streaming chat response
    
    Args:
        question: User question
        context: Context for answer
        memory_id: Memory ID
        llm_service: LLM service instance
    
    Returns:
        Streaming response
    """
    manager = ChatStreamManager(llm_service)
    generator = manager.stream_chat_response(question, context, memory_id)
    return SSEManager.create_stream_response(lambda: generator)


def stream_progress(task_id: str) -> Response:
    """
    Create streaming progress response
    
    Args:
        task_id: Task identifier
    
    Returns:
        Streaming response
    """
    manager = ChatStreamManager()
    generator = manager.stream_analysis_progress(task_id)
    return SSEManager.create_stream_response(lambda: generator)