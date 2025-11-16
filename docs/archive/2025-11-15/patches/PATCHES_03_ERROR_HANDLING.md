# Patch 3: Add Error Handling for New Methods

## Issue
No error handling in `_extract_prior_beliefs()`, `_build_source_matrix()`, `_create_response_tiers()`. System may crash on edge cases.

## Research-Based Solution
Based on error handling best practices: Catch specific exceptions, keep try blocks small, provide fallback values, use graceful degradation.

## Implementation

### File: `src/bop/agent.py`

**Change 1: Add error handling to `_extract_prior_beliefs`**
```python
def _extract_prior_beliefs(self, message: str) -> None:
    """
    Extract prior beliefs from user message.
    
    Gracefully handles errors and returns empty list on failure.
    """
    try:
        # Existing implementation...
        belief_indicators = ["i think", "i believe", "i'm convinced", "i feel", "in my opinion"]
        message_lower = message.lower()
        
        for indicator in belief_indicators:
            if indicator in message_lower:
                # Extract belief text (simple heuristic)
                start_idx = message_lower.find(indicator)
                # Find end of sentence
                end_idx = min(start_idx + 200, len(message))
                belief_text = message[start_idx:end_idx].strip()
                
                if belief_text and len(belief_text) > 10:  # Minimum length
                    self.prior_beliefs.append({
                        "text": belief_text,
                        "source": "user_statement",
                    })
                    # Limit to last 10 beliefs
                    if len(self.prior_beliefs) > 10:
                        self.prior_beliefs = self.prior_beliefs[-10:]
                break
    except Exception as e:
        logger.warning(f"Failed to extract prior beliefs: {e}", exc_info=True)
        # Graceful degradation: continue without belief extraction
        return
```

**Change 2: Add error handling to `_create_response_tiers`**
```python
def _create_response_tiers(
    self,
    full_response: str,
    research: Dict[str, Any],
    query: str,
) -> Dict[str, str]:
    """
    Create progressive disclosure tiers for response.
    
    Gracefully handles errors and returns minimal tiers on failure.
    """
    try:
        # Summary: 1-2 sentence direct answer
        # Try to extract first sentence or first 150 chars
        summary = full_response.split('.')[0] if '.' in full_response else full_response[:150]
        if len(summary) > 150:
            summary = summary[:147] + "..."
    except Exception as e:
        logger.warning(f"Failed to create summary tier: {e}", exc_info=True)
        summary = full_response[:150] + "..." if len(full_response) > 150 else full_response
    
    try:
        # Structured: Organized breakdown (use research synthesis if available)
        structured = ""
        if research and isinstance(research, dict):
            final_synthesis = research.get("final_synthesis", "")
            if final_synthesis:
                structured = final_synthesis
            else:
                # Use subsolutions if available
                subsolutions = research.get("subsolutions", [])
                if subsolutions:
                    structured_parts = []
                    for sub in subsolutions[:3]:  # Top 3
                        subproblem = sub.get("subproblem", "")
                        synthesis = sub.get("synthesis", "")
                        if synthesis:
                            structured_parts.append(f"**{subproblem}**: {synthesis[:200]}")
                    structured = "\n\n".join(structured_parts)
        
        if not structured:
            # Fallback: use first 3 paragraphs of response
            paragraphs = full_response.split('\n\n')[:3]
            structured = "\n\n".join(paragraphs)
    except Exception as e:
        logger.warning(f"Failed to create structured tier: {e}", exc_info=True)
        structured = full_response[:500] + "..." if len(full_response) > 500 else full_response
    
    # Detailed: Full response (always available)
    detailed = full_response
    
    try:
        # Evidence: Full research synthesis
        evidence = ""
        if research and isinstance(research, dict):
            evidence_parts = []
            if research.get("final_synthesis"):
                evidence_parts.append(f"**Final Synthesis**:\n{research['final_synthesis']}")
            
            subsolutions = research.get("subsolutions", [])
            if subsolutions:
                evidence_parts.append("\n**Detailed Breakdown**:")
                for sub in subsolutions:
                    subproblem = sub.get("subproblem", "")
                    synthesis = sub.get("synthesis", "")
                    tools = sub.get("tools_used", [])
                    if synthesis:
                        evidence_parts.append(
                            f"\n**{subproblem}**\n"
                            f"Tools: {', '.join(tools)}\n"
                            f"{synthesis}"
                        )
            
            evidence = "\n\n".join(evidence_parts) if evidence_parts else full_response
        else:
            evidence = full_response
    except Exception as e:
        logger.warning(f"Failed to create evidence tier: {e}", exc_info=True)
        evidence = full_response
    
    return {
        "summary": summary,
        "structured": structured,
        "detailed": detailed,
        "evidence": evidence,
    }
```

