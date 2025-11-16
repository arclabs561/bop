"""Token-level importance tracking and visualization for retrieval results."""

import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import logging

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.tag import pos_tag
    NLTK_AVAILABLE = True
    # Download required NLTK data (idempotent)
    # Note: punkt_tab is the newer version, but punkt works too
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except Exception:
            # Try punkt_tab if punkt fails
            try:
                nltk.download('punkt_tab', quiet=True)
            except Exception:
                pass  # Will fall back to simple approach
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('averaged_perceptron_tagger', quiet=True)
except ImportError:
    NLTK_AVAILABLE = False
    stopwords = None
    word_tokenize = None
    pos_tag = None

logger = logging.getLogger(__name__)


def extract_key_terms(text: str, min_length: int = 3, max_terms: int = 20) -> List[str]:
    """
    Extract key terms from text using NLTK-enhanced heuristics when available.
    
    Uses NLTK for better stop word filtering and POS tagging when available,
    falls back to simple regex-based approach otherwise.
    
    Args:
        text: Input text
        min_length: Minimum word length
        max_terms: Maximum number of terms to return
        
    Returns:
        List of key terms sorted by importance
    """
    if not text:
        return []
    
    # Use NLTK if available for better tokenization and stop word filtering
    if NLTK_AVAILABLE and word_tokenize and stopwords:
        try:
            # Tokenize with NLTK
            tokens = word_tokenize(text.lower())
            
            # Get English stop words from NLTK
            english_stopwords = set(stopwords.words('english'))
            # Add custom stop words
            english_stopwords.update({
                "n't", "'s", "'re", "'ve", "'ll", "'d", "'m",  # Contractions
            })
            
            # Filter: length, stop words, alphanumeric only
            filtered_tokens = [
                token for token in tokens
                if len(token) >= min_length
                and token.isalnum()
                and token not in english_stopwords
            ]
            
            # Optional: Use POS tagging to prefer nouns, adjectives, verbs
            try:
                tagged = pos_tag(filtered_tokens)
                # Prefer nouns (NN, NNS, NNP, NNPS), adjectives (JJ, JJR, JJS), verbs (VB, VBD, VBG, VBN, VBP, VBZ)
                preferred_tags = {'NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'JJR', 'JJS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'}
                filtered_tokens = [word for word, tag in tagged if tag in preferred_tags or not tag]
            except Exception:
                # If POS tagging fails, continue without it
                pass
            
            # Count frequency
            word_counts = Counter(filtered_tokens)
            
            # Return top terms
            return [word for word, _ in word_counts.most_common(max_terms)]
            
        except Exception as e:
            logger.warning(f"NLTK tokenization failed, falling back to simple approach: {e}")
            # Fall through to simple approach
    
    # Fallback: Simple regex-based approach
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "can", "this", "that", "these", "those",
        "and", "or", "but", "if", "then", "than", "as", "to", "of", "in", "on",
        "at", "for", "with", "by", "from", "about", "into", "through", "during",
        "over", "under", "above", "below", "up", "down", "out", "off", "away",
        "what", "how", "why", "when", "where", "which", "who", "whom", "whose",
    }
    
    # Extract words (alphanumeric sequences)
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by length and stop words
    filtered_words = [
        w for w in words 
        if len(w) >= min_length and w not in stop_words
    ]
    
    # Count frequency
    word_counts = Counter(filtered_words)
    
    # Return top terms
    return [word for word, _ in word_counts.most_common(max_terms)]


def compute_term_importance(
    query: str,
    result_text: str,
    query_terms: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Compute importance scores for terms in result text relative to query.
    
    Uses TF-IDF-like approach: terms that appear in both query and result
    get higher importance scores.
    
    Args:
        query: Original query text
        result_text: Result text from retrieval
        query_terms: Optional pre-extracted query terms
        
    Returns:
        Dictionary mapping terms to importance scores (0.0 to 1.0)
    """
    if not result_text:
        return {}
    
    # Extract terms from query if not provided
    if query_terms is None:
        query_terms = extract_key_terms(query)
    
    # Extract terms from result
    result_terms = extract_key_terms(result_text, max_terms=50)
    
    # Compute importance scores
    importance = {}
    
    # Terms that appear in both query and result get high importance
    query_terms_set = set(query_terms)
    result_terms_set = set(result_terms)
    
    # Count term frequencies in result
    result_words = re.findall(r'\b[a-zA-Z]+\b', result_text.lower())
    term_freq = Counter(result_words)
    max_freq = max(term_freq.values()) if term_freq else 1
    
    for term in result_terms:
        # Base importance from frequency (normalized)
        freq_score = term_freq.get(term, 0) / max_freq
        
        # Boost if term appears in query
        query_boost = 1.5 if term in query_terms_set else 1.0
        
        # Combined importance
        importance[term] = min(1.0, freq_score * query_boost)
    
    return importance


def compute_token_importance_for_results(
    query: str,
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute token importance across multiple retrieval results.
    
    Aggregates importance scores across all results to identify
    which terms are most important overall.
    
    Args:
        query: Original query
        results: List of result dictionaries with "result" field
        
    Returns:
        Dictionary with:
        - term_importance: Dict mapping terms to aggregated importance scores
        - per_result_importance: List of importance dicts per result
        - top_terms: List of top N terms by importance
    """
    if not results:
        return {
            "term_importance": {},
            "per_result_importance": [],
            "top_terms": [],
        }
    
    # Extract query terms once
    query_terms = extract_key_terms(query)
    
    # Compute importance for each result
    per_result = []
    all_terms = defaultdict(list)
    
    for result in results:
        result_text = result.get("result", "")
        if not result_text:
            continue
        
        importance = compute_term_importance(query, result_text, query_terms)
        per_result.append(importance)
        
        # Aggregate across results
        for term, score in importance.items():
            all_terms[term].append(score)
    
    # Aggregate importance scores (average across results)
    term_importance = {
        term: sum(scores) / len(scores)
        for term, scores in all_terms.items()
    }
    
    # Get top terms
    top_terms = [
        term for term, _ in sorted(
            term_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
    ]
    
    return {
        "term_importance": term_importance,
        "per_result_importance": per_result,
        "top_terms": top_terms,
        "query_terms": query_terms,
    }


def format_token_importance(
    importance_data: Dict[str, Any],
    max_display: int = 10,
) -> str:
    """
    Format token importance data for display.
    
    Args:
        importance_data: Output from compute_token_importance_for_results
        max_display: Maximum number of terms to display
        
    Returns:
        Formatted string
    """
    if not importance_data or not importance_data.get("term_importance"):
        return ""
    
    term_importance = importance_data["term_importance"]
    top_terms = importance_data.get("top_terms", [])[:max_display]
    
    if not top_terms:
        return ""
    
    parts = ["**Key Terms Driving Retrieval:**"]
    
    for i, term in enumerate(top_terms, 1):
        score = term_importance.get(term, 0.0)
        # Create visual bar
        bar_length = int(score * 20)  # Scale to 20 chars
        bar = "█" * bar_length + "░" * (20 - bar_length)
        parts.append(f"  {i}. {term:20s} {bar} {score:.2f}")
    
    return "\n".join(parts)

