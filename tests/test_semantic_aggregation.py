"""Tests for semantic evaluation aggregation and transparency."""

import pytest
from pathlib import Path
from bop.semantic_eval import SemanticEvaluator, SemanticJudgment


def test_judgment_aggregation():
    """Test that judgments can be aggregated meaningfully."""
    evaluator = SemanticEvaluator()
    
    # Add diverse judgments
    judgments = [
        SemanticJudgment(
            query="Query 1",
            response="Response 1",
            judgment_type="accuracy",
            score=0.9,
            reasoning="High accuracy",
            evidence=["concept1", "concept2"],
            confidence=0.8,
        ),
        SemanticJudgment(
            query="Query 2",
            response="Response 2",
            judgment_type="accuracy",
            score=0.7,
            reasoning="Medium accuracy",
            evidence=["concept1"],
            confidence=0.7,
        ),
        SemanticJudgment(
            query="Query 3",
            response="Response 3",
            judgment_type="relevance",
            score=0.8,
            reasoning="Good relevance",
            evidence=["word1"],
            confidence=0.8,
        ),
    ]
    
    evaluator.judgments = judgments
    
    aggregate = evaluator.aggregate_judgments()
    
    assert aggregate["total_judgments"] == 3
    assert aggregate["overall"]["mean_score"] > 0.0
    assert "accuracy" in aggregate["by_type"]
    assert "relevance" in aggregate["by_type"]
    
    # Accuracy should have 2 judgments
    assert aggregate["by_type"]["accuracy"]["count"] == 2
    assert aggregate["by_type"]["accuracy"]["mean"] == 0.8  # (0.9 + 0.7) / 2


def test_judgment_export_formats(tmp_path):
    """Test that judgments can be exported in multiple formats."""
    evaluator = SemanticEvaluator(output_dir=tmp_path)
    
    evaluator.judgments = [
        SemanticJudgment(
            query="Test query",
            response="Test response",
            judgment_type="accuracy",
            score=0.85,
            reasoning="Test reasoning",
            evidence=["evidence1"],
            confidence=0.8,
            metadata={"schema": "chain_of_thought"},
        )
    ]
    
    # Test JSON export
    json_path = evaluator.save_judgments_json("test.json")
    assert json_path.exists()
    assert json_path.suffix == ".json"
    
    # Test CSV export
    csv_path = evaluator.save_judgments_csv("test.csv")
    assert csv_path.exists()
    assert csv_path.suffix == ".csv"
    
    # Test report export
    report_path = evaluator.save_summary_report("test.md")
    assert report_path.exists()
    assert report_path.suffix == ".md"


def test_aggregation_statistics():
    """Test that aggregation produces meaningful statistics."""
    evaluator = SemanticEvaluator()
    
    # Create judgments with known statistics
    scores = [0.5, 0.6, 0.7, 0.8, 0.9]
    for i, score in enumerate(scores):
        evaluator.judgments.append(
            SemanticJudgment(
                query=f"Query {i}",
                response=f"Response {i}",
                judgment_type="accuracy",
                score=score,
                reasoning=f"Score {score}",
                evidence=[],
            )
        )
    
    aggregate = evaluator.aggregate_judgments()
    
    # Mean should be 0.7
    assert abs(aggregate["overall"]["mean_score"] - 0.7) < 0.01
    
    # Min should be 0.5
    assert aggregate["overall"]["min_score"] == 0.5
    
    # Max should be 0.9
    assert aggregate["overall"]["max_score"] == 0.9
    
    # Should have standard deviation
    assert aggregate["overall"]["std_score"] > 0.0


def test_metadata_aggregation():
    """Test that metadata is aggregated correctly."""
    evaluator = SemanticEvaluator()
    
    evaluator.judgments = [
        SemanticJudgment(
            query="Q1",
            response="R1",
            judgment_type="accuracy",
            score=0.8,
            reasoning="R1",
            evidence=[],
            metadata={"schema": "chain_of_thought", "research": False},
        ),
        SemanticJudgment(
            query="Q2",
            response="R2",
            judgment_type="accuracy",
            score=0.9,
            reasoning="R2",
            evidence=[],
            metadata={"schema": "decompose_and_synthesize", "research": True},
        ),
    ]
    
    aggregate = evaluator.aggregate_judgments()
    
    # Should track metadata
    assert "metadata_summary" in aggregate
    assert "schema" in aggregate["metadata_summary"]
    assert aggregate["metadata_summary"]["schema"]["count"] == 2
    assert aggregate["metadata_summary"]["schema"]["unique_values"] == 2


