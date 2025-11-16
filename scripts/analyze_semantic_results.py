#!/usr/bin/env python3
"""Analyze semantic evaluation results for decision-making."""

import json
import csv
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


def load_judgments(json_path: Path) -> List[Dict[str, Any]]:
    """Load judgments from JSON file."""
    data = json.loads(json_path.read_text())
    return data.get("judgments", [])


def analyze_by_dimension(judgments: List[Dict[str, Any]], dimension: str) -> Dict[str, Any]:
    """Analyze judgments grouped by a metadata dimension."""
    grouped = defaultdict(list)
    
    for judgment in judgments:
        value = judgment.get("metadata", {}).get(dimension, "unknown")
        grouped[value].append(judgment["score"])
    
    results = {}
    for value, scores in grouped.items():
        results[value] = {
            "count": len(scores),
            "mean": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
        }
    
    return results


def find_low_performers(judgments: List[Dict[str, Any]], threshold: float = 0.6) -> List[Dict[str, Any]]:
    """Find judgments below threshold."""
    return [
        j for j in judgments
        if j["score"] < threshold
    ]


def analyze_patterns(judgments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Identify patterns in the data."""
    patterns = {}
    
    # Pattern 1: Schema performance
    if any("schema" in j.get("metadata", {}) for j in judgments):
        schema_analysis = analyze_by_dimension(judgments, "schema")
        if schema_analysis:
            patterns["schema_performance"] = schema_analysis
            best_schema = max(schema_analysis.items(), key=lambda x: x[1]["mean"])
            patterns["best_schema"] = {
                "name": best_schema[0],
                "mean_score": best_schema[1]["mean"],
            }
    
    # Pattern 2: Research impact
    research_judgments = [j for j in judgments if "research" in j.get("metadata", {})]
    if research_judgments:
        with_research = [j for j in research_judgments if j.get("metadata", {}).get("research") is True]
        without_research = [j for j in research_judgments if j.get("metadata", {}).get("research") is False]
        
        if with_research and without_research:
            with_mean = sum(j["score"] for j in with_research) / len(with_research)
            without_mean = sum(j["score"] for j in without_research) / len(without_research)
            patterns["research_impact"] = {
                "with_research": with_mean,
                "without_research": without_mean,
                "improvement": with_mean - without_mean,
            }
    
    # Pattern 3: Query type performance
    if any("query_type" in j.get("metadata", {}) for j in judgments):
        query_type_analysis = analyze_by_dimension(judgments, "query_type")
        if query_type_analysis:
            patterns["query_type_performance"] = query_type_analysis
    
    # Pattern 4: Judgment type distribution
    by_type = defaultdict(list)
    for j in judgments:
        by_type[j["judgment_type"]].append(j["score"])
    
    patterns["judgment_type_distribution"] = {
        j_type: {
            "count": len(scores),
            "mean": sum(scores) / len(scores),
        }
        for j_type, scores in by_type.items()
    }
    
    return patterns


def generate_insights(judgments: List[Dict[str, Any]], aggregate: Dict[str, Any]) -> List[str]:
    """Generate actionable insights from the data."""
    insights = []
    
    overall_mean = aggregate.get("overall", {}).get("mean_score", 0)
    
    # Overall quality insight
    if overall_mean >= 0.8:
        insights.append("✅ System performing excellently (mean score ≥ 0.8)")
    elif overall_mean >= 0.6:
        insights.append("⚠️ System performing adequately but has room for improvement (mean score 0.6-0.8)")
    else:
        insights.append("❌ System needs significant improvement (mean score < 0.6)")
    
    # Completeness insight
    completeness_scores = [
        j["score"] for j in judgments
        if j["judgment_type"] == "completeness"
    ]
    if completeness_scores:
        comp_mean = sum(completeness_scores) / len(completeness_scores)
        if comp_mean < 0.5:
            insights.append("⚠️ Completeness scores are low - responses may be missing key information")
    
    # Consistency insight
    consistency_scores = [
        j["score"] for j in judgments
        if j["judgment_type"] == "consistency"
    ]
    if consistency_scores:
        cons_mean = sum(consistency_scores) / len(consistency_scores)
        if cons_mean < 0.7:
            insights.append("⚠️ Low consistency - responses vary significantly across methods")
        else:
            insights.append("✅ Good consistency across different methods")
    
    # Low performers
    low_performers = find_low_performers(judgments, threshold=0.6)
    if low_performers:
        insights.append(f"⚠️ {len(low_performers)} judgments scored below 0.6 - review these for improvement opportunities")
    
    # Schema insights
    patterns = analyze_patterns(judgments)
    if "best_schema" in patterns:
        best = patterns["best_schema"]
        insights.append(f"📊 Best performing schema: {best['name']} (mean: {best['mean_score']:.3f})")
    
    # Research insights
    if "research_impact" in patterns:
        impact = patterns["research_impact"]
        if impact["improvement"] > 0.1:
            insights.append(f"✅ Research improves quality by {impact['improvement']:.3f} on average")
        elif impact["improvement"] < -0.1:
            insights.append(f"⚠️ Research may be reducing quality (difference: {impact['improvement']:.3f})")
        else:
            insights.append("➡️ Research has minimal impact on quality")
    
    return insights


def print_analysis_report(json_path: Path):
    """Print comprehensive analysis report."""
    data = json.loads(json_path.read_text())
    judgments = data.get("judgments", [])
    aggregate = data.get("aggregate", {})
    
    print("=" * 70)
    print("SEMANTIC EVALUATION ANALYSIS")
    print("=" * 70)
    print()
    
    # Overall statistics
    print("📊 OVERALL STATISTICS")
    print("-" * 70)
    overall = aggregate.get("overall", {})
    print(f"Total Judgments: {aggregate.get('total_judgments', 0)}")
    print(f"Mean Score: {overall.get('mean_score', 0):.3f}")
    print(f"Score Range: {overall.get('min_score', 0):.3f} - {overall.get('max_score', 0):.3f}")
    print(f"Standard Deviation: {overall.get('std_score', 0):.3f}")
    print()
    
    # By judgment type
    print("📈 BY JUDGMENT TYPE")
    print("-" * 70)
    for j_type, stats in aggregate.get("by_type", {}).items():
        print(f"{j_type:20s} | Mean: {stats['mean']:.3f} | Count: {stats['count']:3d} | "
              f"Range: {stats['min']:.3f}-{stats['max']:.3f} | Std: {stats['std']:.3f}")
    print()
    
    # Patterns
    patterns = analyze_patterns(judgments)
    if patterns:
        print("🔍 PATTERNS")
        print("-" * 70)
        
        if "schema_performance" in patterns:
            print("\nSchema Performance:")
            for schema, stats in patterns["schema_performance"].items():
                print(f"  {schema:30s} | Mean: {stats['mean']:.3f} (n={stats['count']})")
        
        if "research_impact" in patterns:
            impact = patterns["research_impact"]
            print(f"\nResearch Impact:")
            print(f"  With research:    {impact['with_research']:.3f}")
            print(f"  Without research: {impact['without_research']:.3f}")
            print(f"  Difference:      {impact['improvement']:+.3f}")
        
        if "query_type_performance" in patterns:
            print(f"\nQuery Type Performance:")
            for q_type, stats in patterns["query_type_performance"].items():
                print(f"  {q_type:20s} | Mean: {stats['mean']:.3f} (n={stats['count']})")
        print()
    
    # Low performers
    low_performers = find_low_performers(judgments, threshold=0.6)
    if low_performers:
        print("⚠️  LOW PERFORMERS (score < 0.6)")
        print("-" * 70)
        for j in low_performers[:5]:  # Show top 5
            print(f"Score: {j['score']:.3f} | Type: {j['judgment_type']:15s} | Query: {j['query'][:50]}")
            print(f"  Reasoning: {j['reasoning'][:100]}")
            print()
    
    # Insights
    insights = generate_insights(judgments, aggregate)
    if insights:
        print("💡 ACTIONABLE INSIGHTS")
        print("-" * 70)
        for insight in insights:
            print(f"  {insight}")
        print()
    
    print("=" * 70)
    print(f"Full data available in: {json_path}")
    print(f"CSV for spreadsheet analysis: {json_path.parent / 'comprehensive_judgments.csv'}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze semantic evaluation results")
    parser.add_argument(
        "json_file",
        type=Path,
        help="Path to semantic_judgments.json file",
    )
    
    args = parser.parse_args()
    
    if not args.json_file.exists():
        print(f"Error: File not found: {args.json_file}")
        sys.exit(1)
    
    print_analysis_report(args.json_file)

