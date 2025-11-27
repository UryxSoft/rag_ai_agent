"""
RAGAS Integration
RAG quality evaluation metrics
"""
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RAGMetrics:
    """RAG evaluation metrics"""
    context_precision: float
    context_recall: float
    faithfulness: float
    answer_relevancy: float
    overall_score: float


class RAGASEvaluator:
    """
    RAGAS-based RAG evaluation
    Implements key metrics for RAG quality assessment
    """
    
    def __init__(self, llm_service=None):
        """
        Initialize RAGAS evaluator
        
        Args:
            llm_service: LLM service for evaluation
        """
        self.llm_service = llm_service
        logger.info("RAGAS Evaluator initialized")
    
    def evaluate_retrieval(self, query: str, retrieved_contexts: List[str],
                          ground_truth: str = None) -> Dict[str, float]:
        """
        Evaluate retrieval quality
        
        Args:
            query: User query
            retrieved_contexts: Retrieved context chunks
            ground_truth: Ground truth context (if available)
        
        Returns:
            Retrieval metrics
        """
        metrics = {}
        
        # Context Precision: How relevant are the retrieved contexts
        metrics['context_precision'] = self._calculate_context_precision(
            query, retrieved_contexts
        )
        
        # Context Recall: Coverage of relevant information
        if ground_truth:
            metrics['context_recall'] = self._calculate_context_recall(
                retrieved_contexts, ground_truth
            )
        
        # Diversity: How diverse are the retrieved contexts
        metrics['context_diversity'] = self._calculate_diversity(retrieved_contexts)
        
        return metrics
    
    def evaluate_generation(self, query: str, answer: str, 
                           contexts: List[str]) -> Dict[str, float]:
        """
        Evaluate generation quality
        
        Args:
            query: User query
            answer: Generated answer
            contexts: Contexts used for generation
        
        Returns:
            Generation metrics
        """
        metrics = {}
        
        # Faithfulness: Is the answer faithful to the contexts
        metrics['faithfulness'] = self._calculate_faithfulness(answer, contexts)
        
        # Answer Relevancy: How relevant is the answer to the query
        metrics['answer_relevancy'] = self._calculate_answer_relevancy(query, answer)
        
        # Completeness: How complete is the answer
        metrics['completeness'] = self._calculate_completeness(query, answer, contexts)
        
        return metrics
    
    def evaluate_end_to_end(self, query: str, answer: str,
                           retrieved_contexts: List[str],
                           ground_truth_answer: str = None) -> RAGMetrics:
        """
        Complete end-to-end RAG evaluation
        
        Args:
            query: User query
            answer: Generated answer
            retrieved_contexts: Retrieved contexts
            ground_truth_answer: Ground truth answer (if available)
        
        Returns:
            Complete RAG metrics
        """
        # Retrieval metrics
        retrieval = self.evaluate_retrieval(query, retrieved_contexts)
        
        # Generation metrics
        generation = self.evaluate_generation(query, answer, retrieved_contexts)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(retrieval, generation)
        
        return RAGMetrics(
            context_precision=retrieval.get('context_precision', 0.0),
            context_recall=retrieval.get('context_recall', 0.0),
            faithfulness=generation.get('faithfulness', 0.0),
            answer_relevancy=generation.get('answer_relevancy', 0.0),
            overall_score=overall_score
        )
    
    def _calculate_context_precision(self, query: str, 
                                    contexts: List[str]) -> float:
        """
        Calculate context precision
        Measures relevance of retrieved contexts to query
        """
        if not contexts:
            return 0.0
        
        # Simple implementation: keyword overlap
        query_words = set(query.lower().split())
        
        relevant_count = 0
        for context in contexts:
            context_words = set(context.lower().split())
            overlap = len(query_words.intersection(context_words))
            
            # Consider relevant if significant overlap
            if overlap >= min(3, len(query_words) * 0.3):
                relevant_count += 1
        
        return relevant_count / len(contexts)
    
    def _calculate_context_recall(self, contexts: List[str], 
                                  ground_truth: str) -> float:
        """
        Calculate context recall
        Measures coverage of ground truth in retrieved contexts
        """
        if not contexts or not ground_truth:
            return 0.0
        
        ground_truth_words = set(ground_truth.lower().split())
        retrieved_words = set()
        
        for context in contexts:
            retrieved_words.update(context.lower().split())
        
        # Calculate coverage
        coverage = len(ground_truth_words.intersection(retrieved_words))
        return coverage / len(ground_truth_words) if ground_truth_words else 0.0
    
    def _calculate_diversity(self, contexts: List[str]) -> float:
        """Calculate diversity of retrieved contexts"""
        if len(contexts) < 2:
            return 1.0
        
        # Calculate pairwise similarity
        similarities = []
        for i in range(len(contexts)):
            for j in range(i + 1, len(contexts)):
                sim = self._text_similarity(contexts[i], contexts[j])
                similarities.append(sim)
        
        # Diversity is inverse of average similarity
        avg_similarity = np.mean(similarities) if similarities else 0
        return 1.0 - avg_similarity
    
    def _calculate_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """
        Calculate faithfulness
        Measures if answer is supported by contexts
        """
        if not contexts:
            return 0.0
        
        answer_sentences = answer.split('.')
        supported_count = 0
        
        for sentence in answer_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if sentence is supported by any context
            for context in contexts:
                if self._is_supported(sentence, context):
                    supported_count += 1
                    break
        
        return supported_count / len(answer_sentences) if answer_sentences else 0.0
    
    def _calculate_answer_relevancy(self, query: str, answer: str) -> float:
        """
        Calculate answer relevancy
        Measures how well answer addresses the query
        """
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        overlap = len(query_words.intersection(answer_words))
        
        # Normalize by query length
        return overlap / len(query_words) if query_words else 0.0
    
    def _calculate_completeness(self, query: str, answer: str,
                               contexts: List[str]) -> float:
        """
        Calculate completeness
        Measures if answer addresses all aspects of query
        """
        # Simple implementation based on length ratio
        context_length = sum(len(c.split()) for c in contexts)
        answer_length = len(answer.split())
        
        if context_length == 0:
            return 0.0
        
        # Expect answer to be 20-50% of context length
        ratio = answer_length / context_length
        
        if 0.2 <= ratio <= 0.5:
            return 1.0
        elif ratio < 0.2:
            return ratio / 0.2
        else:
            return max(0, 1.0 - (ratio - 0.5))
    
    def _calculate_overall_score(self, retrieval: Dict[str, float],
                                generation: Dict[str, float]) -> float:
        """Calculate weighted overall score"""
        weights = {
            'context_precision': 0.2,
            'faithfulness': 0.3,
            'answer_relevancy': 0.3,
            'completeness': 0.2
        }
        
        score = 0.0
        for metric, weight in weights.items():
            if metric in retrieval:
                score += retrieval[metric] * weight
            elif metric in generation:
                score += generation[metric] * weight
        
        return score
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _is_supported(self, sentence: str, context: str) -> bool:
        """Check if sentence is supported by context"""
        # Simple check: significant word overlap
        sentence_words = set(sentence.lower().split())
        context_words = set(context.lower().split())
        
        overlap = len(sentence_words.intersection(context_words))
        return overlap >= len(sentence_words) * 0.6
    
    def batch_evaluate(self, test_cases: List[Dict[str, Any]]) -> List[RAGMetrics]:
        """
        Evaluate multiple test cases
        
        Args:
            test_cases: List of test cases with query, answer, contexts
        
        Returns:
            List of evaluation metrics
        """
        results = []
        
        for case in test_cases:
            metrics = self.evaluate_end_to_end(
                query=case['query'],
                answer=case['answer'],
                retrieved_contexts=case['contexts'],
                ground_truth_answer=case.get('ground_truth')
            )
            results.append(metrics)
        
        return results
    
    def generate_report(self, metrics_list: List[RAGMetrics]) -> Dict[str, Any]:
        """
        Generate evaluation report from multiple metrics
        
        Args:
            metrics_list: List of RAG metrics
        
        Returns:
            Aggregated report
        """
        if not metrics_list:
            return {}
        
        return {
            'total_evaluations': len(metrics_list),
            'average_context_precision': np.mean([m.context_precision for m in metrics_list]),
            'average_context_recall': np.mean([m.context_recall for m in metrics_list]),
            'average_faithfulness': np.mean([m.faithfulness for m in metrics_list]),
            'average_answer_relevancy': np.mean([m.answer_relevancy for m in metrics_list]),
            'average_overall_score': np.mean([m.overall_score for m in metrics_list]),
            'min_score': min(m.overall_score for m in metrics_list),
            'max_score': max(m.overall_score for m in metrics_list)
        }