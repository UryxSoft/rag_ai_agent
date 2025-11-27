"""
Response Formatter
Standardized API response formatting
"""
from typing import Any, Dict, Optional
from flask import jsonify
from datetime import datetime


def success_response(data: Any = None, message: Optional[str] = None, 
                    status_code: int = 200, **kwargs) -> tuple:
    """
    Format successful API response
    
    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code
        **kwargs: Additional fields to include
    
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'status': 'success',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    # Add any additional fields
    response.update(kwargs)
    
    return jsonify(response), status_code


def error_response(error: str, message: Optional[str] = None, 
                  status_code: int = 400, **kwargs) -> tuple:
    """
    Format error API response
    
    Args:
        error: Error type or description
        message: Optional detailed error message
        status_code: HTTP status code
        **kwargs: Additional fields to include
    
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'status': 'error',
        'error': error,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if message:
        response['message'] = message
    
    # Add any additional fields
    response.update(kwargs)
    
    return jsonify(response), status_code


def paginated_response(items: list, total: int, page: int = 1, 
                       per_page: int = 10, **kwargs) -> tuple:
    """
    Format paginated API response
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        per_page: Items per page
        **kwargs: Additional fields to include
    
    Returns:
        Tuple of (response, status_code)
    """
    total_pages = (total + per_page - 1) // per_page
    
    response = {
        'status': 'success',
        'data': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Add any additional fields
    response.update(kwargs)
    
    return jsonify(response), 200


def analysis_response(document_structure: list, 
                     text_similarity_results: Optional[list] = None,
                     ai_text_detection: Optional[list] = None,
                     image_similarity: Optional[list] = None,
                     rag_contextual_results: Optional[list] = None,
                     observations_llm: Optional[str] = None,
                     insights: Optional[str] = None,
                     memory_id: Optional[str] = None,
                     **kwargs) -> tuple:
    """
    Format analysis API response according to MVP specification
    
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'status': 'success',
        'timestamp': datetime.utcnow().isoformat(),
        'analysis_results': {
            'document_structure': document_structure,
            'text_similarity_results': text_similarity_results or [],
            'ai_text_detection': ai_text_detection or [],
            'image_similarity': image_similarity or [],
            'rag_contextual_results': rag_contextual_results or [],
            'observations_llm': observations_llm or '',
            'insights': insights or '',
            'memory_id': memory_id
        }
    }
    
    # Add any additional fields
    response.update(kwargs)
    
    return jsonify(response), 200


def validation_error_response(errors: Dict[str, Any]) -> tuple:
    """
    Format validation error response
    
    Args:
        errors: Dictionary of validation errors
    
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        error='Validation failed',
        message='Request validation failed',
        validation_errors=errors,
        status_code=422
    )
