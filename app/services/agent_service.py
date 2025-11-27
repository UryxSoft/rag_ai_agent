"""
AI Agents Service using CrewAI
Coordinates multiple AI agents for document analysis
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from an individual agent"""
    agent_name: str
    status: str
    data: Any
    execution_time: float
    errors: List[str] = None


class DocumentAnalyzerAgent:
    """Agent for analyzing document structure and content"""
    
    def __init__(self, document_service):
        self.document_service = document_service
        self.name = "Document Analyzer"
    
    def analyze(self, document_path: str) -> Dict[str, Any]:
        """Analyze document structure"""
        logger.info(f"{self.name}: Analyzing document")
        
        try:
            # Extract document structure
            structure = self.document_service.extract_document(document_path)
            
            return {
                'status': 'success',
                'structure': structure,
                'page_count': len(structure.get('document', [])),
                'word_count': sum(len(p['text'].split()) for p in structure.get('document', []))
            }
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return {'status': 'error', 'error': str(e)}


class SimilarityAgent:
    """Agent for detecting text similarity"""
    
    def __init__(self, opensearch_service, faiss_service):
        self.opensearch = opensearch_service
        self.faiss = faiss_service
        self.name = "Similarity Agent"
    
    def analyze(self, document_text: str) -> Dict[str, Any]:
        """Detect similarity with existing documents"""
        logger.info(f"{self.name}: Checking similarity")
        
        try:
            # Search in OpenSearch (BM25)
            opensearch_results = self.opensearch.search_similar(document_text)
            
            # Search in FAISS (semantic)
            faiss_results = self.faiss.search(document_text, top_k=10) if self.faiss else []
            
            return {
                'status': 'success',
                'opensearch_matches': opensearch_results,
                'semantic_matches': faiss_results,
                'total_matches': len(opensearch_results) + len(faiss_results)
            }
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return {'status': 'error', 'error': str(e)}


class AIContentDetectorAgent:
    """Agent for detecting AI-generated content"""
    
    def __init__(self, ai_text_detector):
        self.detector = ai_text_detector
        self.name = "AI Content Detector"
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Detect if text is AI-generated"""
        logger.info(f"{self.name}: Analyzing text")
        
        try:
            # Split into paragraphs for analysis
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            # Analyze each paragraph
            results = self.detector.classify_text_batch_optimized(paragraphs)
            
            # Calculate overall statistics
            ai_count = sum(1 for r in results if not r['is_human'])
            human_count = len(results) - ai_count
            
            avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
            
            return {
                'status': 'success',
                'paragraph_count': len(paragraphs),
                'ai_generated_count': ai_count,
                'human_written_count': human_count,
                'average_confidence': avg_confidence,
                'overall_classification': 'AI' if ai_count > human_count else 'Human',
                'detailed_results': results
            }
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return {'status': 'error', 'error': str(e)}


class ImageSimilarityAgent:
    """Agent for detecting image similarity"""
    
    def __init__(self, image_detector):
        self.detector = image_detector
        self.name = "Image Similarity Agent"
    
    def analyze(self, image_paths: List[str]) -> Dict[str, Any]:
        """Analyze image similarity"""
        logger.info(f"{self.name}: Analyzing images")
        
        try:
            if not image_paths:
                return {'status': 'success', 'message': 'No images to analyze'}
            
            # Analyze each image
            results = []
            for img_path in image_paths:
                result = self.detector.analyze_image(img_path)
                results.append(result)
            
            return {
                'status': 'success',
                'image_count': len(image_paths),
                'results': results
            }
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return {'status': 'error', 'error': str(e)}


class RAGRetrievalAgent:
    """Agent for RAG-based retrieval and contextualization"""
    
    def __init__(self, rag_service):
        self.rag = rag_service
        self.name = "RAG Retrieval Agent"
    
    def analyze(self, document_id: str, query: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve and contextualize information"""
        logger.info(f"{self.name}: Retrieving context")
        
        try:
            if not query:
                query = "Summarize key findings and important sections"
            
            # Retrieve relevant context
            context = self.rag.retrieve_context(query, top_k=10, document_id=document_id)
            
            # Generate summary if possible
            summary = self.rag.get_document_summary(document_id) if document_id else ""
            
            return {
                'status': 'success',
                'context_chunks': len(context),
                'context': context,
                'summary': summary
            }
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return {'status': 'error', 'error': str(e)}