def test_transparent_reasoning():
    """Test that judgments include transparent reasoning."""
    evaluator = SemanticEvaluator()
    
    judgment = evaluator.evaluate_accuracy(
        query="What is trust?",
        response="Trust is confidence in reliability",
        expected_concepts=["trust", "confidence", "reliability"],
    )
    
    # Should have reasoning
    assert len(judgment.reasoning) > 0
    assert "concepts" in judgment.reasoning.lower() or "relevance" in judgment.reasoning.lower()
    
    # Should have evidence
    assert len(judgment.evidence) > 0
    
    # Should have confidence
    assert 0.0 <= judgment.confidence <= 1.0


def test_decision_support_metrics():
    """Test that aggregation provides metrics useful for decision-making."""
    evaluator = SemanticEvaluator()
    
    # Create judgments representing different scenarios
    scenarios = [
        ("high_quality", 0.9, 0.8),
        ("medium_quality", 0.7, 0.7),
        ("low_quality", 0.4, 0.5),
    ]
    
    for scenario_name, score, confidence in scenarios:
        evaluator.judgments.append(
            SemanticJudgment(
                query=f"Query for {scenario_name}",
                response=f"Response for {scenario_name}",
                judgment_type="accuracy",
                score=score,
                reasoning=f"{scenario_name} scenario",
                evidence=[],
                confidence=confidence,
                metadata={"scenario": scenario_name},
            )
        )
    
    aggregate = evaluator.aggregate_judgments()
    
    # Should provide metrics for decision-making
    assert "overall" in aggregate
    assert "by_type" in aggregate
    assert "confidence" in aggregate
    
    # Mean score should be around 0.67
    mean = aggregate["overall"]["mean_score"]
    assert 0.6 <= mean <= 0.7
    
    # Should identify low performers
    min_score = aggregate["overall"]["min_score"]
    assert min_score == 0.4  # Low quality scenario


def test_csv_analysis_friendly():
    """Test that CSV output is analysis-friendly."""
    evaluator = SemanticEvaluator()
    
    evaluator.judgments = [
        SemanticJudgment(
            query="Test",
            response="Response",
            judgment_type="accuracy",
            score=0.8,
            reasoning="Test",
            evidence=["e1", "e2"],
            metadata={"schema": "cot", "research": False},
        )
    ]
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        evaluator.output_dir = Path(tmpdir)
        csv_path = evaluator.save_judgments_csv("test.csv")
        
        # Should be readable
        content = csv_path.read_text()
        assert "timestamp" in content
        assert "score" in content
        assert "judgment_type" in content
        assert "schema" in content  # Metadata field
        assert "research" in content  # Metadata field


def test_report_recommendations():
    """Test that reports include actionable recommendations."""
    evaluator = SemanticEvaluator()
    
    # Low scores scenario
    evaluator.judgments = [
        SemanticJudgment(
            query="Q",
            response="R",
            judgment_type="accuracy",
            score=0.3,
            reasoning="Low score",
            evidence=[],
        )
    ]
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        evaluator.output_dir = Path(tmpdir)
        report_path = evaluator.save_summary_report("test.md")
        
        report = report_path.read_text()
        
        # Should include recommendations
        assert "Recommendations" in report
        # Should flag low scores
        assert "Low" in report or "improve" in report.lower()


def test_multi_dimensional_analysis():
    """Test that judgments support multi-dimensional analysis."""
    evaluator = SemanticEvaluator()
    
    # Create judgments with multiple dimensions
    for schema in ["chain_of_thought", "decompose_and_synthesize"]:
        for research in [True, False]:
            evaluator.judgments.append(
                SemanticJudgment(
                    query="Test",
                    response="Response",
                    judgment_type="accuracy",
                    score=0.8 if research else 0.7,
                    reasoning="Test",
                    evidence=[],
                    metadata={
                        "schema": schema,
                        "research": research,
                    },
                )
            )
    
    aggregate = evaluator.aggregate_judgments()
    
    # Should track both dimensions
    assert "schema" in aggregate["metadata_summary"]
    assert "research" in aggregate["metadata_summary"]
    
    # Can analyze by dimension
    schema_counts = aggregate["metadata_summary"]["schema"]["count"]
    assert schema_counts == 4  # 2 schemas * 2 research values

