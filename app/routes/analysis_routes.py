"""
Analysis Routes
Main document analysis endpoints
"""
import logging
from flask import Blueprint, request
from app.middleware.auth_middleware import require_api_key
from app.utils.response_formatter import success_response, error_response, analysis_response
from app.utils.decorators import validate_file_upload, timing_decorator
from app.utils.file_utils import save_uploaded_file

logger = logging.getLogger(__name__)

bp = Blueprint('analysis', __name__)


@bp.route('/upload', methods=['POST'])
@require_api_key
@validate_file_upload()
@timing_decorator
def upload_document():
    """
    Upload document for analysis
    
    POST /api/analysis/upload
    Form data: file (document file)
    """
    try:
        file = request.files['file']
        filepath, original_filename = save_uploaded_file(file)
        
        return success_response(
            data={
                'filepath': filepath,
                'original_filename': original_filename,
                'message': 'Document uploaded successfully'
            },
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return error_response(str(e), status_code=500)


@bp.route('/analyze', methods=['POST'])
@require_api_key
@timing_decorator
def analyze_document():
    """
    Analyze document with specified analysis types
    
    POST /api/analysis/analyze
    JSON body: {
        "filepath": "path/to/document",
        "analysis_types": ["similarity", "ai_detect", "rag_retrieval"]
    }
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        analysis_types = data.get('analysis_types', [])
        
        if not filepath:
            return error_response('filepath required', status_code=400)
        
        # TODO: Integrate with agent_service for actual analysis
        # For now, return mock response
        
        return analysis_response(
            document_structure=[],
            text_similarity_results=[],
            ai_text_detection=[],
            observations_llm="Analysis completed successfully",
            insights="Document analyzed",
            memory_id="mem_mock123"
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return error_response(str(e), status_code=500)


@bp.route('/status/<analysis_id>', methods=['GET'])
@require_api_key
def get_analysis_status(analysis_id):
    """Get analysis status"""
    return success_response(data={'analysis_id': analysis_id, 'status': 'completed'})
