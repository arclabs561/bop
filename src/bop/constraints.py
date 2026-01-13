"""Constraint-based tool selection using SAT solvers."""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Try to import PySAT, but make it optional
try:
    from pysat.formula import CNF
    from pysat.solvers import Solver
    try:
        from pysat.card import CardEnc
        CARD_AVAILABLE = True
    except ImportError:
        CARD_AVAILABLE = False
        logger.warning("PySAT card module not available. Cardinality constraints will use fallback.")
    PYSAT_AVAILABLE = True
except ImportError:
    PYSAT_AVAILABLE = False
    CARD_AVAILABLE = False
    logger.warning("PySAT not available. Install with: uv pip install python-sat")


class ToolType(str, Enum):
    """Tool types for constraint encoding."""
    PERPLEXITY_DEEP = "perplexity_deep_research"
    PERPLEXITY_REASON = "perplexity_reason"
    PERPLEXITY_SEARCH = "perplexity_search"
    FIRECRAWL_SEARCH = "firecrawl_search"
    FIRECRAWL_SCRAPE = "firecrawl_scrape"
    FIRECRAWL_EXTRACT = "firecrawl_extract"
    TAVILY_SEARCH = "tavily_search"
    TAVILY_EXTRACT = "tavily_extract"


class ToolConstraint:
    """Represents constraints on tool selection."""

    def __init__(
        self,
        tool: ToolType,
        cost: float = 1.0,
        latency: float = 1.0,
        information_gain: float = 0.5,
        dependencies: Optional[List[ToolType]] = None,
        conflicts: Optional[List[ToolType]] = None,
        required: bool = False,
    ):
        """
        Initialize tool constraint.

        Args:
            tool: Tool type
            cost: API cost (normalized 0-1)
            latency: Estimated latency in seconds
            information_gain: Expected information completeness gain (0-1)
            dependencies: Tools that must be called before this one
            conflicts: Tools that conflict with this one (can't use together)
            required: Whether this tool is required
        """
        self.tool = tool
        self.cost = cost
        self.latency = latency
        self.information_gain = information_gain
        self.dependencies = dependencies or []
        self.conflicts = conflicts or []
        self.required = required


