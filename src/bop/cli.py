"""CLI interface for BOP."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# .env is auto-loaded by src/bop/__init__.py when package is imported
from .agent import KnowledgeAgent
from .display_helpers import create_trust_table
from .eval import EvaluationFramework
from .ingestion import BOPIngestion
from .provenance_viz import (
    create_provenance_heatmap,
    create_relevance_breakdown_display,
)
from .quality_feedback import QualityFeedbackLoop
from .query_refinement import create_query_refinement_panel
from .schemas import get_schema, list_schemas
from .semantic_eval import SemanticEvaluator
from .visualizations import (
    create_document_relationship_graph,
    create_source_matrix_heatmap,
    create_token_importance_chart,
    create_trust_metrics_chart,
)

app = typer.Typer(help="BOP: Knowledge Structure Research Agent")
console = Console()


@app.command()
def chat(
    schema: Optional[str] = typer.Option(None, "--schema", "-s", help="Use structured reasoning schema"),
    research: bool = typer.Option(False, "--research", "-r", help="Enable deep research"),
    content_dir: Optional[Path] = typer.Option(None, "--content-dir", help="Content directory"),
    quality_feedback: bool = typer.Option(True, "--quality-feedback/--no-quality-feedback", help="Enable quality feedback loop"),
    use_constraints: bool = typer.Option(None, "--constraints/--no-constraints", help="Use constraint solver for tool selection (default: from BOP_USE_CONSTRAINTS env)"),
    show_details: bool = typer.Option(False, "--show-details", help="Show full response instead of summary (progressive disclosure)"),
    enable_skills: bool = typer.Option(False, "--skills/--no-skills", help="Enable Skills pattern for dynamic context loading"),
    enable_reminders: bool = typer.Option(False, "--reminders/--no-reminders", help="Enable system reminders to keep agent on track"),
) -> None:
    """Start interactive chat session."""
    agent = KnowledgeAgent(
        content_dir=content_dir,
        enable_quality_feedback=quality_feedback,
        enable_skills=enable_skills,
        enable_system_reminders=enable_reminders,
    )

    # Override constraint solver setting if specified
    if use_constraints is not None:
        import os
        os.environ["BOP_USE_CONSTRAINTS"] = "true" if use_constraints else "false"
        # Re-initialize orchestrator with new setting
        from .constraints import PYSAT_AVAILABLE, ConstraintSolver
        agent.orchestrator.use_constraints = use_constraints and PYSAT_AVAILABLE
        if agent.orchestrator.use_constraints and PYSAT_AVAILABLE:
            agent.orchestrator.constraint_solver = ConstraintSolver()
            console.print("[bold green]Constraint solver enabled[/bold green]")
        elif use_constraints and not PYSAT_AVAILABLE:
            console.print("[bold yellow]Constraint solver requested but PySAT not available[/bold yellow]")

    console.print(Panel.fit("[bold blue]BOP Chat Interface[/bold blue]", border_style="blue"))
    console.print("Type 'help' for commands, 'exit' to quit\n")

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")

            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("\n[bold green]Goodbye![/bold green]")
                break

            if user_input.lower() == "help":
                console.print("\n[bold]Available commands:[/bold]")
                console.print("  help          - Show this help")
                console.print("  exit/quit/q   - Exit chat")
                console.print("  schemas       - List available reasoning schemas")
                console.print("  schema <name> - Use a specific schema")
                console.print("  research on/off - Toggle research mode")
                console.print("  history       - Show conversation history")
                console.print("  clear         - Clear conversation history")
                console.print("  quality       - Show quality performance summary")
                continue

            if user_input.lower() == "schemas":
                schemas = list_schemas()
                console.print(f"\n[bold]Available schemas:[/bold] {', '.join(schemas)}")
                for schema_name in schemas:
                    schema = get_schema(schema_name)
                    if schema:
                        console.print(f"  - [cyan]{schema_name}[/cyan]: {schema.description}")
                continue

            if user_input.lower().startswith("schema "):
                schema_name = user_input.split(" ", 1)[1]
                schema_obj = get_schema(schema_name)
                if schema_obj:
                    console.print(f"\n[bold green]Using schema:[/bold green] {schema_name}")
                    schema = schema_name
                else:
                    console.print(f"\n[bold red]Unknown schema:[/bold red] {schema_name}")
                    schema = None
                continue

            if user_input.lower() in ["research on", "research off"]:
                research = "on" in user_input.lower()
                console.print(f"\n[bold green]Research mode:[/bold green] {'enabled' if research else 'disabled'}")
                continue

            if user_input.lower() == "history":
                history = agent.get_conversation_history()
                if history:
                    for msg in history[-10:]:  # Show last 10 messages
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        console.print(f"\n[{role}]: {content[:200]}...")
                else:
                    console.print("\n[italic]No conversation history[/italic]")
                continue

            if user_input.lower() == "clear":
                agent.clear_history()
                console.print("\n[bold green]History cleared[/bold green]")
                continue

            if user_input.lower() == "quality":
                if agent.quality_feedback:
                    summary = agent.quality_feedback.get_performance_summary()
                    console.print("\n[bold]Quality Performance Summary[/bold]")
                    console.print(f"Total evaluations: {summary.get('total_evaluations', 0)}")
                    console.print(f"Recent mean score: {summary.get('recent_mean_score', 0):.3f}")

                    schema_perf = summary.get('schema_performance', {})
                    if schema_perf:
                        console.print("\n[bold]Schema Performance:[/bold]")
                        for schema, score in sorted(schema_perf.items(), key=lambda x: x[1], reverse=True):
                            console.print(f"  {schema}: {score:.3f}")

                    issues = summary.get('quality_issue_frequency', {})
                    if issues:
                        console.print("\n[bold]Common Quality Issues:[/bold]")
                        for issue, count in issues.items():
                            console.print(f"  {issue}: {count}")
                else:
                    console.print("\n[dim]Quality feedback not enabled[/dim]")
                continue

            # Process message (async)
            try:
                response = asyncio.run(agent.chat(user_input, use_schema=schema, use_research=research))
                # Store original query for query refinement
                response["_original_query"] = user_input
            except Exception as e:
                console.print(f"\n[bold red]Error during chat:[/bold red] {e}")
                continue

            # Display response
            console.print("\n[bold green]Assistant[/bold green]")
            if response.get("schema_used"):
                console.print(f"[dim]Using schema: {response['schema_used']}[/dim]")
            if response.get("research_conducted"):
                console.print("[dim]Research conducted[/dim]")
                # Show topology metrics if available
                if response.get("research") and isinstance(response["research"], dict):
                    topology = response["research"].get("topology", {})
                    if topology:
                        trust_summary = topology.get("trust_summary", {})
                        if trust_summary:
                            # Enhanced trust display with visual chart
                            console.print("\n" + "═"*80)
                            console.print("[bold magenta]📊 Trust & Uncertainty Metrics[/bold magenta]")
                            console.print("═"*80)
                            trust_chart = create_trust_metrics_chart(
                                trust_summary,
                                topology.get("source_credibility")
                            )
                            console.print("\n")
                            console.print(trust_chart)

                            # Also show table for detailed metrics
                            trust_table = create_trust_table(
                                trust_summary,
                                topology.get("source_credibility")
                            )
                            console.print("\n")
                            console.print(trust_table)

                            # Source credibility (with better formatting)
                            source_cred = topology.get("source_credibility")
                            if source_cred:
                                console.print("\n[bold cyan]📚 Source Credibility[/bold cyan]")
                                sorted_sources = sorted(source_cred.items(), key=lambda x: x[1], reverse=True)
                                for source, cred in sorted_sources[:5]:  # Top 5
                                    color = "green" if cred > 0.7 else "yellow" if cred > 0.5 else "red"
                                    bar_length = int(cred * 20)
                                    bar = "█" * bar_length + "░" * (20 - bar_length)
                                    console.print(f"  [{color}]{bar}[/{color}] {source[:30]:30s} {cred:.3f}")

                            # Verification counts and source diversity
                            verification_info = topology.get("verification_info", {})
                            if verification_info:
                                console.print("\n[bold cyan]✅ Source Verification & Diversity[/bold cyan]")
                                for source, info in list(verification_info.items())[:5]:
                                    verifications = info.get("verification_count", 0)
                                    nodes = info.get("nodes", 0)
                                    diversity_emoji = "🟢" if nodes >= 3 else "🟡" if nodes >= 2 else "🔴"
                                    console.print(
                                        f"  {diversity_emoji} {source[:30]:30s} {verifications} verifications, {nodes} nodes"
                                    )

                            # Clique clusters (with better formatting)
                            cliques = topology.get("cliques", [])
                            if cliques:
                                console.print("\n[bold cyan]🔗 Source Agreement Clusters[/bold cyan]")
                                trusted_cliques = [
                                    c for c in cliques
                                    if c.get("trust", 0) > 0.5 and c.get("risk", 1.0) < 0.5
                                ]
                                trusted_cliques.sort(key=lambda x: x.get("trust", 0), reverse=True)
                                for i, clique in enumerate(trusted_cliques[:3]):  # Top 3
                                    sources = clique.get("node_sources", [])
                                    unique_sources = clique.get("unique_sources", list(set(sources)))[:3]
                                    source_diversity = clique.get("source_diversity", len(unique_sources))
                                    verifications = clique.get("verification_count", 0)
                                    trust = clique.get("trust", 0)
                                    trust_emoji = "🟢" if trust > 0.7 else "🟡" if trust > 0.5 else "🔴"
                                    console.print(
                                        f"  {trust_emoji} Cluster {i+1}: {len(sources)} sources agree "
                                        f"({', '.join(unique_sources)})"
                                    )
                                    console.print(
                                        f"     Trust: {trust:.3f} | Diversity: {source_diversity} | "
                                        f"Verifications: {verifications}"
                                    )

                        if topology.get("attractor_basins"):
                            console.print(f"[dim]Attractor basins: {topology['attractor_basins']}[/dim]")
            if response.get("research_error"):
                console.print(f"[dim yellow]Research warning: {response['research_error']}[/dim yellow]")

            # Show pipeline uncertainty tracking if available
            if response.get("research") and response["research"].get("pipeline_uncertainty"):
                pipeline_unc = response["research"]["pipeline_uncertainty"]
                console.print("\n" + "─"*80)
                console.print("[bold cyan]🔬 Pipeline Uncertainty Tracking[/bold cyan]")
                console.print("─"*80)

                # Operational uncertainty (pre-training to inference)
                console.print("\n[bold]Operational Uncertainty:[/bold]")
                operational_items = [
                    ("Query Decomposition", pipeline_unc.get("query_decomposition", 0.5)),
                    ("Tool Selection", pipeline_unc.get("tool_selection", 0.5)),
                    ("Tool Execution", pipeline_unc.get("tool_execution", 0.5)),
                    ("Result Aggregation", pipeline_unc.get("result_aggregation", 0.5)),
                ]
                for label, value in operational_items:
                    bar_length = int(value * 20)
                    bar = "█" * bar_length + "░" * (20 - bar_length)
                    color = "red" if value > 0.7 else "yellow" if value > 0.5 else "green"
                    console.print(f"  {label:25} [{color}]{bar}[/{color}] {value:.3f}")

                # Output uncertainty (quality of generated content)
                console.print("\n[bold]Output Uncertainty:[/bold]")
                output_items = [
                    ("Synthesis", pipeline_unc.get("synthesis", 0.5)),
                    ("Final Response", pipeline_unc.get("final_response", 0.5)),
                ]
                for label, value in output_items:
                    bar_length = int(value * 20)
                    bar = "█" * bar_length + "░" * (20 - bar_length)
                    color = "red" if value > 0.7 else "yellow" if value > 0.5 else "green"
                    console.print(f"  {label:25} [{color}]{bar}[/{color}] {value:.3f}")

            # Show quality feedback if available (with better visual hierarchy)
            if response.get("quality"):
                quality = response["quality"]
                score = quality.get("score", 0)
                flags = quality.get("flags", [])
                suggestions = quality.get("suggestions", [])

                # Score indicator with visual bar
                score_bar_length = int(score * 30)
                score_bar = "█" * score_bar_length + "░" * (30 - score_bar_length)
                if score >= 0.7:
                    score_emoji = "🟢"
                    score_color = "green"
                elif score >= 0.5:
                    score_emoji = "🟡"
                    score_color = "yellow"
                else:
                    score_emoji = "🔴"
                    score_color = "red"

                console.print(f"\n[bold]{score_emoji} Quality Score:[/bold] [{score_color}]{score_bar}[/{score_color}] {score:.3f}")

                # Show high-priority suggestions
                high_priority = [s for s in suggestions if s.get("priority") == "high"]
                if high_priority:
                    console.print(f"[bold red]⚠️  {high_priority[0]['message']}[/bold red]")

                # Show flags if any
                if flags:
                    console.print(f"[dim]Flags: {', '.join(flags[:3])}[/dim]")

            # Progressive disclosure: show summary first, allow expansion
            response_tiers = response.get("response_tiers", {})
            if show_details:
                # Show full detailed response with visual hierarchy
                if response_tiers and response_tiers.get("detailed"):
                    console.print("\n" + "="*80)
                    console.print("[bold cyan]📖 Full Response[/bold cyan]")
                    console.print("="*80)
                    console.print(Markdown(response_tiers["detailed"]))
                else:
                    console.print("\n" + "="*80)
                    console.print("[bold cyan]📖 Response[/bold cyan]")
                    console.print("="*80)
                    console.print(Markdown(response.get("response", "No response generated")))
            elif response_tiers and response_tiers.get("summary"):
                # Show summary with visual hint
                console.print("\n" + "─"*80)
                console.print("[bold cyan]📋 Summary[/bold cyan]")
                console.print("─"*80)
                console.print(Markdown(response_tiers["summary"]))
                console.print("\n[dim italic]💡 Tip: Use [bold]--show-details[/bold] to see full response with all details[/dim italic]")
            else:
                # Fallback to full response if no tiers
                console.print("\n" + "─"*80)
                console.print("[bold cyan]💬 Response[/bold cyan]")
                console.print("─"*80)
                console.print(Markdown(response.get("response", "No response generated")))

            # Show belief alignment if prior beliefs exist
            prior_beliefs = response.get("prior_beliefs", [])
            if prior_beliefs:
                console.print("\n" + "─"*80)
                console.print("[bold blue]🧠 Belief-Evidence Alignment[/bold blue]")
                console.print("─"*80)
                for belief in prior_beliefs:
                    console.print(f"  📌 [italic]Your belief:[/italic] \"{belief['text'][:60]}...\"")
                console.print("  [dim]Evidence alignment computed based on your stated beliefs[/dim]")

            # Show source matrix if available (visual heatmap)
            if response.get("research") and isinstance(response["research"], dict):
                research_data = response["research"]

                # Visualizations section header
                has_viz = (
                    research_data.get("source_matrix", {}) or
                    (research_data.get("token_importance", {}).get("term_importance")) or
                    (response.get("research", {}).get("topology", {}).get("cliques", []))
                )

                if has_viz:
                    console.print("\n" + "═"*80)
                    console.print("[bold green]📈 Knowledge Visualizations[/bold green]")
                    console.print("═"*80)

                source_matrix = research_data.get("source_matrix", {})
                if source_matrix:
                    console.print("\n[bold yellow]Source Agreement Matrix[/bold yellow]")
                    heatmap = create_source_matrix_heatmap(source_matrix, max_claims=8)
                    console.print(heatmap)

                # Token importance visualization
                token_importance = research_data.get("token_importance", {})
                if token_importance and token_importance.get("term_importance"):
                    console.print("\n[bold yellow]Token Importance[/bold yellow]")
                    token_chart = create_token_importance_chart(token_importance, max_terms=12)
                    console.print(token_chart)

                # Document relationship graph
                topology = response["research"].get("topology", {}) if response.get("research") else {}
                cliques = topology.get("cliques", []) if topology else []
                if cliques:
                    console.print("\n[bold yellow]Document Relationships[/bold yellow]")
                    relationship_graph = create_document_relationship_graph(cliques, max_cliques=5)
                    console.print(relationship_graph)

                # Token-level provenance (shows which query tokens matched which document tokens)
                provenance = research_data.get("provenance", {})
                if provenance:
                    console.print("\n[bold yellow]Token-Level Provenance[/bold yellow]")
                    provenance_heatmap = create_provenance_heatmap(provenance, max_claims=5)
                    console.print(provenance_heatmap)

                    # Show relevance breakdowns for top claims
                    console.print("\n[bold cyan]Relevance Score Breakdowns[/bold cyan]")
                    sorted_claims = sorted(
                        provenance.items(),
                        key=lambda x: x[1].get("num_sources", 0),
                        reverse=True
                    )[:3]

                    for claim_text, provenance_info in sorted_claims:
                        sources = provenance_info.get("sources", [])
                        if sources:
                            top_source = sources[0]
                            relevance_breakdown = top_source.get("relevance_breakdown", {})
                            if relevance_breakdown:
                                claim_short = claim_text[:60] + "..." if len(claim_text) > 60 else claim_text
                                console.print(f"\n[bold]Claim:[/bold] {claim_short}")
                                breakdown_display = create_relevance_breakdown_display(relevance_breakdown)
                                console.print(breakdown_display)

                    # Show query refinement suggestions
                    # Use the original user input from the response
                    original_query = response.get("_original_query") or response.get("message", "")
                    if original_query:
                        console.print("\n[bold green]Query Refinement Suggestions[/bold green]")
                        refinement_panel = create_query_refinement_panel(provenance, original_query)
                        if refinement_panel:
                            console.print(refinement_panel)

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")


@app.command()
def research(
    query: str,
    focus: Optional[str] = typer.Option(None, "--focus", help="Focus area for research"),
    max_results: int = typer.Option(10, "--max-results", help="Maximum results"),
) -> None:
    """Conduct deep research on a topic."""
    agent = KnowledgeAgent()
    focus_areas = [focus] if focus else None

    console.print(f"[bold blue]Researching:[/bold blue] {query}")
    try:
        result = asyncio.run(agent.research_agent.deep_research(query, focus_areas, max_results))
    except Exception as e:
        console.print(f"[bold red]Research error:[/bold red] {e}")
        return

    console.print("\n[bold]Research Results:[/bold]")
    console.print(Markdown(result.get("summary", "No summary available")))


@app.command()
def schemas() -> None:
    """List all available reasoning schemas."""
    schemas_list = list_schemas()
    console.print(f"\n[bold]Available Schemas ({len(schemas_list)}):[/bold]\n")

    for schema_name in schemas_list:
        schema = get_schema(schema_name)
        if schema:
            console.print(Panel(
                f"[bold cyan]{schema.name}[/bold cyan]\n\n"
                f"{schema.description}\n\n"
                f"[dim]Schema structure:[/dim]\n{schema.schema_def}",
                title=f"Schema: {schema.name}",
                border_style="cyan",
            ))


@app.command()
def eval(
    test_dir: Optional[Path] = typer.Option(None, "--test-dir", help="Test directory"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    content_dir: Optional[Path] = typer.Option(None, "--content-dir", help="Content directory for evaluation"),
) -> None:
    """Run evaluation framework."""
    framework = EvaluationFramework()
    console.print("[bold blue]Running evaluations...[/bold blue]")

    # Use content directory if provided, otherwise try default
    if not content_dir:
        content_dir = Path(__file__).parent.parent.parent / "content"
        if not content_dir.exists():
            content_dir = None

    if content_dir:
        console.print(f"[dim]Using content from: {content_dir}[/dim]")

    results = framework.run_evaluations(content_dir=content_dir)

    console.print("\n[bold]Evaluation Results:[/bold]")
    passed_count = 0
    total_count = 0

    for test_name, result in results.items():
        total_count += 1
        passed = result.get("passed", False)
        if passed:
            passed_count += 1
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        score = result.get("score", 0)
        error = result.get("error")

        console.print(f"{status} {test_name}: {score:.2f}")
        if error:
            console.print(f"  [dim red]Error: {error}[/dim red]")
        if result.get("details"):
            details = result["details"]
            if isinstance(details, dict):
                if details.get("test_cases"):
                    console.print(f"  [dim]Test cases: {details['test_cases']}[/dim]")
                if details.get("passed"):
                    console.print(f"  [dim]Passed: {details['passed']}/{details.get('test_cases', 0)}[/dim]")

    console.print(f"\n[bold]Summary:[/bold] {passed_count}/{total_count} tests passed")

    if output:
        framework.save_results(results, output)
        console.print(f"\n[bold green]Results saved to:[/bold green] {output}")


@app.command()
def semantic_eval(
    content_dir: Optional[Path] = typer.Option(None, "--content-dir", help="Content directory"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Output directory for results"),
    comprehensive: bool = typer.Option(False, "--comprehensive", help="Run comprehensive evaluation"),
) -> None:
    """Run semantic evaluation on realistic data."""
    from .agent import KnowledgeAgent
    from .research import load_content

    console.print("[bold blue]Running semantic evaluation...[/bold blue]")

    # Setup
    if not content_dir:
        content_dir = Path(__file__).parent.parent.parent / "content"

    output_dir = output_dir or Path("eval_outputs")
    evaluator = SemanticEvaluator(output_dir=output_dir)

    knowledge_base = load_content(content_dir) if content_dir.exists() else {}

    if not knowledge_base:
        console.print("[yellow]No content found, using synthetic queries[/yellow]")
        knowledge_base = {}

    agent = KnowledgeAgent()
    agent.llm_service = None

    # Run evaluations
    console.print("[dim]Evaluating semantic accuracy...[/dim]")
    for doc_name, doc_content in list(knowledge_base.items())[:3]:
        content_lower = doc_content.lower()
        concepts = []
        if "trust" in content_lower:
            concepts.append("trust")
        if "uncertainty" in content_lower:
            concepts.append("uncertainty")
        if "knowledge" in content_lower:
            concepts.append("knowledge")

        if concepts:
            query = f"What does {doc_name} say about {concepts[0]}?"
            response_obj = asyncio.run(agent.chat(query, use_schema="chain_of_thought", use_research=False))
            response = response_obj.get("response", "")

            evaluator.evaluate_accuracy(
                query=query,
                response=response,
                expected_concepts=concepts,
                metadata={"document": doc_name, "schema": "chain_of_thought"},
            )

    console.print("[dim]Evaluating semantic relevance...[/dim]")
    queries = [
        "What is knowledge structure?",
        "How does trust propagate?",
        "Why is uncertainty important?",
    ]
    for query in queries:
        response_obj = asyncio.run(agent.chat(query, use_schema="chain_of_thought", use_research=False))
        response = response_obj.get("response", "")
        evaluator.evaluate_relevance(query=query, response=response, metadata={"query_type": "general"})

    if comprehensive:
        console.print("[dim]Running comprehensive evaluation...[/dim]")
        # Add more evaluation types here

    # Save results
    console.print("\n[bold]Saving results...[/bold]")
    json_path = evaluator.save_judgments_json()
    csv_path = evaluator.save_judgments_csv()
    report_path = evaluator.save_summary_report()

    console.print(f"[green]✓[/green] JSON: {json_path}")
    console.print(f"[green]✓[/green] CSV: {csv_path}")
    console.print(f"[green]✓[/green] Report: {report_path}")

    # Show summary
    aggregate = evaluator.aggregate_judgments()
    console.print("\n[bold]Summary Statistics:[/bold]")

    table = Table(title="Semantic Evaluation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Judgments", str(aggregate.get("total_judgments", 0)))
    table.add_row("Overall Mean Score", f"{aggregate.get('overall', {}).get('mean_score', 0):.3f}")
    table.add_row("Score Range",
                  f"{aggregate.get('overall', {}).get('min_score', 0):.3f} - "
                  f"{aggregate.get('overall', {}).get('max_score', 0):.3f}")

    console.print(table)

    console.print("\n[bold]By Judgment Type:[/bold]")
    for j_type, stats in aggregate.get("by_type", {}).items():
        console.print(f"  {j_type}: {stats['mean']:.3f} (n={stats['count']})")

    console.print(f"\n[bold green]Results saved to:[/bold green] {output_dir}")


@app.command()
def sessions(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all sessions"),
    group_id: Optional[str] = typer.Option(None, "--group", "-g", help="Filter by group ID"),
    show_stats: bool = typer.Option(False, "--stats", help="Show session statistics"),
    limit: int = typer.Option(10, "--limit", help="Limit number of sessions"),
) -> None:
    """Manage hierarchical sessions."""

    feedback = QualityFeedbackLoop()
    if not feedback.session_manager:
        console.print("[yellow]Session management not enabled. Sessions are disabled.[/yellow]")
        return

    manager = feedback.session_manager

    if list_all or not show_stats:
        sessions_list = manager.list_sessions(group_id=group_id, limit=limit)

        if not sessions_list:
            console.print("[yellow]No sessions found.[/yellow]")
            return

        all_sessions = manager.list_sessions()
        console.print(f"\n[bold]Sessions[/bold] (showing {len(sessions_list)}/{len(all_sessions)})")

        table = Table()
        table.add_column("Session ID", style="cyan")
        table.add_column("Context", style="green")
        table.add_column("Evaluations", style="yellow")
        table.add_column("Mean Score", style="magenta")
        table.add_column("Updated", style="dim")

        for session in sessions_list:
            stats = session.get_statistics()
            session_id_short = session.session_id[:8] + "..."
            updated = session.updated_at[:10]  # Just date
            table.add_row(
                session_id_short,
                session.context or "N/A",
                str(stats["evaluation_count"]),
                f"{stats['mean_score']:.3f}",
                updated,
            )

        console.print(table)

    if show_stats:
        stats = manager.get_aggregate_statistics(group_id=group_id)

        console.print("\n[bold]Aggregate Statistics[/bold]")
        stats_table = Table()
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total Sessions", str(stats["session_count"]))
        stats_table.add_row("Total Evaluations", str(stats["total_evaluations"]))
        stats_table.add_row("Mean Score", f"{stats['mean_score']:.3f}")
        stats_table.add_row("Score Range", f"{stats['min_score']:.3f} - {stats['max_score']:.3f}")

        console.print(stats_table)

        if stats.get("schemas_used"):
            console.print(f"\n[bold]Schemas Used:[/bold] {', '.join(stats['schemas_used'])}")

        if stats.get("quality_issues"):
            console.print("\n[bold]Quality Issues:[/bold]")
            for issue, count in stats["quality_issues"].items():
                console.print(f"  {issue}: {count}")


@app.command()
def quality(
    show_history: bool = typer.Option(False, "--history", help="Show evaluation history"),
    show_adaptive: bool = typer.Option(False, "--adaptive", help="Show adaptive learning insights"),
) -> None:
    """Show quality performance summary and suggestions."""
    from .adaptive_quality import AdaptiveQualityManager

    feedback = QualityFeedbackLoop()
    summary = feedback.get_performance_summary()

    if "error" in summary:
        console.print(f"[yellow]{summary['error']}[/yellow]")
        return

    console.print("\n[bold]Quality Performance Summary[/bold]")
    console.print(f"Total evaluations: {summary.get('total_evaluations', 0)}")
    console.print(f"Recent mean score: {summary.get('recent_mean_score', 0):.3f}")
    console.print(f"Trend: {summary.get('trend', 'unknown')}")

    schema_perf = summary.get('schema_performance', {})
    if schema_perf:
        console.print("\n[bold]Schema Performance:[/bold]")
        table = Table()
        table.add_column("Schema", style="cyan")
        table.add_column("Mean Score", style="green")
        table.add_column("Evaluations", style="dim")

        for schema, score in sorted(schema_perf.items(), key=lambda x: x[1], reverse=True):
            count = len(feedback.schema_scores.get(schema, []))
            table.add_row(schema, f"{score:.3f}", str(count))

        console.print(table)

    issues = summary.get('quality_issue_frequency', {})
    if issues:
        console.print("\n[bold]Common Quality Issues:[/bold]")
        for issue, count in sorted(issues.items(), key=lambda x: x[1], reverse=True):
            console.print(f"  {issue}: {count} occurrences")

    # Show adaptive insights
    if show_adaptive:
        adaptive_manager = AdaptiveQualityManager(feedback)
        insights = adaptive_manager.get_performance_insights()

        console.print("\n[bold]Adaptive Learning Insights[/bold]")

        # Query type performance
        if insights.get("query_type_performance"):
            console.print("\n[bold]Query Type Performance:[/bold]")
            table = Table()
            table.add_column("Query Type", style="cyan")
            table.add_column("Mean Score", style="green")
            table.add_column("Samples", style="dim")

            for q_type, perf in insights["query_type_performance"].items():
                table.add_row(q_type, f"{perf['mean']:.3f}", str(perf['count']))
            console.print(table)

        # Schema recommendations
        if insights.get("schema_recommendations"):
            console.print("\n[bold]Schema Recommendations by Query Type:[/bold]")
            table = Table()
            table.add_column("Query Type", style="cyan")
            table.add_column("Best Schema", style="green")
            table.add_column("Score", style="yellow")
            table.add_column("Samples", style="dim")

            for q_type, rec in insights["schema_recommendations"].items():
                table.add_row(
                    q_type,
                    rec["schema"],
                    f"{rec['score']:.3f}",
                    str(rec["samples"])
                )
            console.print(table)

        # Research effectiveness
        if insights.get("research_effectiveness"):
            console.print("\n[bold]Research Effectiveness:[/bold]")
            table = Table()
            table.add_column("Query Type", style="cyan")
            table.add_column("With Research", style="green")
            table.add_column("Without Research", style="yellow")
            table.add_column("Improvement", style="magenta")

            for q_type, eff in insights["research_effectiveness"].items():
                improvement = eff["improvement"]
                improvement_str = f"{improvement:+.3f}" if improvement > 0 else f"{improvement:.3f}"
                improvement_style = "green" if improvement > 0 else "red"
                table.add_row(
                    q_type,
                    f"{eff['with_research']:.3f}",
                    f"{eff['without_research']:.3f}",
                    f"[{improvement_style}]{improvement_str}[/{improvement_style}]"
                )
            console.print(table)

        # Length preferences
        if insights.get("length_preferences"):
            console.print("\n[bold]Optimal Response Lengths:[/bold]")
            for q_type, pref in insights["length_preferences"].items():
                console.print(f"  {q_type}: {pref['optimal_length']} chars (range: {pref['range'][0]}-{pref['range'][1]})")

    if show_history:
        console.print("\n[bold]Recent Evaluations:[/bold]")
        for entry in feedback.history[-10:]:
            score = entry.get("score", 0)
            query = entry.get("query", "")[:50]
            flags = entry.get("quality_flags", [])
            status = "[green]✓[/green]" if score > 0.6 else "[yellow]⚠[/yellow]" if score > 0.4 else "[red]✗[/red]"
            console.print(f"{status} {score:.2f} | {query}... | {', '.join(flags) if flags else 'ok'}")


@app.command()
def validate_env(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all optional variables"),
) -> None:
    """Validate environment variable setup and .env file loading."""
    from bop import get_env_info, validate_env_setup

    console.print(Panel.fit("[bold cyan]BOP Environment Validation[/bold cyan]", border_style="cyan"))

    # Show .env file info
    env_info = get_env_info()
    console.print("\n[bold]Environment File:[/bold]")
    if env_info["has_env_file"]:
        console.print(f"  ✅ Loaded from: [green]{env_info['env_file_path']}[/green]")
    else:
        console.print("  ⚠️  No .env file found (using system environment variables)")
        console.print(f"  [dim]Repo root: {env_info['repo_root']}[/dim]")
        console.print("  [dim]Tip: Create .env file in repo root with your API keys[/dim]")

    # Validate setup
    is_valid, issues = validate_env_setup(verbose=verbose)

    console.print("\n[bold]Available Configuration:[/bold]")
    if issues["available"]:
        for item in issues["available"]:
            console.print(f"  {item}")
    else:
        console.print("  [dim]No API keys found[/dim]")

    if issues["missing_required"]:
        console.print("\n[bold red]Missing Required:[/bold red]")
        for item in issues["missing_required"]:
            console.print(f"  ❌ {item}")

    if verbose and issues["missing_optional"]:
        console.print("\n[bold yellow]Missing Optional:[/bold yellow]")
        for item in issues["missing_optional"]:
            console.print(f"  {item}")

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    if is_valid:
        console.print("  [bold green]✅ Environment setup is valid[/bold green]")
        console.print("  [dim]All required variables are set[/dim]")
    else:
        console.print("  [bold red]❌ Environment setup is invalid[/bold red]")
        console.print("  [dim]Missing required variables. See above for details.[/dim]")
        console.print("\n[dim]To fix:[/dim]")
        console.print("  1. Copy .env.example to .env: [cyan]cp .env.example .env[/cyan]")
        console.print("  2. Edit .env and add your API keys")
        console.print("  3. At least one LLM backend key is required")

    # Exit with error code if invalid
    if not is_valid:
        raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port to bind to (default: PORT env or 8000)"),
    use_constraints: bool = typer.Option(True, "--constraints/--no-constraints", help="Enable constraint solver"),
) -> None:
    """Start HTTP server for remote access (e.g., via Tailscale or Fly.io)."""
    import os

    import uvicorn

    # Set constraint solver environment variable
    os.environ["BOP_USE_CONSTRAINTS"] = "true" if use_constraints else "false"

    # Get port (Fly.io uses PORT, fallback to BOP_PORT or provided value or default)
    if port is None:
        port = int(os.getenv("PORT", os.getenv("BOP_PORT", "8000")))

    console.print(f"[bold blue]Starting BOP HTTP server on {host}:{port}[/bold blue]")
    if use_constraints:
        console.print("[bold green]Constraint solver enabled[/bold green]")
    else:
        console.print("[bold yellow]Constraint solver disabled[/bold yellow]")
    console.print("\n[dim]Access the API at:[/dim]")
    console.print(f"  [cyan]http://{host}:{port}[/cyan]")
    console.print(f"  [cyan]http://{host}:{port}/docs[/cyan] (API documentation)")
    console.print("\n[dim]For Tailscale access, use your Tailscale IP address[/dim]")
    console.print("[dim]For Fly.io, use your app URL (e.g., https://bop.fly.dev)[/dim]\n")

    from .server import app
    uvicorn.run(app, host=host, port=port, log_level="info")


@app.command()
def ingest(
    archive_path: Path = typer.Argument(..., help="Path to chat archive file or directory"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory (default: ./content/)"),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Force format (json, markdown, text)"),
    extract_metadata: bool = typer.Option(True, "--metadata/--no-metadata", help="Extract metadata"),
) -> None:
    """Ingest chat archives using HOP and prepare for BOP queries."""
    console.print(Panel.fit("[bold blue]BOP: Ingesting Chat Archives[/bold blue]", border_style="blue"))

    ingestion = BOPIngestion()

    if not ingestion.is_available():
        console.print("[red]Error: HOP is not available[/red]")
        console.print("[yellow]Install HOP with: pip install hop[/yellow]")
        console.print("[dim]Or use standalone HOP CLI: hop ingest <path>[/dim]")
        raise typer.Exit(1)

    # Default output directory
    if output_dir is None:
        output_dir = Path("./content/")

    try:
        result = ingestion.ingest_archives(
            archive_path=archive_path,
            output_dir=output_dir,
            extract_metadata=extract_metadata,
            format=format,
        )

        console.print(f"[green]✓ Processed {result['files_processed']} files[/green]")
        console.print(f"[green]✓ Extracted {result['messages_extracted']} messages[/green]")

        if result.get("metadata"):
            meta = result["metadata"]
            if meta.get("participants"):
                console.print(f"[dim]Participants: {', '.join(meta['participants'])}[/dim]")
            if meta.get("date_range"):
                dr = meta["date_range"]
                console.print(f"[dim]Date Range: {dr.get('earliest')} to {dr.get('latest')}[/dim]")

        console.print("\n[bold green]Content ready for BOP![/bold green]")
        console.print(f"[dim]Query with: bop chat --content-dir {output_dir}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Ingestion failed")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