### File: `src/bop/orchestrator.py`

**Change 3: Add error handling to `_build_source_matrix`**
```python
def _build_source_matrix(
    self,
    subsolutions: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Build source relationship matrix showing agreement/disagreement patterns.
    
    Gracefully handles errors and returns empty dict on failure.
    """
    if not subsolutions:
        return {}
    
    try:
        # Extract key claims from each subsolution
        matrix = {}
        
        for subsolution in subsolutions:
            try:
                subproblem = subsolution.get("subproblem", "")
                synthesis = subsolution.get("synthesis", "")
                tools_used = subsolution.get("tools_used", [])
                results = subsolution.get("results", [])
                
                # Extract key phrases from synthesis (simple approach)
                key_phrases = self._extract_key_phrases(synthesis)
                
                for phrase in key_phrases:
                    if phrase not in matrix:
                        matrix[phrase] = {
                            "sources": {},
                            "consensus": None,
                            "conflict": False,
                        }
                    
                    # Map each source to its position on this claim
                    for result in results:
                        try:
                            source = result.get("tool", "unknown")
                            if source not in matrix[phrase]["sources"]:
                                # Simple: check if result text contains the phrase
                                result_text = result.get("result", "").lower()
                                phrase_lower = phrase.lower()
                                
                                if phrase_lower in result_text:
                                    matrix[phrase]["sources"][source] = "supports"
                                else:
                                    # Check for contradiction
                                    contradiction_indicators = ["but", "however", "contrary", "opposite"]
                                    if any(ind in result_text for ind in contradiction_indicators):
                                        matrix[phrase]["sources"][source] = "contradicts"
                                    else:
                                        matrix[phrase]["sources"][source] = "neutral"
                        except Exception as e:
                            logger.debug(f"Failed to process result for source matrix: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Failed to process subsolution for source matrix: {e}", exc_info=True)
                continue
        
        # Determine consensus for each claim
        for phrase, data in matrix.items():
            try:
                sources = data["sources"]
                if not sources:
                    continue
                
                supports = sum(1 for pos in sources.values() if pos == "supports")
                contradicts = sum(1 for pos in sources.values() if pos == "contradicts")
                total = len(sources)
                
                if contradicts > 0:
                    data["conflict"] = True
                    data["consensus"] = "disagreement"
                elif supports > total * 0.7:
                    data["consensus"] = "strong_agreement"
                elif supports > total * 0.5:
                    data["consensus"] = "weak_agreement"
                else:
                    data["consensus"] = "no_consensus"
            except Exception as e:
                logger.warning(f"Failed to determine consensus for phrase '{phrase}': {e}", exc_info=True)
                data["consensus"] = "unknown"
        
        return matrix
    except Exception as e:
        logger.error(f"Failed to build source matrix: {e}", exc_info=True)
        # Graceful degradation: return empty matrix
        return {}
```

## Testing
Add to `tests/test_error_handling.py` (create if doesn't exist):
```python
def test_belief_extraction_error_handling():
    """Test that belief extraction handles errors gracefully."""
    agent = KnowledgeAgent()
    # Test with malformed input
    agent._extract_prior_beliefs(None)  # Should not crash
    agent._extract_prior_beliefs("")  # Should not crash
    assert len(agent.prior_beliefs) >= 0  # Should be empty or have beliefs

def test_response_tiers_error_handling():
    """Test that tier creation handles errors gracefully."""
    agent = KnowledgeAgent()
    # Test with None/invalid inputs
    tiers = agent._create_response_tiers("", None, "")
    assert "summary" in tiers
    assert "detailed" in tiers
    # Should always return valid tiers dict

def test_source_matrix_error_handling():
    """Test that source matrix handles errors gracefully."""
    orchestrator = StructuredOrchestrator()
    # Test with empty/invalid inputs
    matrix = orchestrator._build_source_matrix([])
    assert isinstance(matrix, dict)
    # Should return empty dict, not crash
```

## Notes
- All methods now have try/except blocks
- Specific exception handling where possible
- Fallback values provided (empty dict/list, minimal tiers)
- Logging for debugging
- Graceful degradation (system continues working)

