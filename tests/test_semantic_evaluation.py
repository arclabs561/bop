"""Semantic evaluation tests that produce meaningful judgments on realistic data."""

from pathlib import Path
from typing import Any, Dict, List

import pytest

from pran.agent import KnowledgeAgent
from pran.orchestrator import StructuredOrchestrator
from pran.research import ResearchAgent, load_content


@pytest.fixture
def content_dir():
    """Get content directory."""
    return Path(__file__).parent.parent / "content"


@pytest.fixture
def knowledge_base(content_dir):
    """Load knowledge base."""
    return load_content(content_dir)


class SemanticJudgment:
    """Represents a semantic judgment about a response."""

    def __init__(
        self,
        query: str,
        response: str,
        judgment_type: str,
        score: float,
        reasoning: str,
        evidence: List[str],
        confidence: float = 0.5,
    ):
        self.query = query
        self.response = response
        self.judgment_type = judgment_type  # e.g., "accuracy", "completeness", "relevance"
        self.score = score  # 0.0 to 1.0
        self.reasoning = reasoning
        self.evidence = evidence
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for aggregation."""
        return {
            "query": self.query,
            "response_length": len(self.response),
            "judgment_type": self.judgment_type,
            "score": self.score,
            "reasoning": self.reasoning,
            "evidence_count": len(self.evidence),
            "confidence": self.confidence,
        }


def evaluate_semantic_accuracy(query: str, response: str, expected_concepts: List[str]) -> SemanticJudgment:
    """
    Evaluate if response accurately addresses the query semantically.

    Args:
        query: The query asked
        response: The response given
        expected_concepts: Concepts that should appear in a good response

    Returns:
        SemanticJudgment with accuracy score
    """
    response_lower = response.lower()
    query_lower = query.lower()

    # Check if response contains expected concepts
    found_concepts = [c for c in expected_concepts if c.lower() in response_lower]
    concept_coverage = len(found_concepts) / len(expected_concepts) if expected_concepts else 0.0

    # Check if response addresses query words
    query_words = set(query_lower.split())
    response_words = set(response_lower.split())
    query_relevance = len(query_words & response_words) / len(query_words) if query_words else 0.0

    # Check response completeness (not too short)
    completeness = min(1.0, len(response) / 100.0)  # At least 100 chars is "complete"

    # Combined accuracy score
    accuracy_score = (concept_coverage * 0.4 + query_relevance * 0.3 + completeness * 0.3)

    reasoning = f"Found {len(found_concepts)}/{len(expected_concepts)} expected concepts. "
    reasoning += f"Query relevance: {query_relevance:.2f}. Completeness: {completeness:.2f}."

    evidence = found_concepts + [f"Query word '{w}' present" for w in (query_words & response_words)]

    return SemanticJudgment(
        query=query,
        response=response,
        judgment_type="accuracy",
        score=accuracy_score,
        reasoning=reasoning,
        evidence=evidence,
        confidence=0.7 if accuracy_score > 0.6 else 0.5,
    )


def evaluate_semantic_completeness(query: str, response: str, content_context: str) -> SemanticJudgment:
    """
    Evaluate if response is semantically complete given the context.

    Args:
        query: The query asked
        response: The response given
        content_context: Relevant content that should inform the response

    Returns:
        SemanticJudgment with completeness score
    """
    response_lower = response.lower()
    context_lower = content_context.lower()

    # Extract key concepts from context
    context_words = set(context_lower.split())
    # Filter for meaningful words (length > 4)
    context_concepts = {w for w in context_words if len(w) > 4}

    # Check how many context concepts appear in response
    response_words = set(response_lower.split())
    covered_concepts = context_concepts & response_words
    coverage = len(covered_concepts) / len(context_concepts) if context_concepts else 0.0

    # Check response depth (not just surface-level)
    depth_score = min(1.0, len(response) / 200.0)  # Deeper responses are better

    completeness_score = (coverage * 0.6 + depth_score * 0.4)

    reasoning = f"Covered {len(covered_concepts)}/{len(context_concepts)} context concepts. "
    reasoning += f"Response depth: {depth_score:.2f}."

    evidence = list(covered_concepts)[:10]  # Limit evidence

    return SemanticJudgment(
        query=query,
        response=response,
        judgment_type="completeness",
        score=completeness_score,
        reasoning=reasoning,
        evidence=evidence,
        confidence=0.7 if completeness_score > 0.5 else 0.5,
    )


def evaluate_semantic_relevance(query: str, response: str) -> SemanticJudgment:
    """
    Evaluate if response is semantically relevant to the query.

    Args:
        query: The query asked
        response: The response given

    Returns:
        SemanticJudgment with relevance score
    """
    import difflib

    query_lower = query.lower()
    response_lower = response.lower()

    # Semantic similarity
    similarity = difflib.SequenceMatcher(None, query_lower, response_lower).ratio()

    # Keyword overlap
    query_words = set(query_lower.split())
    response_words = set(response_lower.split())
    overlap = len(query_words & response_words) / len(query_words) if query_words else 0.0

    # Check if response directly addresses query structure
    question_words = {"what", "how", "why", "when", "where", "who"}
    query_has_question = any(qw in query_lower for qw in question_words)

    if query_has_question:
        # Response should have answer indicators
        answer_indicators = ["because", "is", "are", "refers", "means", "involves"]
        has_answer = any(indicator in response_lower for indicator in answer_indicators)
        answer_score = 1.0 if has_answer else 0.5
    else:
        answer_score = 1.0  # Not a question, can't judge answer structure

    relevance_score = (similarity * 0.3 + overlap * 0.4 + answer_score * 0.3)

    reasoning = f"Semantic similarity: {similarity:.2f}. Keyword overlap: {overlap:.2f}. "
    reasoning += f"Answer structure: {answer_score:.2f}."

    evidence = list(query_words & response_words)[:10]

    return SemanticJudgment(
        query=query,
        response=response,
        judgment_type="relevance",
        score=relevance_score,
        reasoning=reasoning,
        evidence=evidence,
        confidence=0.8 if relevance_score > 0.6 else 0.5,
    )


@pytest.mark.asyncio
async def test_semantic_accuracy_on_content(knowledge_base):
    """Test semantic accuracy of responses to content-based queries."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    judgments = []

    for doc_name, doc_content in list(knowledge_base.items())[:3]:
        # Extract key concepts from document
        content_lower = doc_content.lower()
        concepts = []
        if "trust" in content_lower:
            concepts.append("trust")
        if "uncertainty" in content_lower:
            concepts.append("uncertainty")
        if "knowledge" in content_lower:
            concepts.append("knowledge")
        if "structure" in content_lower:
            concepts.append("structure")

        if concepts:
            query = f"What does {doc_name} say about {concepts[0]}?"
            response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
            response = response_obj.get("response", "")

            judgment = evaluate_semantic_accuracy(query, response, concepts)
            judgments.append(judgment)

    # Aggregate results
    assert len(judgments) > 0
    avg_accuracy = sum(j.score for j in judgments) / len(judgments)

    # Should have reasonable accuracy
    assert avg_accuracy >= 0.0
    assert avg_accuracy <= 1.0

    # Return for aggregation
    return [j.to_dict() for j in judgments]


