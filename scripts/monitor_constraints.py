#!/usr/bin/env python3
"""
Monitoring script for constraint solver performance.

Tracks constraint solver usage, tool selection, and performance metrics.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent
from bop.constraints import PYSAT_AVAILABLE, create_default_constraints


class ConstraintMonitor:
    """Monitor constraint solver performance."""
    
    def __init__(self, output_file: Optional[Path] = None):
        self.output_file = output_file or Path("constraint_monitor.json")
        self.metrics: List[Dict] = []
    
    async def monitor_query(
        self,
        query: str,
        iterations: int = 5,
    ) -> Dict:
        """Monitor constraint solver for a query."""
        research_agent = ResearchAgent()
        orchestrator = StructuredOrchestrator(
            research_agent=research_agent,
            use_constraints=True
        )
        
        constraints = create_default_constraints()
        
        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "iterations": iterations,
            "constraints": {
                "tools_selected": [],
                "costs": [],
                "info_gains": [],
                "latencies": [],
            },
            "heuristics": {
                "tools_selected": [],
                "costs": [],
                "info_gains": [],
                "latencies": [],
            },
        }
        
        for i in range(iterations):
            # With constraints
            import time
            start = time.time()
            result_constraints = await orchestrator.research_with_schema(
                query,
                schema_name="decompose_and_synthesize",
                max_tools_per_subproblem=2,
            )
            latency_constraints = time.time() - start
            
            tools_constraints = set()
            for subsolution in result_constraints.get("subsolutions", []):
                tools_constraints.update(subsolution.get("tools_used", []))
            
            cost_constraints = sum(
                c.cost for c in constraints if c.tool.value in tools_constraints
            )
            info_constraints = sum(
                c.information_gain for c in constraints if c.tool.value in tools_constraints
            )
            
            results["constraints"]["tools_selected"].append(list(tools_constraints))
            results["constraints"]["costs"].append(cost_constraints)
            results["constraints"]["info_gains"].append(info_constraints)
            results["constraints"]["latencies"].append(latency_constraints)
            
            # With heuristics
            orchestrator.use_constraints = False
            start = time.time()
            result_heuristics = await orchestrator.research_with_schema(
                query,
                schema_name="decompose_and_synthesize",
                max_tools_per_subproblem=2,
            )
            latency_heuristics = time.time() - start
            
            tools_heuristics = set()
            for subsolution in result_heuristics.get("subsolutions", []):
                tools_heuristics.update(subsolution.get("tools_used", []))
            
            cost_heuristics = sum(
                c.cost for c in constraints if c.tool.value in tools_heuristics
            )
            info_heuristics = sum(
                c.information_gain for c in constraints if c.tool.value in tools_heuristics
            )
            
            results["heuristics"]["tools_selected"].append(list(tools_heuristics))
            results["heuristics"]["costs"].append(cost_heuristics)
            results["heuristics"]["info_gains"].append(info_heuristics)
            results["heuristics"]["latencies"].append(latency_heuristics)
        
        # Calculate statistics
        for approach in ["constraints", "heuristics"]:
            costs = results[approach]["costs"]
            infos = results[approach]["info_gains"]
            latencies = results[approach]["latencies"]
            
            results[approach]["stats"] = {
                "avg_cost": sum(costs) / len(costs) if costs else 0,
                "avg_info": sum(infos) / len(infos) if infos else 0,
                "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
                "min_cost": min(costs) if costs else 0,
                "max_cost": max(costs) if costs else 0,
                "min_info": min(infos) if infos else 0,
                "max_info": max(infos) if infos else 0,
            }
        
        # Comparison
        results["comparison"] = {
            "cost_improvement": (
                results["heuristics"]["stats"]["avg_cost"] - 
                results["constraints"]["stats"]["avg_cost"]
            ) / results["heuristics"]["stats"]["avg_cost"] if results["heuristics"]["stats"]["avg_cost"] > 0 else 0,
            "info_improvement": (
                results["constraints"]["stats"]["avg_info"] - 
                results["heuristics"]["stats"]["avg_info"]
            ) / results["heuristics"]["stats"]["avg_info"] if results["heuristics"]["stats"]["avg_info"] > 0 else 0,
            "latency_diff": (
                results["constraints"]["stats"]["avg_latency"] - 
                results["heuristics"]["stats"]["avg_latency"]
            ),
        }
        
        self.metrics.append(results)
        return results
    
    def save(self):
        """Save metrics to file."""
        data = {
            "monitoring_session": datetime.now().isoformat(),
            "metrics": self.metrics,
        }
        self.output_file.write_text(json.dumps(data, indent=2))
        print(f"Metrics saved to {self.output_file}")
    
    def print_summary(self):
        """Print summary of all metrics."""
        if not self.metrics:
            print("No metrics collected")
            return
        
        print("\n" + "=" * 80)
        print("CONSTRAINT SOLVER MONITORING SUMMARY")
        print("=" * 80)
        
        for i, metric in enumerate(self.metrics, 1):
            print(f"\nQuery {i}: {metric['query'][:60]}...")
            print(f"  Timestamp: {metric['timestamp']}")
            
            comp = metric["comparison"]
            print(f"\n  Comparison:")
            print(f"    Cost improvement: {comp['cost_improvement']*100:.1f}%")
            print(f"    Info improvement: {comp['info_improvement']*100:.1f}%")
            print(f"    Latency difference: {comp['latency_diff']:.3f}s")
            
            print(f"\n  Constraints:")
            stats = metric["constraints"]["stats"]
            print(f"    Avg cost: {stats['avg_cost']:.3f}")
            print(f"    Avg info: {stats['avg_info']:.3f}")
            print(f"    Avg latency: {stats['avg_latency']:.3f}s")
            
            print(f"\n  Heuristics:")
            stats = metric["heuristics"]["stats"]
            print(f"    Avg cost: {stats['avg_cost']:.3f}")
            print(f"    Avg info: {stats['avg_info']:.3f}")
            print(f"    Avg latency: {stats['avg_latency']:.3f}s")


async def main():
    """Run monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor constraint solver performance")
    parser.add_argument("--query", type=str, help="Query to monitor")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    parser.add_argument("--output", type=Path, help="Output file")
    parser.add_argument("--queries-file", type=Path, help="File with queries (one per line)")
    
    args = parser.parse_args()
    
    if not PYSAT_AVAILABLE:
        print("ERROR: PySAT not available. Install with: uv sync --extra constraints")
        return
    
    monitor = ConstraintMonitor(output_file=args.output)
    
    queries = []
    if args.queries_file and args.queries_file.exists():
        queries = args.queries_file.read_text().strip().split("\n")
    elif args.query:
        queries = [args.query]
    else:
        # Default test queries
        queries = [
            "What is trust in knowledge graphs?",
            "How does uncertainty relate to trust?",
            "comprehensive analysis of knowledge structure research",
        ]
    
    print(f"Monitoring {len(queries)} queries with {args.iterations} iterations each...")
    
    for query in queries:
        if not query.strip():
            continue
        print(f"\nMonitoring: {query[:60]}...")
        await monitor.monitor_query(query, iterations=args.iterations)
    
    monitor.save()
    monitor.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

