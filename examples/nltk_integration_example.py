"""
Concrete examples of NLTK integration improvements.

This script demonstrates:
- Enhanced token extraction with NLTK
- POS tagging for better term selection
- Fallback behavior when NLTK unavailable
"""

from pran.token_importance import extract_key_terms, NLTK_AVAILABLE
from rich.console import Console
from rich.table import Table

console = Console()

def example_basic_extraction():
    """Example: Basic key term extraction"""
    console.print("\n[bold cyan]Example 1: Basic Key Term Extraction[/bold cyan]")
    console.print("─" * 80)
    
    text = """
    Trust and uncertainty are crucial concepts in knowledge systems. 
    Information geometry provides mathematical foundations for understanding 
    how knowledge structures relate to each other. Bayesian networks use 
    d-separation to determine conditional independence relationships.
    """
    
    terms = extract_key_terms(text, max_terms=10)
    
    console.print(f"\n[bold]Input Text:[/bold]")
    console.print(f"[dim]{text.strip()}[/dim]")
    
    console.print(f"\n[bold]NLTK Available:[/bold] {'✅ Yes' if NLTK_AVAILABLE else '❌ No (using fallback)'}")
    console.print(f"[bold]Extracted Terms ({len(terms)}):[/bold]")
    for i, term in enumerate(terms, 1):
        console.print(f"  {i}. {term}")


def example_comparison():
    """Example: Comparison with and without NLTK"""
    console.print("\n[bold cyan]Example 2: NLTK vs Fallback Comparison[/bold cyan]")
    console.print("─" * 80)
    
    text = "The quick brown fox jumps over the lazy dog. Machine learning algorithms process data efficiently."
    
    terms_nltk = extract_key_terms(text, max_terms=10)
    
    console.print(f"\n[bold]Input:[/bold] {text}")
    console.print(f"\n[bold]With NLTK:[/bold] {', '.join(terms_nltk)}")
    console.print(f"[dim]NLTK filters stop words ('the', 'over', 'the') and focuses on content words[/dim]")


def example_domain_specific():
    """Example: Domain-specific terminology extraction"""
    console.print("\n[bold cyan]Example 3: Domain-Specific Terminology[/bold cyan]")
    console.print("─" * 80)
    
    texts = [
        """
        D-separation is a graphical criterion for determining conditional 
        independence in Bayesian networks. It uses the graph structure to 
        identify blocked paths between variables.
        """,
        """
        Information geometry studies the geometric structure of probability 
        distributions. Fisher information provides a metric tensor for 
        statistical manifolds.
        """,
        """
        Trust metrics quantify the reliability of information sources. 
        Calibration error measures how well confidence scores match actual 
        accuracy. Source credibility depends on verification counts.
        """,
    ]
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Domain", style="cyan")
    table.add_column("Key Terms", style="green")
    
    domains = ["Causal Inference", "Information Geometry", "Trust & Uncertainty"]
    
    for domain, text in zip(domains, texts):
        terms = extract_key_terms(text, max_terms=8)
        table.add_row(domain, ", ".join(terms))
    
    console.print(table)


def example_pos_tagging():
    """Example: POS tagging benefits"""
    console.print("\n[bold cyan]Example 4: POS Tagging Benefits[/bold cyan]")
    console.print("─" * 80)
    
    text = """
    The running algorithm processes data quickly. The processed data shows 
    significant improvements. Processing requires careful attention to detail.
    """
    
    terms = extract_key_terms(text, max_terms=10)
    
    console.print(f"\n[bold]Input:[/bold]")
    console.print(f"[dim]{text.strip()}[/dim]")
    
    console.print(f"\n[bold]Extracted Terms:[/bold] {', '.join(terms)}")
    console.print(f"[dim]NLTK POS tagging helps identify content words (nouns, adjectives, verbs) "
                  f"and filter out function words and common verbs like 'is', 'shows', 'requires'[/dim]")


if __name__ == "__main__":
    console.print("[bold blue]NLTK Integration Examples[/bold blue]")
    console.print("\nDemonstrating enhanced token extraction capabilities:\n")
    
    example_basic_extraction()
    example_comparison()
    example_domain_specific()
    example_pos_tagging()
    
    console.print("\n" + "="*80)
    console.print(f"[bold green]✅ NLTK Status: {'Available' if NLTK_AVAILABLE else 'Unavailable (using fallback)'}[/bold green]")
    console.print("="*80)