class ConstraintSolver:
    """
    Solves tool selection as a constraint satisfaction problem.

    Encodes tool selection as SAT constraints:
    - Tool availability
    - Dependencies (tool A before tool B)
    - Conflicts (tool A and tool B can't both be used)
    - Budget constraints (total cost <= budget)
    - Information requirements (total gain >= threshold)
    """

    def __init__(self):
        """Initialize the constraint solver."""
        if not PYSAT_AVAILABLE:
            raise ImportError(
                "PySAT not available. Install with: uv pip install python-sat "
                "or: uv sync --extra constraints"
            )
        self.tool_vars: Dict[ToolType, int] = {}
        self.var_counter = 1
        self.cnf = CNF()

    def _get_var(self, tool: ToolType) -> int:
        """Get or create variable for a tool."""
        if tool not in self.tool_vars:
            self.tool_vars[tool] = self.var_counter
            self.var_counter += 1
        return self.tool_vars[tool]

    def add_tool_constraints(
        self,
        constraints: List[ToolConstraint],
        available_tools: Optional[Set[ToolType]] = None,
    ) -> None:
        """
        Add constraints for tool selection.

        Args:
            constraints: List of tool constraints
            available_tools: Set of available tools (None = all tools)
        """
        if available_tools is None:
            available_tools = {c.tool for c in constraints}

        # Add variables for all tools
        for constraint in constraints:
            if constraint.tool in available_tools:
                self._get_var(constraint.tool)

        # Add constraints
        for constraint in constraints:
            if constraint.tool not in available_tools:
                continue

            tool_var = self._get_var(constraint.tool)

            # Required tools must be selected
            if constraint.required:
                self.cnf.append([tool_var])

            # Dependencies: if tool is selected, dependencies must be selected
            for dep in constraint.dependencies:
                if dep in available_tools:
                    dep_var = self._get_var(dep)
                    # tool_var -> dep_var (if tool selected, dep must be selected)
                    # Equivalent to: -tool_var OR dep_var
                    self.cnf.append([-tool_var, dep_var])

            # Conflicts: if tool is selected, conflicting tools cannot be selected
            for conflict in constraint.conflicts:
                if conflict in available_tools and conflict != constraint.tool:
                    conflict_var = self._get_var(conflict)
                    # tool_var -> -conflict_var (if tool selected, conflict not selected)
                    # Equivalent to: -tool_var OR -conflict_var
                    self.cnf.append([-tool_var, -conflict_var])

    def solve(
        self,
        constraints: List[ToolConstraint],
        budget: Optional[float] = None,
        min_information: Optional[float] = None,
        max_tools: Optional[int] = None,
        available_tools: Optional[Set[ToolType]] = None,
    ) -> Optional[List[ToolType]]:
        """
        Solve tool selection problem.

        Args:
            constraints: List of tool constraints
            budget: Maximum total cost (None = no budget constraint)
            min_information: Minimum total information gain (None = no requirement)
            max_tools: Maximum number of tools to select (None = no limit)
            available_tools: Set of available tools (None = all tools)

        Returns:
            List of selected tools, or None if no solution found
        """
        if not PYSAT_AVAILABLE:
            return None

        # Reset
        self.tool_vars = {}
        self.var_counter = 1
        self.cnf = CNF()

        # Add tool constraints
        self.add_tool_constraints(constraints, available_tools)

        # Add max tools constraint (if specified) - cardinality constraint
        if max_tools is not None:
            tool_vars_list = list(self.tool_vars.values())
            if tool_vars_list:
                if CARD_AVAILABLE:
                    # Use PySAT's CardEnc for efficient encoding
                    card_constraint = CardEnc.atmost(
                        lits=tool_vars_list,
                        bound=max_tools,
                        encoding=1  # Use sequential counter encoding
                    )
                    self.cnf.extend(card_constraint.clauses)
                else:
                    # Fallback: Use naive encoding (at-most-k)
                    # Generate all combinations of k+1 tools and add constraint
                    # that at least one must be false
                    from itertools import combinations
                    if len(tool_vars_list) > max_tools:
                        for combo in combinations(tool_vars_list, max_tools + 1):
                            # At least one must be false: -x1 OR -x2 OR ... OR -xk+1
                            self.cnf.append([-var for var in combo])

        # If min_information > 0, require at least one tool (at-least-1 constraint)
        # This prevents the trivial solution of selecting no tools
        if min_information is not None and min_information > 0:
            tool_vars_list = list(self.tool_vars.values())
            if tool_vars_list:
                # At least one must be true: x1 OR x2 OR ... OR xn
                self.cnf.append(tool_vars_list)

        # Add budget constraint (if specified) - pseudo-boolean constraint
        # Encode: sum(selected_tools * cost) <= budget
        if budget is not None:
            # Use iterative solving with filtering for budget constraint
            # This is more efficient than full pseudo-boolean encoding
            # We'll solve and filter solutions that exceed budget
            pass  # Will be handled in solve loop

        # Add information requirement (if specified) - pseudo-boolean constraint
        # Encode: sum(selected_tools * information_gain) >= min_information
        if min_information is not None:
            # Use iterative solving with filtering for information constraint
            # We'll solve and filter solutions that don't meet information requirement
            pass  # Will be handled in solve loop

        # Solve with budget and information filtering
        with Solver(bootstrap_with=self.cnf) as solver:
            max_iterations = 100  # Limit iterations to prevent infinite loops
            iteration = 0

            while solver.solve() and iteration < max_iterations:
                iteration += 1
                model = solver.get_model()
                selected = []
                for tool, var in self.tool_vars.items():
                    # PySAT models are lists of variable assignments
                    # Positive value = variable is true, negative = false
                    if var in model:
                        selected.append(tool)

                # Check budget constraint
                if budget is not None:
                    total_cost = sum(
                        next((c.cost for c in constraints if c.tool == t), 1.0)
                        for t in selected
                    )
                    if total_cost > budget:
                        # Block this solution and try again
                        # Block by negating all selected variables
                        blocking_clause = [-var for var in self.tool_vars.values() if var in model]
                        if blocking_clause:
                            solver.add_clause(blocking_clause)
                        continue

                # Check information requirement
                if min_information is not None:
                    total_info = sum(
                        next((c.information_gain for c in constraints if c.tool == t), 0.0)
                        for t in selected
                    )
                    if total_info < min_information:
                        # Block this solution and try again
                        # Block by negating all selected variables
                        blocking_clause = [-var for var in self.tool_vars.values() if var in model]
                        if blocking_clause:
                            solver.add_clause(blocking_clause)
                        continue

                # Solution satisfies all constraints
                return selected

        return None

    def solve_optimal(
        self,
        constraints: List[ToolConstraint],
        objective: str = "min_cost",  # "min_cost", "max_information", "min_latency"
        budget: Optional[float] = None,
        min_information: Optional[float] = None,
        max_tools: Optional[int] = None,
        available_tools: Optional[Set[ToolType]] = None,
    ) -> Optional[List[ToolType]]:
        """
        Solve tool selection with optimization objective.

        Uses iterative approach: find all solutions, then select best.
        For production, would use MaxSAT or pseudo-boolean optimization.

        Args:
            constraints: List of tool constraints
            objective: Optimization objective
            budget: Maximum total cost
            min_information: Minimum total information gain
            max_tools: Maximum number of tools
            available_tools: Set of available tools

        Returns:
            Optimal list of selected tools, or None if no solution
        """
        if not PYSAT_AVAILABLE:
            return None

        # Reset and build CNF
        self.tool_vars = {}
        self.var_counter = 1
        self.cnf = CNF()

        # Add tool constraints
        self.add_tool_constraints(constraints, available_tools)

        # Add max_tools constraint if specified (cardinality constraint)
        if max_tools is not None:
            # At-most-k: at most max_tools can be selected
            selected_vars = list(self.tool_vars.values())
            if len(selected_vars) > max_tools:
                # Generate all combinations of max_tools+1 variables
                # At least one must be false
                from itertools import combinations
                for combo in combinations(selected_vars, max_tools + 1):
                    # At least one must be false: -x1 OR -x2 OR ... OR -xk+1
                    self.cnf.append([-var for var in combo])

        # If min_information > 0, require at least one tool (at-least-1 constraint)
        # This prevents the trivial solution of selecting no tools
        if min_information is not None and min_information > 0:
            selected_vars = list(self.tool_vars.values())
            if selected_vars:
                # At least one must be true: x1 OR x2 OR ... OR xn
                self.cnf.append(selected_vars)

        # For now, use simple heuristic-based optimization
        # In production, would use MaxSAT solver or pseudo-boolean optimization

        # Get all valid solutions (with timeout protection)
        solutions = []
        max_solutions = 50  # Reduced limit to prevent explosion
        max_time_seconds = 2.0  # Timeout after 2 seconds

        import time
        start_time = time.time()

        with Solver(bootstrap_with=self.cnf) as solver:
            # Enumerate all solutions (with limit and timeout)
            solution_count = 0

            while solver.solve() and solution_count < max_solutions:
                # Check timeout
                if time.time() - start_time > max_time_seconds:
                    break

                model = solver.get_model()
                selected = []
                for tool, var in self.tool_vars.items():
                    # PySAT models are lists of variable assignments
                    # Positive value = variable is true, negative = false
                    if var in model:
                        selected.append(tool)

                # Evaluate solution
                total_cost = sum(
                    next((c.cost for c in constraints if c.tool == t), 1.0)
                    for t in selected
                )
                total_info = sum(
                    next((c.information_gain for c in constraints if c.tool == t), 0.0)
                    for t in selected
                )
                total_latency = sum(
                    next((c.latency for c in constraints if c.tool == t), 1.0)
                    for t in selected
                )

                # Check constraints
                selected_vars = [var for var in self.tool_vars.values() if var in model]

                if budget is not None and total_cost > budget:
                    # Block this specific assignment
                    if selected_vars:
                        blocking_clause = [-var for var in selected_vars]
                        solver.add_clause(blocking_clause)
                    solution_count += 1
                    continue
                if min_information is not None and total_info < min_information:
                    # Block this specific assignment
                    if selected_vars:
                        blocking_clause = [-var for var in selected_vars]
                        solver.add_clause(blocking_clause)
                    solution_count += 1
                    continue
                if max_tools is not None and len(selected) > max_tools:
                    # Block this specific assignment
                    if selected_vars:
                        blocking_clause = [-var for var in selected_vars]
                        solver.add_clause(blocking_clause)
                    solution_count += 1
                    continue

                solutions.append({
                    "tools": selected,
                    "cost": total_cost,
                    "information": total_info,
                    "latency": total_latency,
                })

                # Block this solution and continue
                # Block by saying: at least one selected variable must be false
                # This prevents finding the exact same solution again
                selected_vars = [var for var in self.tool_vars.values() if var in model]
                if selected_vars:
                    # At least one must be false: -var1 OR -var2 OR ... OR -varn
                    blocking_clause = [-var for var in selected_vars]
                    solver.add_clause(blocking_clause)
                solution_count += 1

        if not solutions:
            return None

        # Select best solution based on objective
        if objective == "min_cost":
            best = min(solutions, key=lambda s: s["cost"])
        elif objective == "max_information":
            best = max(solutions, key=lambda s: s["information"])
        elif objective == "min_latency":
            best = min(solutions, key=lambda s: s["latency"])
        else:
            # Default: minimize cost
            best = min(solutions, key=lambda s: s["cost"])

        return best["tools"]


