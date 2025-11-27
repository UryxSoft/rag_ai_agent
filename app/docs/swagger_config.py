"""
Swagger/OpenAPI Documentation
Interactive API documentation
"""
import logging
from flask import Blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

# Create Swagger UI blueprint
swagger_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Intelligent Analysis System API",
        'layout': "BaseLayout",
        'deepLinking': True
    }
)


def generate_openapi_spec() -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification
    
    Returns:
        OpenAPI specification dictionary
    """
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Intelligent Analysis System API",
            "version": "2.0.0",
            "description": "Enterprise-level document and image analysis system with RAG, AI Agents, and real-time updates",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            },
            "license": {
                "name": "Proprietary",
                "url": "https://example.com/license"
            }
        },
        "servers": [
            {
                "url": "http://localhost:5000",
                "description": "Development server"
            },
            {
                "url": "https://api.example.com",
                "description": "Production server"
            }
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token obtained from /api/auth/login"
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "status": {"type": "string"},
                        "message": {"type": "string"}
                    }
                },
                "AnalysisResult": {
                    "type": "object",
                    "properties": {
                        "document_structure": {"type": "array"},
                        "text_similarity_results": {"type": "array"},
                        "ai_text_detection": {"type": "array"},
                        "image_similarity": {"type": "array"},
                        "rag_contextual_results": {"type": "array"},
                        "observations_llm": {"type": "string"},
                        "insights": {"type": "string"},
                        "memory_id": {"type": "string"}
                    }
                },
                "TaskStatus": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "state": {"type": "string", "enum": ["PENDING", "PROCESSING", "SUCCESS", "FAILURE"]},
                        "progress": {"type": "integer", "minimum": 0, "maximum": 100},
                        "status": {"type": "string"},
                        "result": {"type": "object"}
                    }
                }
            }
        },
        "security": [
            {"BearerAuth": []}
        ],
        "paths": {
            "/api/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "User login",
                    "description": "Authenticate user and receive JWT tokens",
                    "security": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string", "format": "password"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "access_token": {"type": "string"},
                                            "refresh_token": {"type": "string"},
                                            "token_type": {"type": "string"},
                                            "expires_in": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid credentials",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/analysis/upload": {
                "post": {
                    "tags": ["Analysis"],
                    "summary": "Upload document",
                    "description": "Upload document for analysis",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "required": ["file"],
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Document uploaded successfully"
                        },
                        "400": {
                            "description": "Invalid file"
                        }
                    }
                }
            },
            "/api/analysis/analyze": {
                "post": {
                    "tags": ["Analysis"],
                    "summary": "Analyze document",
                    "description": "Start asynchronous document analysis",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["filepath", "analysis_types"],
                                    "properties": {
                                        "filepath": {"type": "string"},
                                        "analysis_types": {
                                            "type": "array",
                                            "items": {
                                                "type": "string",
                                                "enum": ["similarity", "ai_detect", "rag_retrieval"]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Analysis started",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "task_id": {"type": "string"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/tasks/{task_id}": {
                "get": {
                    "tags": ["Tasks"],
                    "summary": "Get task status",
                    "description": "Get status of async task",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Task status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TaskStatus"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/chat/message": {
                "post": {
                    "tags": ["Chat"],
                    "summary": "Send chat message",
                    "description": "Send message in post-analysis chat",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["memory_id", "question"],
                                    "properties": {
                                        "memory_id": {"type": "string"},
                                        "question": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Chat response"
                        }
                    }
                }
            },
            "/api/chat/stream": {
                "post": {
                    "tags": ["Chat"],
                    "summary": "Stream chat response",
                    "description": "Stream chat response with SSE",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["memory_id", "question"],
                                    "properties": {
                                        "memory_id": {"type": "string"},
                                        "question": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Streaming response",
                            "content": {
                                "text/event-stream": {
                                    "schema": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "/metrics": {
                "get": {
                    "tags": ["Monitoring"],
                    "summary": "Prometheus metrics",
                    "description": "Get Prometheus metrics",
                    "security": [],
                    "responses": {
                        "200": {
                            "description": "Metrics in Prometheus format"
                        }
                    }
                }
            },
            "/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "Health check",
                    "description": "Check system health",
                    "security": [],
                    "responses": {
                        "200": {
                            "description": "System healthy"
                        }
                    }
                }
            }
        },
        "tags": [
            {"name": "Authentication", "description": "Authentication endpoints"},
            {"name": "Analysis", "description": "Document analysis operations"},
            {"name": "Tasks", "description": "Async task management"},
            {"name": "Chat", "description": "Post-analysis chat"},
            {"name": "Monitoring", "description": "System monitoring"},
            {"name": "System", "description": "System utilities"}
        ]
    }
    
    return spec


# Blueprint for serving OpenAPI spec
api_spec_blueprint = Blueprint('api_spec', __name__)


@api_spec_blueprint.route('/api/swagger.json')
def swagger_spec():
    """Serve OpenAPI specification"""
    from flask import jsonify
    return jsonify(generate_openapi_spec())