"""Chat Routes - Post-Analysis Q&A"""
import logging
from flask import Blueprint, request
from app.middleware.auth_middleware import require_api_key
from app.utils.response_formatter import success_response, error_response

logger = logging.getLogger(__name__)
bp = Blueprint('chat', __name__)


@bp.route('/message', methods=['POST'])
@require_api_key
def send_message():
    """
    Send message in context of analyzed document
    
    POST /api/chat/message
    JSON: {
        "memory_id": "mem_xxxx",
        "question": "What are the main findings?"
    }
    """
    try:
        data = request.get_json()
        memory_id = data.get('memory_id')
        question = data.get('question')
        
        if not memory_id or not question:
            return error_response('memory_id and question required', status_code=400)
        
        # TODO: Integrate with memory_service and RAG
        return success_response(data={
            'answer': 'This is a mock answer',
            'sources': [],
            'memory_id': memory_id
        })
        
    except Exception as e:
        return error_response(str(e), status_code=500)


@bp.route('/history/<memory_id>', methods=['GET'])
@require_api_key
def get_chat_history(memory_id):
    """Get chat history for a memory"""
    try:
        # TODO: Integrate with memory_service
        return success_response(data={'history': [], 'memory_id': memory_id})
        
    except Exception as e:
        return error_response(str(e), status_code=500)
