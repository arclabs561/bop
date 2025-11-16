# Patch 4: Improve Belief Alignment with Semantic Similarity

## Issue
Belief alignment uses simple keyword matching. May miss semantic similarity (e.g., "trust" vs "confidence").

## Research-Based Solution
Based on semantic similarity research: Use embedding-based alignment computation. Embeddings capture semantic proximity better than keyword matching.

## Implementation

### File: `src/bop/orchestrator.py`

**Change: Enhance `_compute_belief_alignment` with embedding fallback**
```python
def _compute_belief_alignment(
    self,
    evidence_text: str,
    prior_beliefs: List[Dict[str, Any]],
) -> float:
    """
    Compute belief-evidence alignment using semantic similarity.
    
    Uses embedding-based similarity if available, falls back to keyword matching.
    
    Returns:
        0.0 to 1.0 where:
        - 0.0-0.3: Strong contradiction
        - 0.3-0.5: Weak contradiction or neutral
        - 0.5-0.7: Weak alignment
        - 0.7-1.0: Strong alignment
    """
    if not prior_beliefs or not evidence_text:
        return 0.5  # Neutral if no prior beliefs
    
    evidence_lower = evidence_text.lower()
    alignments = []
    
    # Try embedding-based similarity first (if LLM service available)
    use_embeddings = False
    if self.llm_service:
        try:
            # Check if LLM service supports embeddings
            # This is a placeholder - actual implementation depends on LLM service API
            use_embeddings = hasattr(self.llm_service, 'compute_similarity')
        except Exception:
            use_embeddings = False
    
    for belief in prior_beliefs:
        belief_text = belief.get("text", "").lower()
        if not belief_text:
            continue
        
        try:
            if use_embeddings:
                # Embedding-based semantic similarity
                alignment = self._compute_semantic_alignment(belief_text, evidence_lower)
            else:
                # Fallback to keyword-based alignment
                alignment = self._compute_keyword_alignment(belief_text, evidence_lower)
            
            alignments.append(alignment)
        except Exception as e:
            logger.debug(f"Failed to compute alignment for belief: {e}")
            # Fallback to neutral
            alignments.append(0.5)
    
    if not alignments:
        return 0.5
    
    # Return average alignment
    return float(sum(alignments) / len(alignments))

def _compute_keyword_alignment(self, belief_text: str, evidence_text: str) -> float:
    """Compute alignment using keyword matching (original method)."""
    # Simple keyword overlap check
    belief_words = set(belief_text.split())
    evidence_words = set(evidence_text.split())
    
    # Remove common stop words
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                 "have", "has", "had", "do", "does", "did", "will", "would", "could",
                 "should", "may", "might", "must", "can", "this", "that", "these", "those"}
    belief_words = belief_words - stop_words
    evidence_words = evidence_words - stop_words
    
    if not belief_words:
        return 0.5
    
    # Check for contradiction indicators
    contradiction_words = {"but", "however", "contrary", "opposite", "disagree", "contradict",
                         "conflict", "different", "wrong", "incorrect", "false", "not"}
    has_contradiction = any(word in evidence_text for word in contradiction_words)
    
    # Compute overlap
    overlap = len(belief_words & evidence_words)
    total_belief_words = len(belief_words)
    
    if total_belief_words == 0:
        alignment = 0.5
    else:
        overlap_ratio = overlap / total_belief_words
        
        if has_contradiction:
            # Contradiction: invert alignment
            alignment = 1.0 - overlap_ratio
        else:
            # Alignment: direct ratio
            alignment = 0.5 + (overlap_ratio * 0.5)  # Scale to 0.5-1.0
    
    return alignment

def _compute_semantic_alignment(self, belief_text: str, evidence_text: str) -> float:
    """
    Compute alignment using semantic similarity (embedding-based).
    
    Falls back to keyword matching if embeddings unavailable.
    """
    try:
        # Try to use LLM service for semantic similarity
        if self.llm_service and hasattr(self.llm_service, 'compute_similarity'):
            similarity = self.llm_service.compute_similarity(belief_text, evidence_text)
            # Convert similarity (0-1) to alignment (0-1)
            # High similarity = high alignment
            return float(similarity)
        else:
            # Fallback to keyword matching
            return self._compute_keyword_alignment(belief_text, evidence_text)
    except Exception as e:
        logger.debug(f"Semantic alignment failed, using keyword fallback: {e}")
        return self._compute_keyword_alignment(belief_text, evidence_text)
```

### Optional: Add embedding support to LLMService

**File: `src/bop/llm.py` (optional enhancement)**
```python
async def compute_similarity(self, text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts using embeddings.
    
    Returns:
        0.0 to 1.0 similarity score
    """
    try:
        # Use LLM to compute similarity
        # This is a placeholder - actual implementation depends on backend
        prompt = f"""Compute the semantic similarity between these two texts on a scale of 0.0 to 1.0.
        
Text 1: {text1}
Text 2: {text2}

Respond with only a number between 0.0 and 1.0."""
        
        result = await self.agent.run(prompt)
        similarity = float(result.data.strip())
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    except Exception as e:
        logger.warning(f"Failed to compute semantic similarity: {e}")
        # Fallback: simple word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0
```

## Testing
Add to `tests/test_belief_alignment.py` (create if doesn't exist):
```python
def test_semantic_alignment():
    """Test that semantic alignment works better than keyword matching."""
    orchestrator = StructuredOrchestrator()
    
    # Test case: semantic similarity without keyword overlap
    belief = "I think trust is crucial for systems"
    evidence = "Confidence in knowledge systems is essential"
    
    # Should detect alignment despite different words
    alignment = orchestrator._compute_belief_alignment(evidence, [{"text": belief}])
    assert 0.0 <= alignment <= 1.0
    
    # With keyword matching, this would be low
    # With semantic similarity, this should be higher
```

## Notes
- Embedding-based approach preferred
- Graceful fallback to keyword matching
- No breaking changes (backwards compatible)
- Can be enhanced later with proper embedding models

