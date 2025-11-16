"""Token-level provenance tracking for source references.

This module provides functionality to track which query tokens matched
which document tokens, enabling interactive provenance visualization.
"""

import re
import difflib
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def extract_sentences(text: str, min_length: int = 20) -> List[str]:
    """Extract meaningful sentences from text."""
    if not text:
        return []
    
    # Split by sentence boundaries
    sentences = re.split(r'[.!?]+', text)
    # Clean and filter
    sentences = [s.strip() for s in sentences if len(s.strip()) >= min_length]
    return sentences


def _levenshtein_ratio(s1: str, s2: str) -> float:
    """
    Compute Levenshtein similarity ratio between two strings.
    
    Returns 0.0 to 1.0 where 1.0 is identical.
    """
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    
    # Use SequenceMatcher for efficiency (approximates Levenshtein)
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def compute_token_matches(
    query: str,
    document_text: str,
    query_tokens: Optional[List[str]] = None,
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Compute which query tokens matched which document tokens.
    
    Returns a mapping from query tokens to list of (document_token, similarity_score) tuples.
    
    Enhanced with:
    - Levenshtein distance for fuzzy matching
    - Stemming-aware matching (handles word variations)
    - Position-aware scoring (earlier matches weighted higher)
    """
    if not document_text:
        return {}
    
    # Extract query tokens if not provided
    if query_tokens is None:
        query_lower = query.lower()
        # Remove punctuation and split
        query_tokens = re.findall(r'\b[a-zA-Z]{3,}\b', query_lower)
    
    # Extract document tokens with positions for better scoring
    doc_lower = document_text.lower()
    doc_tokens_with_pos = []
    for match in re.finditer(r'\b[a-zA-Z]{3,}\b', doc_lower):
        doc_tokens_with_pos.append((match.group(), match.start()))
    
    doc_tokens = [token for token, _ in doc_tokens_with_pos]
    doc_tokens_set = set(doc_tokens)
    
    # Compute matches with improved similarity
    matches = {}
    for query_token in query_tokens:
        token_matches = []
        
        # Check exact match first
        if query_token in doc_tokens_set:
            # Exact match with position bonus (earlier = better)
            positions = [pos for token, pos in doc_tokens_with_pos if token == query_token]
            for pos in positions[:3]:  # Top 3 positions
                # Position bonus: earlier in document = slightly higher score
                position_bonus = max(0.95, 1.0 - (pos / len(doc_lower)) * 0.05)
                token_matches.append((query_token, position_bonus))
        else:
            # Fuzzy matching with Levenshtein distance
            for doc_token, pos in doc_tokens_with_pos:
                # Check substring match first (fast)
                if query_token in doc_token or doc_token in query_token:
                    # Use Levenshtein ratio for better similarity
                    similarity = _levenshtein_ratio(query_token, doc_token)
                    if similarity > 0.7:  # 70% similarity threshold
                        # Position bonus for earlier matches
                        position_bonus = max(0.9, 1.0 - (pos / len(doc_lower)) * 0.1)
                        final_score = similarity * position_bonus
                        token_matches.append((doc_token, final_score))
                else:
                    # Check Levenshtein distance for similar words
                    similarity = _levenshtein_ratio(query_token, doc_token)
                    if similarity > 0.8:  # Higher threshold for non-substring matches
                        position_bonus = max(0.9, 1.0 - (pos / len(doc_lower)) * 0.1)
                        final_score = similarity * position_bonus
                        token_matches.append((doc_token, final_score))
        
        if token_matches:
            # Sort by score and take top matches
            token_matches.sort(key=lambda x: x[1], reverse=True)
            matches[query_token] = token_matches[:5]  # Top 5 matches
    
    return matches


def _compute_semantic_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts.
    
    Uses multiple methods:
    - Sequence matcher (character-level similarity)
    - Word overlap (Jaccard similarity)
    - Concept overlap (key terms)
    
    Returns:
        0.0 to 1.0 similarity score
    """
    if not text1 or not text2:
        return 0.0
    
    text1_lower = text1.lower()
    text2_lower = text2.lower()
    
    # Method 1: Sequence matcher
    seq_sim = difflib.SequenceMatcher(None, text1_lower, text2_lower).ratio()
    
    # Method 2: Word overlap (Jaccard)
    words1 = set(re.findall(r'\b[a-zA-Z]{3,}\b', text1_lower))
    words2 = set(re.findall(r'\b[a-zA-Z]{3,}\b', text2_lower))
    if words1 or words2:
        jaccard = len(words1 & words2) / len(words1 | words2) if (words1 | words2) else 0.0
    else:
        jaccard = 0.0
    
    # Method 3: Concept overlap (longer words weighted more)
    concepts1 = {w for w in words1 if len(w) >= 4}
    concepts2 = {w for w in words2 if len(w) >= 4}
    if concepts1 or concepts2:
        concept_overlap = len(concepts1 & concepts2) / len(concepts1 | concepts2) if (concepts1 | concepts2) else 0.0
    else:
        concept_overlap = 0.0
    
    # Weighted combination
    return (seq_sim * 0.3 + jaccard * 0.3 + concept_overlap * 0.4)


def _compute_relevance_breakdown(
    claim: str,
    result_text: str,
    overlap_ratio: float,
    semantic_similarity: float,
    token_matches: Dict[str, List[Tuple[str, float]]],
) -> Dict[str, Any]:
    """
    Compute detailed relevance score breakdown explaining why source was selected.
    
    Returns:
        Dictionary with:
        - overall_score: Combined relevance score
        - components: Individual score components
        - explanation: Human-readable explanation
        - top_token_matches: Most important token matches
    """
    # Calculate token match contribution
    token_scores = []
    for query_token, matches in token_matches.items():
        if matches:
            # Get best match score
            best_score = max(score for _, score in matches)
            token_scores.append((query_token, best_score))
    
    # Sort by score
    token_scores.sort(key=lambda x: x[1], reverse=True)
    top_tokens = token_scores[:5]
    
    # Calculate average token match score
    avg_token_score = sum(score for _, score in token_scores) / len(token_scores) if token_scores else 0.0
    
    # Enhanced relevance scoring with adaptive weights
    # If token matches are strong, weight them more
    token_weight = 0.2
    if avg_token_score > 0.8:
        # Strong token matches -> increase token weight
        token_weight = 0.3
        overlap_weight = 0.35
        semantic_weight = 0.35
    elif avg_token_score < 0.3:
        # Weak token matches -> decrease token weight
        token_weight = 0.1
        overlap_weight = 0.45
        semantic_weight = 0.45
    else:
        overlap_weight = 0.4
        semantic_weight = 0.4
    
    # Overall relevance score (weighted combination)
    overall_score = (
        overlap_ratio * overlap_weight +
        semantic_similarity * semantic_weight +
        avg_token_score * token_weight
    )
    
    # Clamp to [0, 1]
    overall_score = max(0.0, min(1.0, overall_score))
    
    # Generate explanation
    explanation_parts = []
    if overlap_ratio > 0.5:
        explanation_parts.append(f"High word overlap ({overlap_ratio:.1%})")
    elif overlap_ratio > 0.3:
        explanation_parts.append(f"Moderate word overlap ({overlap_ratio:.1%})")
    else:
        explanation_parts.append(f"Low word overlap ({overlap_ratio:.1%})")
    
    if semantic_similarity > 0.6:
        explanation_parts.append(f"Strong semantic similarity ({semantic_similarity:.1%})")
    elif semantic_similarity > 0.4:
        explanation_parts.append(f"Moderate semantic similarity ({semantic_similarity:.1%})")
    else:
        explanation_parts.append(f"Weak semantic similarity ({semantic_similarity:.1%})")
    
    if top_tokens:
        top_token_str = ", ".join([f"{token}({score:.2f})" for token, score in top_tokens[:3]])
        explanation_parts.append(f"Key token matches: {top_token_str}")
    
    explanation = ". ".join(explanation_parts) + "."
    
    return {
        "overall_score": overall_score,
        "components": {
            "word_overlap": overlap_ratio,
            "semantic_similarity": semantic_similarity,
            "token_match_avg": avg_token_score,
        },
        "explanation": explanation,
        "top_token_matches": top_tokens,
        "num_token_matches": len(token_scores),
    }


def match_claim_to_sources(
    claim: str,
    research_results: List[Dict[str, Any]],
    min_overlap: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Match a claim (sentence from response) to source results.
    
    Returns list of source matches with provenance information.
    """
    if not claim or not research_results:
        return []
    
    claim_lower = claim.lower()
    claim_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', claim_lower))
    
    matches = []
    for result in research_results:
        result_text = result.get("result", "")
        if not result_text:
            continue
        
        result_lower = result_text.lower()
        result_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', result_lower))
        
        # Compute word overlap
        overlap = len(claim_words & result_words)
        total_claim_words = len(claim_words)
        
        if total_claim_words == 0:
            continue
        
        overlap_ratio = overlap / total_claim_words
        
        if overlap_ratio >= min_overlap:
            # Find the best matching passage (sentence or short paragraph)
            sentences = extract_sentences(result_text, min_length=20)
            best_passage = None
            best_passage_score = 0.0
            
            for sentence in sentences:
                sentence_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower()))
                sentence_overlap = len(claim_words & sentence_words)
                if total_claim_words > 0:
                    sentence_score = sentence_overlap / total_claim_words
                    if sentence_score > best_passage_score:
                        best_passage_score = sentence_score
                        best_passage = sentence
            
            # Compute token-level matches
            token_matches = compute_token_matches(claim, result_text)
            
            # Compute semantic similarity for relevance breakdown
            semantic_similarity = _compute_semantic_similarity(claim, result_text)
            
            # Compute relevance score breakdown
            relevance_breakdown = _compute_relevance_breakdown(
                claim,
                result_text,
                overlap_ratio,
                semantic_similarity,
                token_matches,
            )
            
            matches.append({
                "source": result.get("tool", "unknown"),
                "overlap_ratio": overlap_ratio,
                "matching_passage": best_passage or result_text[:200],
                "token_matches": token_matches,
                "result_text": result_text[:500],  # First 500 chars for context
                "semantic_similarity": semantic_similarity,
                "relevance_breakdown": relevance_breakdown,
            })
    
    # Sort by relevance score (better than just overlap)
    def get_sort_key(match):
        # Prefer relevance breakdown score, fallback to overlap
        breakdown = match.get("relevance_breakdown", {})
        if breakdown:
            return breakdown.get("overall_score", match.get("overlap_ratio", 0.0))
        return match.get("overlap_ratio", 0.0)
    
    matches.sort(key=get_sort_key, reverse=True)
    return matches


def extract_claims_from_response(
    response_text: str,
    max_claims: int = 10,
) -> List[Dict[str, Any]]:
    """
    Extract key claims (sentences) from response text.
    
    Returns list of claim dictionaries with position and text.
    """
    sentences = extract_sentences(response_text, min_length=30)
    
    # Filter to meaningful claims (not just filler)
    stop_phrases = [
        "for example", "in other words", "that is", "in summary",
        "in conclusion", "as we can see", "it is important",
    ]
    
    claims = []
    for i, sentence in enumerate(sentences[:max_claims]):
        sentence_lower = sentence.lower()
        # Skip if it's mostly stop phrases
        if any(phrase in sentence_lower for phrase in stop_phrases):
            continue
        
        # Skip very short sentences
        if len(sentence.split()) < 5:
            continue
        
        claims.append({
            "text": sentence,
            "position": i,
            "word_count": len(sentence.split()),
        })
    
    return claims


def build_provenance_map(
    response_text: str,
    research: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build comprehensive provenance map for response text.
    
    Maps each claim in response to:
    - Source results that support it
    - Token-level matches
    - Relevance scores
    - Alternative interpretations
    """
    if not research or not isinstance(research, dict):
        return {}
    
    # Extract all research results
    all_results = []
    subsolutions = research.get("subsolutions", [])
    for subsolution in subsolutions:
        if not isinstance(subsolution, dict):
            continue
        results = subsolution.get("results", [])
        if results:
            all_results.extend(results)
    
    if not all_results:
        return {}
    
    # Extract claims from response
    claims = extract_claims_from_response(response_text)
    
    # Match each claim to sources (prioritize higher quality claims)
    provenance_map = {}
    for claim_data in claims:
        claim_text = claim_data["text"]
        matches = match_claim_to_sources(claim_text, all_results)
        
        if matches:
            # Calculate claim-level relevance (average of top sources)
            top_source_relevance = 0.0
            if matches:
                top_source = matches[0]
                breakdown = top_source.get("relevance_breakdown", {})
                if breakdown:
                    top_source_relevance = breakdown.get("overall_score", top_source.get("overlap_ratio", 0.0))
                else:
                    top_source_relevance = top_source.get("overlap_ratio", 0.0)
            
            provenance_map[claim_text] = {
                "claim": claim_text,
                "position": claim_data["position"],
                "quality_score": claim_data.get("quality_score", 0.5),
                "sources": matches,
                "num_sources": len(matches),
                "top_source": matches[0] if matches else None,
                "top_source_relevance": top_source_relevance,
            }
    
    # Sort claims by combined quality (quality_score * relevance)
    # This ensures high-quality, well-supported claims appear first
    sorted_claims = sorted(
        provenance_map.items(),
        key=lambda x: (
            x[1].get("quality_score", 0.5) * x[1].get("top_source_relevance", 0.0),
            x[1].get("num_sources", 0)
        ),
        reverse=True
    )
    
    # Return as dict but with claims in quality order
    return dict(sorted_claims)

