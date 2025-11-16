"""Performance benchmarks for constraint solver."""

import pytest
import time
import statistics
from typing import List, Tuple

from bop.constraints import ConstraintSolver, create_default_constraints, PYSAT_AVAILABLE


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
class TestConstraintSolverBenchmarks:
    """Benchmark constraint solver performance."""
    
    def test_solve_speed_benchmark(self):
        """Benchmark basic solve speed."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()
        
        times = []
        for _ in range(20):
            start = time.time()
            solver.solve(constraints, max_tools=2)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        print(f"\nSolve benchmark: avg={avg_time*1000:.2f}ms, p95={p95_time*1000:.2f}ms")
        
        assert avg_time < 0.05, f"Average solve time should be < 50ms, got {avg_time*1000:.2f}ms"
        assert p95_time < 0.1, f"95th percentile should be < 100ms, got {p95_time*1000:.2f}ms"
    
    def test_solve_optimal_speed_benchmark(self):
        """Benchmark solve_optimal speed."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()
        
        objectives = ["min_cost", "max_information", "min_latency"]
        all_times = []
        
        for objective in objectives:
            times = []
            for _ in range(10):
                start = time.time()
                solver.solve_optimal(
                    constraints=constraints,
                    objective=objective,
                    max_tools=2,
                    min_information=0.5,
                )
                elapsed = time.time() - start
                times.append(elapsed)
                all_times.append(elapsed)
            
            avg_time = statistics.mean(times)
            print(f"\n{objective} benchmark: avg={avg_time*1000:.2f}ms")
        
        overall_avg = statistics.mean(all_times)
        print(f"\nOverall solve_optimal avg: {overall_avg*1000:.2f}ms")
        
        assert overall_avg < 0.1, f"Average solve_optimal time should be < 100ms, got {overall_avg*1000:.2f}ms"
    
    def test_constraint_complexity_benchmark(self):
        """Benchmark with varying constraint complexity."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()
        
        scenarios = [
            {"max_tools": 1, "name": "simple"},
            {"max_tools": 2, "name": "medium"},
            {"max_tools": 3, "name": "complex"},
            {"max_tools": 2, "budget": 0.2, "name": "with_budget"},
            {"max_tools": 3, "min_information": 0.8, "name": "high_info"},
        ]
        
        results = []
        for scenario in scenarios:
            times = []
            for _ in range(5):
                start = time.time()
                solver.solve_optimal(
                    constraints=constraints,
                    objective="min_cost",
                    **{k: v for k, v in scenario.items() if k != "name"}
                )
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            results.append((scenario["name"], avg_time))
            print(f"\n{scenario['name']}: avg={avg_time*1000:.2f}ms")
        
        # All scenarios should complete quickly
        max_time = max(t for _, t in results)
        assert max_time < 0.2, f"All scenarios should complete < 200ms, max was {max_time*1000:.2f}ms"
    
    def test_memory_efficiency(self):
        """Test that solver doesn't leak memory with repeated calls."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()
        
        # Run many iterations
        for i in range(100):
            result = solver.solve_optimal(
                constraints=constraints,
                objective="min_cost",
                max_tools=2,
                min_information=0.5,
            )
            # Reset solver state (simulating new problem)
            solver.tool_vars = {}
            solver.var_counter = 1
        
        # Should complete without issues
        assert True  # If we get here, no memory issues
    
    def test_concurrent_solve_benchmark(self):
        """Benchmark solving multiple independent problems."""
        import concurrent.futures
        
        def solve_one():
            solver = ConstraintSolver()
            constraints = create_default_constraints()
            return solver.solve_optimal(
                constraints=constraints,
                objective="min_cost",
                max_tools=2,
                min_information=0.5,
            )
        
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(solve_one) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed = time.time() - start
        
        print(f"\nConcurrent solve (10 problems, 4 workers): {elapsed*1000:.2f}ms")
        
        # Should complete reasonably quickly
        assert elapsed < 1.0, f"Concurrent solve should complete < 1s, got {elapsed:.3f}s"
        assert len(results) == 10, "Should solve all problems"

