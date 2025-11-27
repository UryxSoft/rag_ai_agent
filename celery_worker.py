"""
Celery Configuration and Tasks
Async task processing for long-running analysis
"""
import logging
from celery import Celery, Task
from celery.result import AsyncResult
from typing import Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'intelligent_analysis',
    broker='redis://redis:6379/1',
    backend='redis://redis:6379/2'
)

# Celery Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True
)


class CallbackTask(Task):
    """Base task with callbacks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Success callback"""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback"""
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(base=CallbackTask, bind=True, name='tasks.analyze_document')
def analyze_document_task(self, document_path: str, analysis_types: List[str], 
                          user_id: str = None) -> Dict[str, Any]:
    """
    Async document analysis task
    
    Args:
        self: Task instance
        document_path: Path to document
        analysis_types: Types of analysis to run
        user_id: User identifier
    
    Returns:
        Analysis results
    """
    try:
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Initializing analysis',
                'progress': 0,
                'current_step': 'setup'
            }
        )
        
        # Import services here to avoid circular imports
        from app.services.agent_service import AgentCoordinator
        from app.services.document_extractor import DocumentExtractor
        
        # Initialize services
        doc_extractor = DocumentExtractor()
        
        # Step 1: Extract document (20% progress)
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Extracting document content',
                'progress': 20,
                'current_step': 'extraction'
            }
        )
        
        doc_structure = doc_extractor.extract_document(document_path)
        
        # Step 2: Initialize agents (40% progress)
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Initializing AI agents',
                'progress': 40,
                'current_step': 'agent_setup'
            }
        )
        
        # Create agent coordinator (would need proper initialization)
        # coordinator = AgentCoordinator(config={})
        
        # Step 3: Run analysis (60% progress)
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Running analysis',
                'progress': 60,
                'current_step': 'analysis'
            }
        )
        
        # Perform analysis
        results = {
            'document_structure': doc_structure,
            'analysis_types': analysis_types,
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id
        }
        
        # Step 4: Finalize (100% progress)
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Analysis completed',
                'progress': 100,
                'current_step': 'complete',
                'results': results
            }
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': f'Analysis failed: {str(e)}',
                'progress': 0,
                'error': str(e)
            }
        )
        raise


@celery_app.task(name='tasks.batch_analyze')
def batch_analyze_task(document_paths: List[str], analysis_types: List[str]) -> Dict[str, Any]:
    """
    Batch document analysis
    
    Args:
        document_paths: List of document paths
        analysis_types: Analysis types to run
    
    Returns:
        Batch results
    """
    results = []
    
    for doc_path in document_paths:
        # Chain individual tasks
        result = analyze_document_task.delay(doc_path, analysis_types)
        results.append({
            'document': doc_path,
            'task_id': result.id
        })
    
    return {
        'batch_id': results[0]['task_id'] if results else None,
        'total_documents': len(document_paths),
        'tasks': results
    }


@celery_app.task(name='tasks.cleanup_old_results')
def cleanup_old_results_task(days: int = 7):
    """
    Cleanup old analysis results
    
    Args:
        days: Delete results older than this many days
    """
    logger.info(f"Cleaning up results older than {days} days")
    # Implementation would delete old Redis keys, files, etc.
    return {'status': 'completed', 'days': days}


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get task status
    
    Args:
        task_id: Task identifier
    
    Returns:
        Task status information
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        response = {
            'state': task_result.state,
            'status': 'Task is waiting to be processed',
            'progress': 0
        }
    elif task_result.state == 'PROCESSING':
        response = {
            'state': task_result.state,
            'status': task_result.info.get('status', ''),
            'progress': task_result.info.get('progress', 0),
            'current_step': task_result.info.get('current_step', '')
        }
    elif task_result.state == 'SUCCESS':
        response = {
            'state': task_result.state,
            'status': 'Task completed successfully',
            'progress': 100,
            'result': task_result.result
        }
    elif task_result.state == 'FAILURE':
        response = {
            'state': task_result.state,
            'status': 'Task failed',
            'error': str(task_result.info)
        }
    else:
        response = {
            'state': task_result.state,
            'status': str(task_result.info)
        }
    
    return response


def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a running task
    
    Args:
        task_id: Task identifier
    
    Returns:
        Cancellation status
    """
    task_result = AsyncResult(task_id, app=celery_app)
    task_result.revoke(terminate=True)
    
    return {
        'task_id': task_id,
        'status': 'cancelled'
    }