def create_default_constraints() -> List[ToolConstraint]:
    """
    Create default tool constraints based on heuristics.

    Returns:
        List of tool constraints with default values
    """
    return [
        ToolConstraint(
            tool=ToolType.PERPLEXITY_DEEP,
            cost=0.3,
            latency=3.0,
            information_gain=0.8,
        ),
        ToolConstraint(
            tool=ToolType.PERPLEXITY_REASON,
            cost=0.2,
            latency=2.0,
            information_gain=0.6,
        ),
        ToolConstraint(
            tool=ToolType.PERPLEXITY_SEARCH,
            cost=0.1,
            latency=1.0,
            information_gain=0.4,
        ),
        ToolConstraint(
            tool=ToolType.FIRECRAWL_SEARCH,
            cost=0.15,
            latency=1.5,
            information_gain=0.5,
        ),
        ToolConstraint(
            tool=ToolType.FIRECRAWL_SCRAPE,
            cost=0.2,
            latency=2.0,
            information_gain=0.7,
            dependencies=[ToolType.FIRECRAWL_SEARCH],  # Search before scrape
        ),
        ToolConstraint(
            tool=ToolType.FIRECRAWL_EXTRACT,
            cost=0.25,
            latency=2.5,
            information_gain=0.8,
            dependencies=[ToolType.FIRECRAWL_SCRAPE],  # Scrape before extract
        ),
        ToolConstraint(
            tool=ToolType.TAVILY_SEARCH,
            cost=0.1,
            latency=1.0,
            information_gain=0.4,
            conflicts=[ToolType.PERPLEXITY_SEARCH],  # Don't use both search tools
        ),
        ToolConstraint(
            tool=ToolType.TAVILY_EXTRACT,
            cost=0.2,
            latency=2.0,
            information_gain=0.6,
        ),
    ]