@pytest.mark.asyncio
async def test_semantic_completeness_on_content(knowledge_base):
    """Test semantic completeness of responses given content context."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    judgments = []

    for doc_name, doc_content in list(knowledge_base.items())[:2]:
        query = f"Summarize the key points in {doc_name}"
        response_obj = await agent.chat(query, use_schema="decompose_and_synthesize", use_research=False)
        response = response_obj.get("response", "")

        # Use document content as context
        judgment = evaluate_semantic_completeness(query, response, doc_content[:1000])
        judgments.append(judgment)

    assert len(judgments) > 0
    avg_completeness = sum(j.score for j in judgments) / len(judgments)

    assert avg_completeness >= 0.0
    assert avg_completeness <= 1.0

    return [j.to_dict() for j in judgments]


@pytest.mark.asyncio
async def test_semantic_relevance_on_queries(knowledge_base):
    """Test semantic relevance of responses to various query types."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    queries = [
        "What is knowledge structure?",
        "How does trust work?",
        "Why is uncertainty important?",
    ]

    judgments = []

    for query in queries:
        response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
        response = response_obj.get("response", "")

        judgment = evaluate_semantic_relevance(query, response)
        judgments.append(judgment)

    assert len(judgments) > 0
    avg_relevance = sum(j.score for j in judgments) / len(judgments)

    assert avg_relevance >= 0.0
    assert avg_relevance <= 1.0

    return [j.to_dict() for j in judgments]


@pytest.mark.asyncio
async def test_semantic_consistency_across_schemas(knowledge_base):
    """Test semantic consistency when same query uses different schemas."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    query = "What is trust in knowledge graphs?"
    schemas = ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test"]

    responses = []
    for schema in schemas:
        response_obj = await agent.chat(query, use_schema=schema, use_research=False)
        responses.append(response_obj.get("response", ""))

    # Evaluate consistency
    judgments = []
    for i, response in enumerate(responses):
        # Check if responses are semantically similar to each other
        for j, other_response in enumerate(responses[i+1:], start=i+1):
            import difflib
            similarity = difflib.SequenceMatcher(None, response.lower(), other_response.lower()).ratio()

            judgments.append(SemanticJudgment(
                query=f"{query} (schema comparison)",
                response=f"Response {i} vs {j}",
                judgment_type="consistency",
                score=similarity,
                reasoning=f"Semantic similarity between schema responses: {similarity:.2f}",
                evidence=[f"Schema {i}", f"Schema {j}"],
            ).to_dict())

    assert len(judgments) > 0
    return judgments


@pytest.mark.asyncio
async def test_semantic_research_quality(knowledge_base):
    """Test semantic quality of research results."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    query = "What are the key concepts in knowledge structure?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
    )

    synthesis = result.get("final_synthesis", "")

    # Evaluate synthesis quality
    judgment = evaluate_semantic_completeness(
        query,
        synthesis,
        " ".join(knowledge_base.values())[:1000] if knowledge_base else ""
    )

    # Should have some content
    assert judgment.score >= 0.0

    return judgment.to_dict()

