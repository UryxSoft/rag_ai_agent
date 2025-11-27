"""
Text Utilities
Helper functions for text processing and analysis
"""
import re
import logging
from typing import List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix punctuation spacing
    text = re.sub(r'\s+([,.;:?!])', r'\1', text)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    # Simple sentence splitter
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk = ' '.join(chunk_words)
        chunks.append(chunk)
    
    return chunks


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extract top keywords from text
    Simple frequency-based extraction
    """
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which'
    }
    
    # Tokenize and clean
    words = re.findall(r'\b[a-z]+\b', text.lower())
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Get most common
    word_counts = Counter(filtered_words)
    return [word for word, _ in word_counts.most_common(top_n)]


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple Jaccard similarity between two texts
    
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())


def count_sentences(text: str) -> int:
    """Count sentences in text"""
    return len(split_into_sentences(text))


def get_text_statistics(text: str) -> Dict[str, Any]:
    """
    Get comprehensive text statistics
    
    Returns:
        Dictionary with various text metrics
    """
    words = text.split()
    sentences = split_into_sentences(text)
    paragraphs = split_into_paragraphs(text)
    
    return {
        'char_count': len(text),
        'word_count': len(words),
        'sentence_count': len(sentences),
        'paragraph_count': len(paragraphs),
        'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
        'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
        'unique_words': len(set(w.lower() for w in words))
    }


def highlight_text(text: str, query: str, tag: str = 'mark') -> str:
    """
    Highlight search query in text
    
    Args:
        text: Input text
        query: Search query
        tag: HTML tag to use for highlighting
    
    Returns:
        Text with highlighted matches
    """
    if not query:
        return text
    
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(f'<{tag}>\\g<0></{tag}>', text)


def extract_snippet(text: str, query: str, context_length: int = 100) -> str:
    """
    Extract a snippet of text around the query
    
    Args:
        text: Input text
        query: Search query
        context_length: Characters to include before/after match
    
    Returns:
        Text snippet with context
    """
    query_lower = query.lower()
    text_lower = text.lower()
    
    pos = text_lower.find(query_lower)
    if pos == -1:
        return truncate_text(text, context_length * 2)
    
    start = max(0, pos - context_length)
    end = min(len(text), pos + len(query) + context_length)
    
    snippet = text[start:end]
    
    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'
    
    return snippet