class InsightAgent:
    """Agent for generating insights and observations using LLM"""
    
    def __init__(self, llm_service):
        self.llm = llm_service
        self.name = "Insight Agent"
    
    def analyze(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from analysis results"""
        logger.info(f"{self.name}: Generating insights")
        
        try:
            # Build prompt from all results
            prompt = self._build_insight_prompt(analysis_results)
            
            # Generate insights
            insights = self.llm.generate(prompt, max_tokens=1024) if self.llm else "LLM not available"
            
            # Generate specific observations
            observations = self._generate_observations(analysis_results)
            
            return {
                'status': 'success',
                'insights': insights,
                'observations': observations
            }
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _build_insight_prompt(self, results: Dict[str, Any]) -> str:
        """Build prompt for LLM insight generation"""
        prompt = "Analyze the following document analysis results and provide key insights:\n\n"
        
        # Add document info
        if 'document_analysis' in results:
            doc = results['document_analysis']
            prompt += f"Document: {doc.get('page_count', 0)} pages, {doc.get('word_count', 0)} words\n"
        
        # Add similarity info
        if 'similarity' in results:
            sim = results['similarity']
            prompt += f"Similarity: {sim.get('total_matches', 0)} potential matches found\n"
        
        # Add AI detection info
        if 'ai_detection' in results:
            ai = results['ai_detection']
            prompt += f"AI Detection: {ai.get('overall_classification', 'Unknown')}, "
            prompt += f"{ai.get('ai_generated_count', 0)} AI paragraphs, "
            prompt += f"{ai.get('human_written_count', 0)} human paragraphs\n"
        
        prompt += "\nProvide a concise analysis highlighting the most important findings:\n"
        
        return prompt
    
    def _generate_observations(self, results: Dict[str, Any]) -> List[str]:
        """Generate specific observations from results"""
        observations = []
        
        # Document observations
        if 'document_analysis' in results:
            doc = results['document_analysis']
            if doc.get('word_count', 0) > 5000:
                observations.append("Document is substantial in length")
        
        # Similarity observations
        if 'similarity' in results:
            sim = results['similarity']
            if sim.get('total_matches', 0) > 5:
                observations.append("High similarity detected with existing documents")
        
        # AI detection observations
        if 'ai_detection' in results:
            ai = results['ai_detection']
            if ai.get('ai_generated_count', 0) > ai.get('human_written_count', 0):
                observations.append("Majority of content appears to be AI-generated")
        
        return observations


class AgentCoordinator:
    """
    Coordinates all AI agents using CrewAI pattern
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize agent coordinator
        
        Args:
            config: Configuration with service instances
        """
        self.config = config or {}
        self.agents = {}
        self._initialize_agents()
        logger.info("Agent Coordinator initialized")
    
    def _initialize_agents(self):
        """Initialize all agents with their dependencies"""
        config = self.config
        
        # Initialize agents with their respective services
        if 'document_service' in config:
            self.agents['document_analyzer'] = DocumentAnalyzerAgent(config['document_service'])
        
        if 'opensearch_service' in config and 'faiss_service' in config:
            self.agents['similarity'] = SimilarityAgent(
                config['opensearch_service'],
                config['faiss_service']
            )
        
        if 'ai_text_detector' in config:
            self.agents['ai_detector'] = AIContentDetectorAgent(config['ai_text_detector'])
        
        if 'image_detector' in config:
            self.agents['image_similarity'] = ImageSimilarityAgent(config['image_detector'])
        
        if 'rag_service' in config:
            self.agents['rag_retrieval'] = RAGRetrievalAgent(config['rag_service'])
        
        if 'llm_service' in config:
            self.agents['insight'] = InsightAgent(config['llm_service'])
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    def run_analysis(self, document_path: str, analysis_types: List[str],
                    image_paths: List[str] = None) -> Dict[str, Any]:
        """
        Run coordinated analysis with specified agents
        
        Args:
            document_path: Path to document
            analysis_types: List of analysis types to run
            image_paths: Optional list of image paths
        
        Returns:
            Combined analysis results
        """
        import time
        
        results = {
            'analysis_types': analysis_types,
            'timestamp': time.time()
        }
        
        # Run Document Analyzer
        if 'document_analyzer' in self.agents:
            start = time.time()
            results['document_analysis'] = self.agents['document_analyzer'].analyze(document_path)
            results['document_analysis']['execution_time'] = time.time() - start
        
        # Extract text for other agents
        document_text = self._extract_text_from_results(results.get('document_analysis', {}))
        document_id = document_path  # Use path as ID for now
        
        # Run Similarity Agent if requested
        if 'similarity' in analysis_types and 'similarity' in self.agents:
            start = time.time()
            results['similarity'] = self.agents['similarity'].analyze(document_text)
            results['similarity']['execution_time'] = time.time() - start
        
        # Run AI Detector if requested
        if 'ai_detect' in analysis_types and 'ai_detector' in self.agents:
            start = time.time()
            results['ai_detection'] = self.agents['ai_detector'].analyze(document_text)
            results['ai_detection']['execution_time'] = time.time() - start
        
        # Run Image Similarity if requested
        if 'image_similarity' in analysis_types and image_paths and 'image_similarity' in self.agents:
            start = time.time()
            results['image_analysis'] = self.agents['image_similarity'].analyze(image_paths)
            results['image_analysis']['execution_time'] = time.time() - start
        
        # Run RAG Retrieval if requested
        if 'rag_retrieval' in self.agents:
            start = time.time()
            results['rag_context'] = self.agents['rag_retrieval'].analyze(document_id)
            results['rag_context']['execution_time'] = time.time() - start
        
        # Run Insight Agent to generate final observations
        if 'insight' in self.agents:
            start = time.time()
            results['insights'] = self.agents['insight'].analyze(results)
            results['insights']['execution_time'] = time.time() - start
        
        return results
    
    def _extract_text_from_results(self, document_analysis: Dict) -> str:
        """Extract full text from document analysis results"""
        if not document_analysis or document_analysis.get('status') != 'success':
            return ""
        
        structure = document_analysis.get('structure', {})
        document = structure.get('document', [])
        
        text_parts = [item.get('text', '') for item in document]
        return "\n\n".join(text_parts)
