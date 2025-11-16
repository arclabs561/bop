"""Semantic evaluation framework for producing transparent, aggregatable judgments."""

import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

import difflib


@dataclass
class SemanticJudgment:
    """A semantic judgment about a response."""
    
    query: str
    response: str
    judgment_type: str  # "accuracy", "completeness", "relevance", "consistency", etc.
    score: float  # 0.0 to 1.0
    reasoning: str
    evidence: List[str]
    confidence: float = 0.5
    timestamp: str = None
    metadata: Dict[str, Any] = None
    quality_flags: List[str] = None  # e.g., "placeholder", "error", "incomplete"
    query_characteristics: Dict[str, Any] = None  # e.g., complexity, length, type
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
        if self.quality_flags is None:
            self.quality_flags = []
        if self.query_characteristics is None:
            self.query_characteristics = {}


class SemanticEvaluator:
    """Evaluates semantic quality and produces transparent judgments."""
    
    # Quality indicators
    PLACEHOLDER_PATTERNS = [
        r"\[LLM service not available",
        r"\[MCP integration ready",
        r"Response to:",
        r"to be filled",
        r"placeholder",
    ]
    
    ERROR_PATTERNS = [
        r"error",
        r"failed",
        r"not available",
        r"please set",
    ]
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize semantic evaluator.
        
        Args:
            output_dir: Directory to save evaluation results
        """
        self.output_dir = output_dir or Path("eval_outputs")
        self.output_dir.mkdir(exist_ok=True)
        self.judgments: List[SemanticJudgment] = []
    
    def _analyze_query_characteristics(self, query: str) -> Dict[str, Any]:
        """Analyze query characteristics for better evaluation."""
        query_lower = query.lower().strip()
        
        # Length characteristics
        word_count = len(query_lower.split())
        char_count = len(query_lower)
        
        # Complexity indicators
        complexity_indicators = {
            "simple": word_count <= 3,
            "moderate": 4 <= word_count <= 8,
            "complex": word_count > 8,
        }
        complexity = next(k for k, v in complexity_indicators.items() if v)
        
        # Query type detection
        question_words = {"what", "how", "why", "when", "where", "who", "which"}
        has_question = any(qw in query_lower for qw in question_words)
        
        # Multi-part indicators
        multi_part_indicators = ["and", "or", "compare", "contrast", "versus", "vs", "between"]
        is_multi_part = any(ind in query_lower for ind in multi_part_indicators)
        
        # Abstract vs concrete
        abstract_indicators = ["philosophical", "theoretical", "conceptual", "abstract", "basis", "foundation"]
        is_abstract = any(ind in query_lower for ind in abstract_indicators)
        
        # Procedural indicators
        procedural_indicators = ["how to", "steps", "process", "calculate", "compute", "method"]
        is_procedural = any(ind in query_lower for ind in procedural_indicators)
        
        # Temporal indicators
        temporal_indicators = ["evolved", "history", "changed", "development", "progress"]
        has_temporal = any(ind in query_lower for ind in temporal_indicators)
        
        # Ambiguity detection
        is_ambiguous = word_count <= 2 or query_lower in ["?", "??"]
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "complexity": complexity,
            "has_question": has_question,
            "is_multi_part": is_multi_part,
            "is_abstract": is_abstract,
            "is_procedural": is_procedural,
            "has_temporal": has_temporal,
            "is_ambiguous": is_ambiguous,
        }
    
    def _detect_quality_issues(self, response: str, validation_issues: Optional[List[Any]] = None) -> List[str]:
        """
        Detect quality issues in response.
        
        Now integrates with validation issues for comprehensive quality assessment.
        """
        flags = []
        response_lower = response.lower()
        
        # Check for placeholders
        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE):
                flags.append("placeholder")
                break
        
        # Check for errors
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE):
                flags.append("error")
                break
        
        # Check for very short responses
        if len(response.strip()) < 50:
            flags.append("too_short")
        
        # Check for repetitive content
        words = response_lower.split()
        if len(words) > 10:
            word_counts = Counter(words)
            most_common_ratio = word_counts.most_common(1)[0][1] / len(words)
            if most_common_ratio > 0.3:
                flags.append("repetitive")
        
        # Check for echo (response just repeats query)
        if len(response.strip()) > 0:
            response_words = set(response_lower.split())
            # If response is mostly query words, it's likely an echo
            if len(response_words) < 10:  # Short response
                query_in_response = False  # Would need query to check
                # This is a heuristic - if response is very short and has few unique words
                if len(response_words) <= 3:
                    flags.append("echo")
        
        # Integrate validation issues as quality flags
        if validation_issues:
            for issue in validation_issues:
                # Convert ValidationIssue to quality flag
                if hasattr(issue, 'severity') and hasattr(issue, 'category'):
                    if issue.severity == "critical":
                        flags.append(f"validation_critical_{issue.category}")
                    elif issue.severity == "warning":
                        flags.append(f"validation_warning_{issue.category}")
                elif isinstance(issue, dict):
                    # Handle dict format (from metadata)
                    severity = issue.get("severity", "")
                    category = issue.get("category", "")
                    if severity == "critical":
                        flags.append(f"validation_critical_{category}")
                    elif severity == "warning":
                        flags.append(f"validation_warning_{category}")
        
        return flags
    
    def _extract_key_concepts(self, text: str, min_length: int = 5) -> Set[str]:
        """
        Extract key concepts from text using better heuristics.
        
        Filters out:
        - Common stop words
        - Very short words
        - Numbers
        - Punctuation-only
        """
        # Common stop words to exclude
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "what", "which", "who", "whom", "whose",
            "where", "when", "why", "how", "about", "into", "through", "during",
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Filter
        concepts = {
            w for w in words
            if w not in stop_words
            and len(w) >= min_length
            and not w.isdigit()
        }
        
        return concepts
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using multiple methods."""
        # Method 1: Sequence matcher
        seq_sim = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
        # Method 2: Word overlap (Jaccard)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if words1 or words2:
            jaccard = len(words1 & words2) / len(words1 | words2)
        else:
            jaccard = 0.0
        
        # Method 3: Concept overlap
        concepts1 = self._extract_key_concepts(text1)
        concepts2 = self._extract_key_concepts(text2)
        if concepts1 or concepts2:
            concept_overlap = len(concepts1 & concepts2) / len(concepts1 | concepts2) if (concepts1 | concepts2) else 0.0
        else:
            concept_overlap = 0.0
        
        # Weighted combination
        return (seq_sim * 0.3 + jaccard * 0.3 + concept_overlap * 0.4)
    
    def _adjust_score_for_query_complexity(
        self,
        base_score: float,
        query_characteristics: Dict[str, Any],
        response_length: int,
    ) -> float:
        """
        Adjust score based on query complexity and expected response characteristics.
        
        More complex queries should have longer, more detailed responses.
        """
        complexity = query_characteristics.get("complexity", "moderate")
        is_multi_part = query_characteristics.get("is_multi_part", False)
        is_abstract = query_characteristics.get("is_abstract", False)
        is_procedural = query_characteristics.get("is_procedural", False)
        
        # Expected minimum response length by complexity
        expected_lengths = {
            "simple": 50,
            "moderate": 150,
            "complex": 300,
        }
        expected_length = expected_lengths.get(complexity, 150)
        
        # Adjust for multi-part queries (need more content)
        if is_multi_part:
            expected_length *= 1.5
        
        # Adjust for abstract queries (may need more explanation)
        if is_abstract:
            expected_length *= 1.3
        
        # Adjust for procedural queries (need step-by-step)
        if is_procedural:
            expected_length *= 1.2
        
        # Penalize if response is too short for query complexity
        if response_length < expected_length * 0.5:
            # Response is less than half expected length
            length_penalty = 0.2
        elif response_length < expected_length * 0.8:
            # Response is 50-80% of expected length
            length_penalty = 0.1
        else:
            length_penalty = 0.0
        
        adjusted_score = max(0.0, base_score - length_penalty)
        return adjusted_score, length_penalty
    
    def evaluate_accuracy(
        self,
        query: str,
        response: str,
        expected_concepts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticJudgment:
        """
        Evaluate semantic accuracy of response.
        
        Improved to:
        - Check concept usage in context, not just presence
        - Account for quality issues
        - Provide more actionable reasoning
        - Adjust for query complexity
        """
        response_lower = response.lower()
        query_lower = query.lower()
        # Get validation issues from metadata if available
        validation_issues = None
        if metadata and isinstance(metadata, dict):
            # Check if validation issues were passed in metadata
            validation_issues = metadata.get("validation_issues")
        
        quality_flags = self._detect_quality_issues(response, validation_issues=validation_issues)
        query_chars = self._analyze_query_characteristics(query)
        
        # Penalize quality issues
        quality_penalty = 0.0
        if "placeholder" in quality_flags:
            quality_penalty = 0.5  # Major penalty for placeholders
        elif "error" in quality_flags:
            quality_penalty = 0.3
        elif "too_short" in quality_flags:
            quality_penalty = 0.2
        
        # Concept coverage - check if concepts appear AND are used meaningfully
        found_concepts = []
        concept_scores = []
        
        for concept in expected_concepts:
            concept_lower = concept.lower()
            # Check presence
            if concept_lower in response_lower:
                # Check if it's used in a meaningful way (not just in error messages)
                # Look for concept near other meaningful words
                pattern = rf'\b{re.escape(concept_lower)}\b'
                matches = list(re.finditer(pattern, response_lower))
                
                if matches:
                    # Check context around matches
                    meaningful_usage = False
                    context_words = {"is", "are", "refers", "means", "involves", "relates", "describes"}
                    
                    for match in matches:
                        start = max(0, match.start() - 20)
                        end = min(len(response_lower), match.end() + 20)
                        context = response_lower[start:end]
                        
                        # Check if concept appears with meaningful context
                        if any(cw in context for cw in context_words):
                            meaningful_usage = True
                            break
                        # Or if it's part of a longer phrase
                        if len(concept) > 5:  # Longer concepts are more likely to be meaningful
                            meaningful_usage = True
                            break
                    
                    if meaningful_usage:
                        found_concepts.append(concept)
                        concept_scores.append(1.0)
                    else:
                        # Concept present but not used meaningfully
                        found_concepts.append(concept)
                        concept_scores.append(0.5)
                else:
                    concept_scores.append(0.0)
            else:
                concept_scores.append(0.0)
        
        concept_coverage = sum(concept_scores) / len(expected_concepts) if expected_concepts else 0.0
        
        # Query relevance - improved to use semantic similarity
        query_relevance = self._calculate_semantic_similarity(query, response)
        
        # Completeness - check if response has substantial content
        # Not just length, but meaningful content
        response_concepts = self._extract_key_concepts(response)
        completeness = min(1.0, len(response_concepts) / 10.0)  # At least 10 unique concepts
        
        # Combined accuracy (with quality penalty)
        base_accuracy = (concept_coverage * 0.5 + query_relevance * 0.3 + completeness * 0.2)
        
        # Adjust for query complexity
        adjusted_score, length_penalty = self._adjust_score_for_query_complexity(
            base_accuracy,
            query_chars,
            len(response),
        )
        
        accuracy_score = max(0.0, adjusted_score - quality_penalty)
        
        # Build actionable reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Found {len(found_concepts)}/{len(expected_concepts)} expected concepts")
        
        if concept_scores:
            meaningful_count = sum(1 for s in concept_scores if s == 1.0)
            if meaningful_count < len(found_concepts):
                reasoning_parts.append(f"({meaningful_count} used meaningfully)")
        
        reasoning_parts.append(f"Query relevance: {query_relevance:.2f}")
        reasoning_parts.append(f"Content completeness: {completeness:.2f}")
        
        if length_penalty > 0:
            reasoning_parts.append(f"Length penalty for {query_chars['complexity']} query: -{length_penalty:.2f}")
        
        if quality_flags:
            reasoning_parts.append(f"Quality issues: {', '.join(quality_flags)}")
        
        if quality_penalty > 0:
            reasoning_parts.append(f"Quality penalty: -{quality_penalty:.2f}")
        
        reasoning = ". ".join(reasoning_parts) + "."
        
        # Better evidence - only meaningful concepts
        evidence = found_concepts[:5]  # Top concepts found
        if response_concepts:
            evidence.extend(list(response_concepts)[:3])  # Some response concepts
        
        judgment = SemanticJudgment(
            query=query,
            response=response[:500],  # Truncate for storage
            judgment_type="accuracy",
            score=accuracy_score,
            reasoning=reasoning,
            evidence=evidence,
            confidence=0.8 if accuracy_score > 0.7 and not quality_flags else 0.5,
            metadata=metadata or {},
            quality_flags=quality_flags,
            query_characteristics=query_chars,
        )
        
        self.judgments.append(judgment)
        return judgment
    
    def evaluate_completeness(
        self,
        query: str,
        response: str,
        content_context: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticJudgment:
        """
        Evaluate semantic completeness given context.
        
        Improved to:
        - Use key concepts instead of all words
        - Check for important concepts specifically
        - Account for summary nature (not all concepts needed)
        - Adjust for query type
        """
        # Get validation issues from metadata if available
        validation_issues = None
        if metadata and isinstance(metadata, dict):
            # Check if validation issues were passed in metadata
            validation_issues = metadata.get("validation_issues")
        
        quality_flags = self._detect_quality_issues(response, validation_issues=validation_issues)
        query_chars = self._analyze_query_characteristics(query)
        
        # Penalize quality issues
        quality_penalty = 0.0
        if "placeholder" in quality_flags:
            quality_penalty = 0.5
        elif "error" in quality_flags:
            quality_penalty = 0.3
        
        response_lower = response.lower()
        context_lower = content_context.lower()
        
        # Extract key concepts from context (not all words)
        context_concepts = self._extract_key_concepts(context_lower, min_length=5)
        response_concepts = self._extract_key_concepts(response_lower, min_length=5)
        
        # Coverage - how many context concepts appear in response
        # But weight by importance (frequency in context)
        context_word_freq = Counter(context_lower.split())
        important_concepts = {
            c for c in context_concepts
            if context_word_freq.get(c, 0) >= 2  # Appears at least twice
        }
        
        covered_important = important_concepts & response_concepts
        coverage_important = len(covered_important) / len(important_concepts) if important_concepts else 0.0
        
        # Also check general coverage
        covered_all = context_concepts & response_concepts
        coverage_all = len(covered_all) / len(context_concepts) if context_concepts else 0.0
        
        # For summaries, we don't need all concepts - weight important ones more
        # But adjust based on query type
        if query_chars.get("is_abstract") or query_chars.get("complexity") == "complex":
            # Complex/abstract queries may need more concepts
            coverage = (coverage_important * 0.6 + coverage_all * 0.4)
        else:
            # Standard weighting
            coverage = (coverage_important * 0.7 + coverage_all * 0.3)
        
        # Depth - check if response has substantial content
        # Use concept count, not just length
        expected_concepts = 15 if query_chars.get("complexity") == "complex" else 10
        depth_score = min(1.0, len(response_concepts) / expected_concepts)
        
        # Check if response addresses the query type
        query_lower = query.lower()
        if "summarize" in query_lower or "summary" in query_lower:
            # For summaries, check for summary indicators
            summary_indicators = ["key", "main", "important", "overview", "summary"]
            has_summary_structure = any(ind in response_lower for ind in summary_indicators)
            structure_bonus = 0.1 if has_summary_structure else 0.0
        else:
            structure_bonus = 0.0
        
        base_completeness = (coverage * 0.5 + depth_score * 0.4 + structure_bonus)
        
        # Adjust for query complexity
        adjusted_score, length_penalty = self._adjust_score_for_query_complexity(
            base_completeness,
            query_chars,
            len(response),
        )
        
        completeness_score = max(0.0, adjusted_score - quality_penalty)
        
        # Build actionable reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Covered {len(covered_important)}/{len(important_concepts)} important context concepts")
        reasoning_parts.append(f"({len(covered_all)}/{len(context_concepts)} total concepts)")
        reasoning_parts.append(f"Response depth: {len(response_concepts)} unique concepts")
        
        if length_penalty > 0:
            reasoning_parts.append(f"Length penalty for {query_chars['complexity']} query: -{length_penalty:.2f}")
        
        if quality_flags:
            reasoning_parts.append(f"Quality issues: {', '.join(quality_flags)}")
        
        if quality_penalty > 0:
            reasoning_parts.append(f"Quality penalty: -{quality_penalty:.2f}")
        
        reasoning = ". ".join(reasoning_parts) + "."
        
        # Evidence - important concepts covered
        evidence = list(covered_important)[:10]
        if not evidence:
            evidence = list(covered_all)[:5]
        
        judgment = SemanticJudgment(
            query=query,
            response=response[:500],
            judgment_type="completeness",
            score=completeness_score,
            reasoning=reasoning,
            evidence=evidence,
            confidence=0.7 if completeness_score > 0.5 and not quality_flags else 0.5,
            metadata=metadata or {},
            quality_flags=quality_flags,
            query_characteristics=query_chars,
        )
        
        self.judgments.append(judgment)
        return judgment
    
    def evaluate_relevance(
        self,
        query: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticJudgment:
        """
        Evaluate semantic relevance to query.
        
        Improved to:
        - Use better semantic similarity
        - Detect placeholder responses
        - Check for actual answer content
        - Adjust for query complexity and type
        """
        # Get validation issues from metadata if available
        validation_issues = None
        if metadata and isinstance(metadata, dict):
            # Check if validation issues were passed in metadata
            validation_issues = metadata.get("validation_issues")
        
        quality_flags = self._detect_quality_issues(response, validation_issues=validation_issues)
        query_chars = self._analyze_query_characteristics(query)
        
        # Major penalty for placeholders/errors (but still evaluate)
        quality_penalty = 0.0
        if "placeholder" in quality_flags:
            quality_penalty = 0.6  # Major penalty
        elif "error" in quality_flags:
            quality_penalty = 0.4
        
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Improved semantic similarity
        similarity = self._calculate_semantic_similarity(query, response)
        
        # Keyword overlap - but only meaningful words
        query_concepts = self._extract_key_concepts(query_lower)
        response_concepts = self._extract_key_concepts(response_lower)
        
        if query_concepts:
            overlap = len(query_concepts & response_concepts) / len(query_concepts)
        else:
            overlap = 0.0
        
        # Answer structure - check if response actually answers
        # Adjust expectations based on query type
        answer_score = 1.0
        if query_chars.get("has_question"):
            # Check for answer indicators
            answer_indicators = ["because", "is", "are", "refers", "means", "involves", "consists", "describes"]
            has_answer = any(indicator in response_lower for indicator in answer_indicators)
            
            # Also check if response has substantial content (not just echoing query)
            min_ratio = 1.2 if query_chars.get("complexity") == "simple" else 1.5
            if len(response_lower) > len(query_lower) * min_ratio:
                has_substantial_content = True
            else:
                has_substantial_content = False
            
            if has_answer and has_substantial_content:
                answer_score = 1.0
            elif has_answer or has_substantial_content:
                answer_score = 0.7
            else:
                answer_score = 0.4
        
        # Special handling for multi-part queries
        if query_chars.get("is_multi_part"):
            # Multi-part queries should address multiple aspects
            multi_part_indicators = ["compare", "contrast", "and", "versus", "vs", "between"]
            addresses_multiple = sum(1 for ind in multi_part_indicators if ind in response_lower)
            if addresses_multiple >= 2:
                answer_score = min(1.0, answer_score + 0.1)  # Bonus for addressing multiple parts
        
        # Special handling for procedural queries
        if query_chars.get("is_procedural"):
            procedural_indicators = ["step", "first", "then", "next", "finally", "process", "method"]
            has_procedural_structure = sum(1 for ind in procedural_indicators if ind in response_lower)
            if has_procedural_structure >= 2:
                answer_score = min(1.0, answer_score + 0.1)  # Bonus for procedural structure
        
        base_relevance = (similarity * 0.4 + overlap * 0.4 + answer_score * 0.2)
        
        # Adjust for query complexity
        adjusted_score, length_penalty = self._adjust_score_for_query_complexity(
            base_relevance,
            query_chars,
            len(response),
        )
        
        relevance_score = max(0.0, adjusted_score - quality_penalty)
        
        reasoning_parts = [
            f"Semantic similarity: {similarity:.2f}",
            f"Concept overlap: {overlap:.2f} ({len(query_concepts & response_concepts)}/{len(query_concepts)} concepts)",
            f"Answer structure: {answer_score:.2f}",
        ]
        
        if length_penalty > 0:
            reasoning_parts.append(f"Length penalty for {query_chars['complexity']} query: -{length_penalty:.2f}")
        
        if quality_flags:
            reasoning_parts.append(f"Quality issues: {', '.join(quality_flags)}")
        
        if quality_penalty > 0:
            reasoning_parts.append(f"Quality penalty: -{quality_penalty:.2f}")
        
        reasoning = ". ".join(reasoning_parts) + "."
        
        evidence = list(query_concepts & response_concepts)[:10]
        
        judgment = SemanticJudgment(
            query=query,
            response=response[:500],
            judgment_type="relevance",
            score=relevance_score,
            reasoning=reasoning,
            evidence=evidence,
            confidence=0.8 if relevance_score > 0.6 and not quality_flags else 0.5,
            metadata=metadata or {},
            quality_flags=quality_flags,
            query_characteristics=query_chars,
        )
        
        self.judgments.append(judgment)
        return judgment
    
    def evaluate_consistency(
        self,
        query: str,
        responses: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticJudgment:
        """
        Evaluate consistency across multiple responses to same query.
        
        Improved to:
        - Account for quality issues
        - Use concept-based comparison
        - Consider query complexity
        """
        if len(responses) < 2:
            return SemanticJudgment(
                query=query,
                response="",
                judgment_type="consistency",
                score=1.0,
                reasoning="Only one response, cannot evaluate consistency",
                evidence=[],
                metadata=metadata or {},
                query_characteristics=self._analyze_query_characteristics(query),
            )
        
        query_chars = self._analyze_query_characteristics(query)
        
        # Check for quality issues
        quality_flags_all = [self._detect_quality_issues(r) for r in responses]
        has_quality_issues = any(flags for flags in quality_flags_all)
        
        if has_quality_issues:
            # If responses have quality issues, consistency is less meaningful
            # But we can still check if they're consistently bad
            all_placeholders = all("placeholder" in flags for flags in quality_flags_all)
            if all_placeholders:
                return SemanticJudgment(
                    query=query,
                    response=f"{len(responses)} responses compared",
                    judgment_type="consistency",
                    score=1.0,  # Consistently placeholders
                    reasoning="All responses are placeholders - consistent but not meaningful",
                    evidence=[],
                    confidence=0.5,
                    metadata=metadata or {},
                    quality_flags=["placeholder"],
                    query_characteristics=query_chars,
                )
        
        # Extract concepts from each response
        response_concepts = [self._extract_key_concepts(r.lower()) for r in responses]
        
        # Pairwise similarities using concepts
        similarities = []
        for i in range(len(response_concepts)):
            for j in range(i + 1, len(response_concepts)):
                # Concept overlap
                concepts_i = response_concepts[i]
                concepts_j = response_concepts[j]
                if concepts_i or concepts_j:
                    concept_overlap = len(concepts_i & concepts_j) / len(concepts_i | concepts_j) if (concepts_i | concepts_j) else 0.0
                else:
                    concept_overlap = 0.0
                
                # Text similarity
                text_sim = difflib.SequenceMatcher(None, responses[i].lower(), responses[j].lower()).ratio()
                
                # Combined
                sim = (concept_overlap * 0.6 + text_sim * 0.4)
                similarities.append(sim)
        
        consistency_score = sum(similarities) / len(similarities) if similarities else 0.0
        
        # Adjust for query complexity - complex queries may have more variation
        if query_chars.get("complexity") == "complex" or query_chars.get("is_abstract"):
            # Slightly more lenient for complex queries
            consistency_score = min(1.0, consistency_score * 1.1)
        
        reasoning = (
            f"Average pairwise similarity: {consistency_score:.2f} "
            f"across {len(responses)} responses. "
            f"Based on concept overlap and text similarity."
        )
        
        if has_quality_issues:
            reasoning += f" Some responses have quality issues."
        
        if query_chars.get("complexity") == "complex":
            reasoning += f" Adjusted for complex query."
        
        evidence = [f"Response {i+1}" for i in range(len(responses))]
        
        judgment = SemanticJudgment(
            query=query,
            response=f"{len(responses)} responses compared",
            judgment_type="consistency",
            score=consistency_score,
            reasoning=reasoning,
            evidence=evidence,
            confidence=0.7 if consistency_score > 0.5 and not has_quality_issues else 0.5,
            metadata=metadata or {},
            quality_flags=[] if not has_quality_issues else ["mixed_quality"],
            query_characteristics=query_chars,
        )
        
        self.judgments.append(judgment)
        return judgment
    
    def aggregate_judgments(self) -> Dict[str, Any]:
        """
        Aggregate all judgments into summary statistics.
        
        Enhanced to include quality flag statistics and query characteristics.
        """
        if not self.judgments:
            return {"error": "No judgments to aggregate"}
        
        # Group by judgment type
        by_type = defaultdict(list)
        for judgment in self.judgments:
            by_type[judgment.judgment_type].append(judgment.score)
        
        # Overall statistics
        all_scores = [j.score for j in self.judgments]
        
        # Statistics by type
        type_stats = {}
        for j_type, scores in by_type.items():
            type_stats[j_type] = {
                "count": len(scores),
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "std": self._std_dev(scores),
            }
        
        # Confidence statistics
        confidences = [j.confidence for j in self.judgments]
        
        # Quality flag statistics
        quality_flag_counts = Counter()
        for judgment in self.judgments:
            quality_flag_counts.update(judgment.quality_flags)
        
        # Query characteristics aggregation
        complexity_dist = Counter()
        query_types = Counter()
        for judgment in self.judgments:
            if judgment.query_characteristics:
                complexity_dist[judgment.query_characteristics.get("complexity", "unknown")] += 1
                if judgment.query_characteristics.get("has_question"):
                    query_types["question"] += 1
                if judgment.query_characteristics.get("is_multi_part"):
                    query_types["multi_part"] += 1
                if judgment.query_characteristics.get("is_abstract"):
                    query_types["abstract"] += 1
                if judgment.query_characteristics.get("is_procedural"):
                    query_types["procedural"] += 1
        
        # Metadata aggregation
        metadata_keys = set()
        for judgment in self.judgments:
            metadata_keys.update(judgment.metadata.keys())
        
        metadata_stats = {}
        for key in metadata_keys:
            values = [j.metadata.get(key) for j in self.judgments if key in j.metadata]
            if values:
                metadata_stats[key] = {
                    "count": len(values),
                    "unique_values": len(set(str(v) for v in values)),
                }
        
        # Quality distribution
        quality_distribution = {
            "with_issues": sum(1 for j in self.judgments if j.quality_flags),
            "without_issues": sum(1 for j in self.judgments if not j.quality_flags),
            "flag_counts": dict(quality_flag_counts),
        }
        
        return {
            "total_judgments": len(self.judgments),
            "overall": {
                "mean_score": sum(all_scores) / len(all_scores),
                "min_score": min(all_scores),
                "max_score": max(all_scores),
                "std_score": self._std_dev(all_scores),
            },
            "by_type": type_stats,
            "confidence": {
                "mean": sum(confidences) / len(confidences),
                "min": min(confidences),
                "max": max(confidences),
            },
            "quality": quality_distribution,
            "query_characteristics": {
                "complexity_distribution": dict(complexity_dist),
                "query_type_distribution": dict(query_types),
            },
            "metadata_summary": metadata_stats,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def save_judgments_json(self, filename: str = "semantic_judgments.json") -> Path:
        """Save all judgments as JSON."""
        output_path = self.output_dir / filename
        data = {
            "judgments": [asdict(j) for j in self.judgments],
            "aggregate": self.aggregate_judgments(),
        }
        output_path.write_text(json.dumps(data, indent=2))
        return output_path
    
    def save_judgments_csv(self, filename: str = "semantic_judgments.csv") -> Path:
        """Save judgments as CSV for easy analysis."""
        output_path = self.output_dir / filename
        
        if not self.judgments:
            return output_path
        
        # Collect all metadata keys across all judgments
        base_fieldnames = [
            "timestamp",
            "query",
            "judgment_type",
            "score",
            "confidence",
            "reasoning",
            "evidence_count",
            "quality_flags",
            "query_complexity",
            "query_word_count",
        ]
        
        metadata_keys = set()
        for judgment in self.judgments:
            metadata_keys.update(judgment.metadata.keys())
        
        fieldnames = base_fieldnames + sorted(metadata_keys)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for judgment in self.judgments:
                row = {
                    "timestamp": judgment.timestamp,
                    "query": judgment.query[:100],  # Truncate
                    "judgment_type": judgment.judgment_type,
                    "score": judgment.score,
                    "confidence": judgment.confidence,
                    "reasoning": judgment.reasoning[:200],  # Truncate
                    "evidence_count": len(judgment.evidence),
                    "quality_flags": ",".join(judgment.quality_flags) if judgment.quality_flags else "",
                    "query_complexity": judgment.query_characteristics.get("complexity", "") if judgment.query_characteristics else "",
                    "query_word_count": judgment.query_characteristics.get("word_count", 0) if judgment.query_characteristics else 0,
                }
                # Add metadata fields (only those in fieldnames)
                for key in metadata_keys:
                    row[key] = judgment.metadata.get(key, "")
                writer.writerow(row)
        
        return output_path
    
    def save_summary_report(self, filename: str = "semantic_eval_report.md") -> Path:
        """Save human-readable summary report."""
        output_path = self.output_dir / filename
        
        aggregate = self.aggregate_judgments()
        
        report = f"""# Semantic Evaluation Report

Generated: {aggregate.get('timestamp', 'Unknown')}

## Summary

- **Total Judgments**: {aggregate.get('total_judgments', 0)}
- **Overall Mean Score**: {aggregate.get('overall', {}).get('mean_score', 0):.3f}
- **Score Range**: {aggregate.get('overall', {}).get('min_score', 0):.3f} - {aggregate.get('overall', {}).get('max_score', 0):.3f}
- **Standard Deviation**: {aggregate.get('overall', {}).get('std_score', 0):.3f}

## Quality Issues

"""
        
        quality = aggregate.get('quality', {})
        total = aggregate.get('total_judgments', 0)
        with_issues = quality.get('with_issues', 0)
        without_issues = quality.get('without_issues', 0)
        
        report += f"- **Judgments with quality issues**: {with_issues}/{total} ({with_issues/total*100:.1f}%)\n"
        report += f"- **Judgments without issues**: {without_issues}/{total} ({without_issues/total*100:.1f}%)\n"
        
        flag_counts = quality.get('flag_counts', {})
        if flag_counts:
            report += "\n**Quality Flag Distribution:**\n"
            for flag, count in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True):
                report += f"- `{flag}`: {count} occurrences\n"
        
        # Query characteristics
        query_chars = aggregate.get('query_characteristics', {})
        if query_chars:
            report += "\n## Query Characteristics\n\n"
            
            complexity_dist = query_chars.get('complexity_distribution', {})
            if complexity_dist:
                report += "**Complexity Distribution:**\n"
                for complexity, count in sorted(complexity_dist.items()):
                    report += f"- {complexity}: {count} queries\n"
            
            query_type_dist = query_chars.get('query_type_distribution', {})
            if query_type_dist:
                report += "\n**Query Type Distribution:**\n"
                for q_type, count in sorted(query_type_dist.items(), key=lambda x: x[1], reverse=True):
                    report += f"- {q_type}: {count} queries\n"
        
        report += "\n## By Judgment Type\n\n"
        
        for j_type, stats in aggregate.get('by_type', {}).items():
            report += f"""### {j_type.title()}

- **Count**: {stats['count']}
- **Mean**: {stats['mean']:.3f}
- **Range**: {stats['min']:.3f} - {stats['max']:.3f}
- **Std Dev**: {stats['std']:.3f}

"""
        
        report += f"""## Confidence

- **Mean Confidence**: {aggregate.get('confidence', {}).get('mean', 0):.3f}
- **Range**: {aggregate.get('confidence', {}).get('min', 0):.3f} - {aggregate.get('confidence', {}).get('max', 0):.3f}

## Metadata Summary

"""
        
        for key, stats in aggregate.get('metadata_summary', {}).items():
            report += f"- **{key}**: {stats['count']} occurrences, {stats['unique_values']} unique values\n"
        
        report += f"""
## Recommendations

Based on the evaluation results:

"""
        
        # Generate recommendations
        overall_mean = aggregate.get('overall', {}).get('mean_score', 0)
        if overall_mean < 0.5:
            report += "- ⚠️ **Low overall scores**: Consider improving response quality or query formulation\n"
        elif overall_mean < 0.7:
            report += "- ⚠️ **Moderate scores**: Some improvement needed\n"
        else:
            report += "- ✅ **Good overall scores**: System performing well\n"
        
        # Quality issues recommendation
        if with_issues > total * 0.3:  # More than 30% have issues
            report += f"- ⚠️ **High rate of quality issues** ({with_issues/total*100:.1f}%): Review system configuration and error handling\n"
        
        # Query complexity insights
        complexity_dist = query_chars.get('complexity_distribution', {})
        if complexity_dist:
            complex_count = complexity_dist.get('complex', 0)
            if complex_count > 0:
                report += f"- 📊 **Complex queries tested**: {complex_count} - ensure responses are appropriately detailed\n"
        
        # Check consistency
        consistency_scores = [
            j.score for j in self.judgments
            if j.judgment_type == "consistency"
        ]
        if consistency_scores:
            avg_consistency = sum(consistency_scores) / len(consistency_scores)
            if avg_consistency < 0.6:
                report += "- ⚠️ **Low consistency**: Responses vary significantly across schemas/methods\n"
            else:
                report += "- ✅ **Good consistency**: Responses are consistent across methods\n"
        
        output_path.write_text(report)
        return output_path
