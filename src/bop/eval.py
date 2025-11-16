"""Evaluation framework for reasoning quality."""

import json
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class EvaluationResult(BaseModel):
    """Result of a single evaluation test."""

    test_name: str
    passed: bool
    score: float
    details: Dict[str, Any] = {}
    error: Optional[str] = None


class EvaluationFramework:
    """Framework for evaluating reasoning quality."""

    def __init__(self):
        """Initialize evaluation framework."""
        self.results: List[EvaluationResult] = []

    def evaluate_schema_usage(
        self,
        schema_name: str,
        test_cases: List[Dict[str, Any]],
    ) -> EvaluationResult:
        """
        Evaluate structured schema usage.

        Args:
            schema_name: Name of schema to test
            test_cases: List of test cases with input/expected output
        """
        if not test_cases:
            return EvaluationResult(
                test_name=f"schema_{schema_name}",
                passed=False,
                score=0.0,
                details={"test_cases": 0, "error": "No test cases provided"},
            )

        passed_count = 0
        total_score = 0.0
        errors = []

        for i, test_case in enumerate(test_cases):
            input_text = test_case.get("input", "")
            expected = test_case.get("expected", {})
            actual = test_case.get("actual", {})

            if not input_text:
                errors.append(f"Test case {i}: Missing input")
                continue

            if isinstance(expected, dict) and isinstance(actual, dict):
                from .schemas import get_schema
                schema = get_schema(schema_name)
                if schema:
                    required_fields = list(schema.schema_def.keys())
                    actual_fields = set(actual.keys())
                    expected_fields = set(required_fields)

                    field_coverage = len(actual_fields & expected_fields) / len(expected_fields) if expected_fields else 0.0
                    
                    content_quality = 0.0
                    type_quality = 0.0
                    if actual_fields & expected_fields:
                        non_empty_count = 0
                        type_match_count = 0
                        for field in (actual_fields & expected_fields):
                            value = actual.get(field)
                            if value and str(value).strip():
                                non_empty_count += 1
                                expected_type = expected.get(field)
                                if expected_type:
                                    if isinstance(expected_type, type):
                                        if isinstance(value, expected_type):
                                            type_match_count += 1
                                    elif isinstance(expected_type, str):
                                        if isinstance(value, str):
                                            type_match_count += 1
                                    elif isinstance(expected_type, list):
                                        if isinstance(value, (list, tuple)):
                                            type_match_count += 1
                                    else:
                                        type_match_count += 1
                                else:
                                    type_match_count += 1
                        
                        content_quality = non_empty_count / len(actual_fields & expected_fields) if (actual_fields & expected_fields) else 0.0
                        type_quality = type_match_count / len(actual_fields & expected_fields) if (actual_fields & expected_fields) else 0.0
                    
                    case_score = field_coverage * (0.4 + 0.3 * content_quality + 0.3 * type_quality)
                    total_score += case_score

                    if case_score >= 0.7:
                        passed_count += 1
                    else:
                        if field_coverage < 0.7:
                            errors.append(f"Test case {i}: Only {field_coverage:.0%} field coverage")
                        if content_quality < 0.7:
                            errors.append(f"Test case {i}: Only {content_quality:.0%} fields have content")
                else:
                    errors.append(f"Test case {i}: Schema {schema_name} not found")
            else:
                errors.append(f"Test case {i}: Invalid test case format")

        avg_score = total_score / len(test_cases) if test_cases else 0.0
        passed = passed_count >= len(test_cases) * 0.7

        return EvaluationResult(
            test_name=f"schema_{schema_name}",
            passed=passed,
            score=avg_score,
            details={
                "test_cases": len(test_cases),
                "passed": passed_count,
                "errors": errors[:5],
            },
        )

    def evaluate_reasoning_coherence(
        self,
        responses: List[str],
    ) -> EvaluationResult:
        """
        Evaluate reasoning coherence across responses.
        """
        if not responses:
            return EvaluationResult(
                test_name="reasoning_coherence",
                passed=False,
                score=0.0,
                details={"responses_evaluated": 0, "error": "No responses provided"},
            )

        lengths = [len(r) for r in responses if r]
        if not lengths:
            return EvaluationResult(
                test_name="reasoning_coherence",
                passed=False,
                score=0.0,
                details={"error": "All responses empty"},
            )

        avg_length = sum(lengths) / len(lengths)
        length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths) if lengths else 0
        length_coherence = 1.0 / (1.0 + length_variance / (avg_length ** 2 + 1))

        all_words = set()
        response_words = []
        for r in responses:
            words = set(r.lower().split())
            all_words.update(words)
            response_words.append(words)

        if not all_words:
            overlap_score = 0.0
            semantic_score = 0.0
        else:
            overlaps = []
            semantic_similarities = []
            for i in range(len(response_words)):
                for j in range(i + 1, len(response_words)):
                    overlap = len(response_words[i] & response_words[j])
                    union = len(response_words[i] | response_words[j])
                    if union > 0:
                        overlaps.append(overlap / union)
                    
                    response_i = responses[i].lower()
                    response_j = responses[j].lower()
                    similarity = difflib.SequenceMatcher(None, response_i, response_j).ratio()
                    semantic_similarities.append(similarity)
            
            overlap_score = sum(overlaps) / len(overlaps) if overlaps else 0.0
            semantic_score = sum(semantic_similarities) / len(semantic_similarities) if semantic_similarities else 0.0

        structure_scores = []
        for r in responses:
            has_numbers = any(c.isdigit() for c in r[:100])
            has_newlines = "\n" in r
            has_markers = any(marker in r for marker in ["-", "*", "•", "1.", "2."])
            structure_score = (has_numbers + has_newlines + has_markers) / 3.0
            structure_scores.append(structure_score)

        avg_structure = sum(structure_scores) / len(structure_scores) if structure_scores else 0.0

        score = (length_coherence * 0.2 + overlap_score * 0.3 + semantic_score * 0.3 + avg_structure * 0.2)
        passed = score > 0.6

        if 'semantic_score' not in locals():
            semantic_score = 0.0
        
        return EvaluationResult(
            test_name="reasoning_coherence",
            passed=passed,
            score=score,
            details={
                "responses_evaluated": len(responses),
                "length_coherence": length_coherence,
                "overlap_score": overlap_score,
                "semantic_score": semantic_score,
                "structure_score": avg_structure,
            },
        )

    def evaluate_dependency_gap_handling(
        self,
        test_cases: List[Dict[str, Any]],
    ) -> EvaluationResult:
        """
        Evaluate handling of dependency gaps.
        """
        if not test_cases:
            return EvaluationResult(
                test_name="dependency_gap_handling",
                passed=False,
                score=0.0,
                details={"test_cases": 0, "error": "No test cases provided"},
            )

        passed_count = 0
        total_score = 0.0
        errors = []

        for i, test_case in enumerate(test_cases):
            query = test_case.get("query", "")
            expected_steps = test_case.get("intermediate_steps", [])
            actual_steps = test_case.get("actual_steps", [])
            expected_answer = test_case.get("final_answer", "")
            actual_answer = test_case.get("actual_answer", "")

            if not query:
                errors.append(f"Test case {i}: Missing query")
                continue

            step_score = 0.0
            step_relevance_score = 0.0
            if actual_steps:
                step_count_score = min(1.0, len(actual_steps) / max(1, len(expected_steps)))
                
                if expected_steps:
                    relevance_scores = []
                    for actual_step in actual_steps:
                        if actual_step:
                            best_match = 0.0
                            for expected_step in expected_steps:
                                similarity = difflib.SequenceMatcher(
                                    None, 
                                    str(actual_step).lower(), 
                                    str(expected_step).lower()
                                ).ratio()
                                best_match = max(best_match, similarity)
                            relevance_scores.append(best_match)
                    
                    query_words = set(query.lower().split())
                    query_relevance = []
                    for step in actual_steps:
                        if step:
                            step_words = set(str(step).lower().split())
                            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
                            step_words -= stop_words
                            query_words_clean = query_words - stop_words
                            if query_words_clean:
                                relevance = len(step_words & query_words_clean) / len(query_words_clean)
                                query_relevance.append(relevance)
                    
                    step_relevance_score = (
                        (sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0) * 0.6 +
                        (sum(query_relevance) / len(query_relevance) if query_relevance else 0.0) * 0.4
                    )
                
                step_score = step_count_score * 0.5 + step_relevance_score * 0.5
            else:
                errors.append(f"Test case {i}: No intermediate steps found")

            answer_score = 0.0
            if actual_answer:
                answer_str = str(actual_answer).strip()
                if not answer_str:
                    errors.append(f"Test case {i}: Answer is empty")
                    answer_score = 0.0
                else:
                    length_score = min(1.0, len(answer_str) / max(50, len(query) * 0.5))
                    
                    query_words = set(query.lower().split())
                    answer_words = set(answer_str.lower().split())
                    relevance_score = len(query_words & answer_words) / len(query_words) if query_words else 0.0
                    
                    answer_score = (length_score * 0.6 + relevance_score * 0.4)
            else:
                errors.append(f"Test case {i}: No answer provided")

            case_score = (step_score * 0.6 + answer_score * 0.4)
            total_score += case_score

            if case_score >= 0.7:
                passed_count += 1

        avg_score = total_score / len(test_cases) if test_cases else 0.0
        passed = passed_count >= len(test_cases) * 0.7

        avg_step_relevance = 0.0
        step_relevance_scores = []
        for i, test_case in enumerate(test_cases):
            actual_steps = test_case.get("actual_steps", [])
            expected_steps = test_case.get("intermediate_steps", [])
            if actual_steps and expected_steps:
                relevance_scores = []
                for actual_step in actual_steps:
                    if actual_step:
                        best_match = 0.0
                        for expected_step in expected_steps:
                            similarity = difflib.SequenceMatcher(
                                None,
                                str(actual_step).lower(),
                                str(expected_step).lower()
                            ).ratio()
                            best_match = max(best_match, similarity)
                        relevance_scores.append(best_match)
                if relevance_scores:
                    step_relevance_scores.append(sum(relevance_scores) / len(relevance_scores))
        avg_step_relevance = sum(step_relevance_scores) / len(step_relevance_scores) if step_relevance_scores else 0.0

        return EvaluationResult(
            test_name="dependency_gap_handling",
            passed=passed,
            score=avg_score,
            details={
                "test_cases": len(test_cases),
                "passed": passed_count,
                "errors": errors[:5],
                "avg_step_relevance": avg_step_relevance,
            },
        )

    def run_evaluations(self, content_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        """
        Run all evaluations with content in multiple ways.

        Args:
            content_dir: Optional directory containing content files to use for evaluation
        """
        results = {}

        # Standard evaluations
        schema_test_cases = [
            {
                "input": "Solve 2x + 3 = 7",
                "expected": {"input_analysis": str, "steps": list, "final_result": str},
                "actual": {
                    "input_analysis": "Equation to solve: 2x + 3 = 7",
                    "steps": ["Subtract 3", "Divide by 2"],
                    "final_result": "x = 2",
                },
            }
        ]
        schema_result = self.evaluate_schema_usage("chain_of_thought", schema_test_cases)
        results[schema_result.test_name] = schema_result.model_dump()

        sample_responses = [
            "First, I need to understand the problem. Then I'll break it down into steps.",
            "Let me analyze this step by step. First, identify the key components.",
            "I'll solve this systematically. Step 1: Understand the requirements.",
        ]
        coherence_result = self.evaluate_reasoning_coherence(sample_responses)
        results[coherence_result.test_name] = coherence_result.model_dump()

        gap_test_cases = [
            {
                "query": "What is the relationship between A and C?",
                "intermediate_steps": ["Understand A", "Find connection to B", "Relate B to C"],
                "actual_steps": ["Understanding A", "Finding B connection", "Relating to C"],
                "final_answer": "A relates to C through B",
                "actual_answer": "A relates to C through intermediate B",
            }
        ]
        gap_result = self.evaluate_dependency_gap_handling(gap_test_cases)
        results[gap_result.test_name] = gap_result.model_dump()

        # Content-based evaluations (multiple ways)
        if content_dir and content_dir.exists():
            try:
                from .research import load_content
                knowledge_base = load_content(content_dir)
                
                # Way 1: Document-level queries
                doc_test_cases = []
                for doc_name, doc_content in list(knowledge_base.items())[:3]:
                    if len(doc_content) > 100:
                        doc_test_cases.append({
                            "input": f"What does {doc_name} discuss?",
                            "expected": {"input_analysis": str, "steps": list, "final_result": str},
                            "actual": {
                                "input_analysis": f"Analyzing {doc_name}",
                                "steps": ["Load document", "Extract key concepts"],
                                "final_result": f"{doc_name} discusses relevant concepts",
                            },
                        })
                
                if doc_test_cases:
                    doc_result = self.evaluate_schema_usage("chain_of_thought", doc_test_cases)
                    results[f"{doc_result.test_name}_doc_level"] = doc_result.model_dump()
                
                # Way 2: Concept-based queries
                all_content = " ".join(knowledge_base.values()).lower()
                concept_test_cases = []
                concepts = ["trust", "uncertainty", "knowledge", "structure"]
                for concept in concepts:
                    if concept in all_content:
                        concept_test_cases.append({
                            "input": f"What is {concept}?",
                            "expected": {"input_analysis": str, "steps": list},
                            "actual": {
                                "input_analysis": f"Analyzing {concept}",
                                "steps": [f"Define {concept}", "Find examples"],
                            },
                        })
                
                if concept_test_cases:
                    concept_result = self.evaluate_schema_usage("chain_of_thought", concept_test_cases)
                    results[f"{concept_result.test_name}_concept_level"] = concept_result.model_dump()
                
                # Way 3: Sentence-level responses
                sentence_responses = []
                for doc_name, doc_content in knowledge_base.items():
                    sentences = doc_content.split('.')[:5]
                    for sentence in sentences:
                        if sentence.strip() and len(sentence.strip()) > 20:
                            sentence_responses.append(f"From {doc_name}: {sentence.strip()}.")
                
                if sentence_responses:
                    sentence_result = self.evaluate_reasoning_coherence(sentence_responses)
                    results[f"{sentence_result.test_name}_sentence_level"] = sentence_result.model_dump()
                
                # Way 4: Paragraph-level responses
                para_responses = []
                for doc_name, doc_content in knowledge_base.items():
                    paragraphs = doc_content.split('\n\n')[:3]
                    for para in paragraphs:
                        if para.strip() and len(para.strip()) > 50:
                            para_responses.append(f"Paragraph from {doc_name}: {para[:300]}")
                
                if para_responses:
                    para_result = self.evaluate_reasoning_coherence(para_responses)
                    results[f"{para_result.test_name}_paragraph_level"] = para_result.model_dump()
                
                # Way 5: Cross-document queries
                if len(knowledge_base) >= 2:
                    doc_names = list(knowledge_base.keys())[:2]
                    cross_test_cases = [
                        {
                            "input": f"Compare {doc_names[0]} and {doc_names[1]}",
                            "expected": {"input_analysis": str, "comparison": dict},
                            "actual": {
                                "input_analysis": f"Comparing documents",
                                "comparison": {"similarities": [], "differences": []},
                            },
                        }
                    ]
                    cross_result = self.evaluate_schema_usage("decompose_and_synthesize", cross_test_cases)
                    results[f"{cross_result.test_name}_cross_doc"] = cross_result.model_dump()
                
                # Way 6: Multi-hop dependency gaps with content
                all_content_text = " ".join(knowledge_base.values()).lower()
                if "trust" in all_content_text and "uncertainty" in all_content_text and "knowledge" in all_content_text:
                    multi_hop_cases = [
                        {
                            "query": "How does trust relate to knowledge through uncertainty?",
                            "intermediate_steps": [
                                "Understand trust",
                                "Understand uncertainty",
                                "Understand knowledge",
                                "Relate trust-uncertainty",
                                "Relate uncertainty-knowledge",
                                "Synthesize trust-knowledge",
                            ],
                            "actual_steps": [
                                "Understanding trust",
                                "Understanding uncertainty",
                                "Understanding knowledge",
                                "Relating trust and uncertainty",
                                "Relating uncertainty and knowledge",
                                "Synthesizing relationships",
                            ],
                            "final_answer": "Trust relates to knowledge through uncertainty",
                            "actual_answer": "Trust relates to knowledge through uncertainty, where uncertainty mediates the relationship",
                        }
                    ]
                    multi_hop_result = self.evaluate_dependency_gap_handling(multi_hop_cases)
                    results[f"{multi_hop_result.test_name}_multi_hop"] = multi_hop_result.model_dump()
                
                # Way 7: Temporal queries
                temporal_test_cases = []
                for doc_name in list(knowledge_base.keys())[:2]:
                    temporal_test_cases.append({
                        "input": f"What are the historical foundations in {doc_name}?",
                        "expected": {"input_analysis": str, "temporal_context": str},
                        "actual": {
                            "input_analysis": f"Analyzing {doc_name} historically",
                            "temporal_context": "Historical",
                        },
                    })
                
                if temporal_test_cases:
                    temporal_result = self.evaluate_schema_usage("scenario_analysis", temporal_test_cases)
                    results[f"{temporal_result.test_name}_temporal"] = temporal_result.model_dump()
                
                # Way 8: Quality gradation
                quality_responses = []
                for doc_name, doc_content in list(knowledge_base.items())[:2]:
                    quality_responses.append(f"High quality: {doc_content[:200]}")
                    quality_responses.append(f"Medium quality: {doc_content[:100]}")
                    quality_responses.append(f"Low quality: {doc_content[:50]}")
                
                if quality_responses:
                    quality_result = self.evaluate_reasoning_coherence(quality_responses)
                    results[f"{quality_result.test_name}_quality_gradation"] = quality_result.model_dump()
                    
            except Exception as e:
                results["content_evaluation_error"] = {
                    "test_name": "content_evaluation",
                    "passed": False,
                    "score": 0.0,
                    "error": str(e),
                }

        self.results = [EvaluationResult(**r) for r in results.values()]

        return results

    def save_results(self, results: Dict[str, Dict[str, Any]], output_path: Path) -> None:
        """Save evaluation results to file."""
        output_path.write_text(json.dumps(results, indent=2))

    def load_results(self, input_path: Path) -> Dict[str, Dict[str, Any]]:
        """Load evaluation results from file."""
        return json.loads(input_path.read_text())
