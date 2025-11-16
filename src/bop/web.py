"""Modern web interface using marimo + manus for mobile-friendly chat."""

import asyncio
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

import marimo
from marimo import ui
from manus import components

from .agent import KnowledgeAgent
from .quality_feedback import QualityFeedbackLoop
from .visualizations import (
    create_source_matrix_heatmap,
    create_token_importance_chart,
    create_document_relationship_graph,
)
from .provenance_viz import (
    create_provenance_heatmap,
    create_provenance_summary,
    format_clickable_source,
    create_relevance_breakdown_display,
)
from .query_refinement import create_query_refinement_panel, suggest_followup_queries

# Initialize agent (lazy loading)
_agent: Optional[KnowledgeAgent] = None


def get_agent() -> KnowledgeAgent:
    """Get or create the knowledge agent."""
    global _agent
    if _agent is None:
        _agent = KnowledgeAgent(enable_quality_feedback=True)
    return _agent


# ============================================================================
# UI Components
# ============================================================================

def create_chat_interface():
    """Create the main chat interface."""
    
    # Chat state
    messages = ui.state([])
    input_text = ui.text_area(
        label="",
        placeholder="Ask me anything about knowledge structures, reasoning, or research...",
        full_width=True,
        rows=3,
    )
    research_toggle = ui.switch(label="Enable Research", value=True)
    show_visualizations = ui.switch(label="Show Visualizations", value=True)
    exploration_mode = ui.switch(label="Exploration Mode", value=False)
    schema_select = ui.dropdown(
        label="Reasoning Schema",
        options=[
            ("Auto (Adaptive)", None),
            ("Chain of Thought", "chain_of_thought"),
            ("Decompose and Synthesize", "decompose_and_synthesize"),
            ("Iterative Elaboration", "iterative_elaboration"),
            ("Hypothesize and Test", "hypothesize_and_test"),
            ("Scenario Analysis", "scenario_analysis"),
        ],
        value=None,
    )
    
    async def send_message():
        """Send a message and get response."""
        if not input_text.value or not input_text.value.strip():
            return
        
        user_message = input_text.value.strip()
        
        # Add user message to chat
        messages.value = messages.value + [{
            "role": "user",
            "content": user_message,
            "timestamp": asyncio.get_event_loop().time(),
        }]
        
        # Clear input
        input_text.value = ""
        
        # Add thinking indicator
        thinking_id = len(messages.value)
        messages.value = messages.value + [{
            "role": "assistant",
            "content": "Thinking...",
            "thinking": True,
            "timestamp": asyncio.get_event_loop().time(),
        }]
        
        try:
            # Get agent response
            agent = get_agent()
            # Track exploration mode for context-dependent adaptation
            # (The agent already does this internally, but we can pass hints)
            response = await agent.chat(
                message=user_message,
                use_schema=schema_select.value,
                use_research=research_toggle.value,
            )
            
            # Store exploration mode preference in response metadata
            if exploration_mode.value:
                response["metadata"] = response.get("metadata", {})
                response["metadata"]["exploration_mode"] = True
            
            # Update thinking message with actual response
            # Use progressive disclosure: show summary first, allow expansion
            response_tiers = response.get("response_tiers", {})
            if response_tiers and response_tiers.get("summary"):
                # Show summary first (progressive disclosure)
                # Store full tiers for potential expansion in UI
                response_text = response_tiers["summary"]
                # Note: Full expansion would require UI state management
                # For now, show summary with hint about available tiers
                if response_tiers.get("detailed") or response_tiers.get("evidence"):
                    response_text += "\n\n*[Full response available in response_tiers]*"
            else:
                response_text = response.get("response", "No response generated.")
            
            quality = response.get("quality", {})
            quality_score = quality.get("score") if quality else None
            
            # Format response with metadata
            formatted_response = response_text
            if quality_score:
                formatted_response += f"\n\n*Quality Score: {quality_score:.2f}*"
            
            # Add trust metrics and visualizations if available
            if response.get("research") and isinstance(response["research"], dict):
                research_data = response["research"]
                topology = research_data.get("topology", {})
                if topology:
                    trust_summary = topology.get("trust_summary", {})
                    if trust_summary:
                        avg_trust = trust_summary.get("avg_trust", 0)
                        formatted_response += f"\n\n*Trust: {avg_trust:.2f}*"
                
                # Add token importance info
                token_importance = research_data.get("token_importance", {})
                if token_importance and token_importance.get("top_terms"):
                    top_terms = token_importance["top_terms"][:5]
                    formatted_response += f"\n\n*Key terms: {', '.join(top_terms)}*"
                
                # Add source matrix summary
                source_matrix = research_data.get("source_matrix", {})
                if source_matrix:
                    claim_count = len(source_matrix)
                    formatted_response += f"\n\n*Source analysis: {claim_count} claims analyzed*"
            
            # Store visualization data for interactive exploration
            visualization_data = {}
            tooltip_data_map = {}  # Store tooltip data for clickable sources
            if show_visualizations.value and response.get("research"):
                research_data = response["research"]
                visualization_data = {
                    "source_matrix": research_data.get("source_matrix", {}),
                    "token_importance": research_data.get("token_importance", {}),
                    "topology": research_data.get("topology", {}),
                    "provenance": research_data.get("provenance", {}),
                }
                
                # Add visualization summaries to formatted response if enabled
                if visualization_data.get("token_importance", {}).get("top_terms"):
                    top_terms = visualization_data["token_importance"]["top_terms"][:8]
                    formatted_response += f"\n\n**🔑 Key Terms Driving Retrieval:**\n"
                    formatted_response += ", ".join([f"`{term}`" for term in top_terms])
                
                if visualization_data.get("source_matrix"):
                    claim_count = len(visualization_data["source_matrix"])
                    formatted_response += f"\n\n**📊 Source Agreement:** {claim_count} claims analyzed"
                    # Show consensus summary
                    agreements = sum(1 for c in visualization_data["source_matrix"].values() 
                                   if c.get("consensus") == "strong_agreement")
                    if agreements > 0:
                        formatted_response += f" ({agreements} with strong agreement)"
                
                # Add provenance summary and make sources clickable
                provenance = visualization_data.get("provenance", {})
                if provenance:
                    provenance_summary = create_provenance_summary(provenance)
                    formatted_response += f"\n\n{provenance_summary}"
                    
                    # Add query refinement suggestions
                    refinement_panel = create_query_refinement_panel(provenance, user_message)
                    if refinement_panel:
                        formatted_response += f"\n\n{refinement_panel}"
                    
                    # Process response text to make source references clickable
                    # Parse the "Sources:" section and replace with clickable links
                    if "**Sources:**" in formatted_response:
                        # Split on Sources section
                        parts = formatted_response.split("**Sources:**", 1)
                        if len(parts) == 2:
                            main_text = parts[0]
                            sources_section = parts[1]
                            
                            # Process each claim in sources section
                            lines = sources_section.split("\n")
                            clickable_sources = []
                            
                            for line in lines:
                                if line.strip().startswith("- "):
                                    # Extract claim text (remove "- " prefix)
                                    claim_text = line.strip()[2:]
                                    # Remove existing source citation if present
                                    if " [Sources:" in claim_text:
                                        claim_text = claim_text.split(" [Sources:")[0]
                                    
                                    # Find matching provenance info
                                    matched = False
                                    for prov_claim, prov_info in provenance.items():
                                        # Check if this line matches the claim (fuzzy match)
                                        if claim_text[:50] in prov_claim or prov_claim[:50] in claim_text:
                                            # Format as clickable
                                            clickable_text, tooltip = format_clickable_source(
                                                claim_text,
                                                prov_info
                                            )
                                            clickable_sources.append(clickable_text)
                                            if tooltip:
                                                tooltip_data_map[claim_text[:50]] = tooltip
                                            matched = True
                                            break
                                    
                                    if not matched:
                                        # No match found, keep original
                                        clickable_sources.append(line)
                                elif line.strip():
                                    clickable_sources.append(line)
                            
                            # Reconstruct with clickable sources
                            formatted_response = main_text + "**Sources:**\n" + "\n".join(clickable_sources)
            
            messages.value[thinking_id] = {
                "role": "assistant",
                "content": formatted_response,
                "thinking": False,
                "quality_score": quality_score,
                "research_conducted": response.get("research_conducted", False),
                "schema_used": response.get("schema_used"),
                "response_tiers": response_tiers,  # Store tiers for expansion
                "full_response": response.get("response", ""),  # Store full response
                "expanded": False,  # Track expansion state
                "visualization_data": visualization_data,
                "tooltip_data": tooltip_data_map,  # Store tooltip data for interactive display
                "exploration_mode": exploration_mode.value,
                "timestamp": asyncio.get_event_loop().time(),
            }
            
        except Exception as e:
            messages.value[thinking_id] = {
                "role": "assistant",
                "content": f"Error: {str(e)}",
                "error": True,
                "timestamp": asyncio.get_event_loop().time(),
            }
    
    send_button = ui.button(
        label="Send",
        on_click=send_message,
        variant="primary",
        full_width=True,
    )
    
    # Chat display
    chat_display = ui.markdown("")
    
    def update_chat_display():
        """Update chat display with messages."""
        if not messages.value:
            chat_display.value = "**Welcome to BOP**\n\nAsk me anything about knowledge structures, reasoning, or research."
            return
        
        chat_html = []
        for msg in messages.value:
            if msg["role"] == "user":
                chat_html.append(f"### You\n{msg['content']}\n")
            else:
                if msg.get("thinking"):
                    chat_html.append(f"### BOP\n*Thinking...*\n")
                elif msg.get("error"):
                    chat_html.append(f"### BOP\n❌ {msg['content']}\n")
                else:
                    # Progressive disclosure: use response_tiers if available
                    response_tiers = msg.get("response_tiers", {})
                    if response_tiers and not msg.get("expanded", False):
                        # Show summary first
                        content = response_tiers.get("summary", msg.get("content", ""))
                    elif response_tiers and msg.get("expanded", False):
                        # Show detailed when expanded
                        content = response_tiers.get("detailed", response_tiers.get("summary", msg.get("content", "")))
                    else:
                        # Fallback to stored content
                        content = msg.get("content", "")
                    
                    metadata = []
                    if msg.get("research_conducted"):
                        metadata.append("🔍 Research")
                    if msg.get("schema_used"):
                        metadata.append(f"📋 {msg['schema_used']}")
                    if msg.get("quality_score"):
                        metadata.append(f"⭐ {msg['quality_score']:.2f}")
                    
                    if metadata:
                        content += f"\n\n*{' • '.join(metadata)}*"
                    
                    # Add expansion hint if tiers available and not expanded
                    if response_tiers and not msg.get("expanded", False):
                        content += "\n\n*[Click to expand for full details](#expand-response)*"
                    
                    # Add provenance heatmap if available
                    viz_data = msg.get("visualization_data", {})
                    provenance = viz_data.get("provenance", {})
                    # Check if visualizations were enabled when message was created
                    if provenance and viz_data:
                        try:
                            # Convert Rich Table to HTML for display
                            # Note: This is a simplified version - full Rich rendering would require more work
                            provenance_heatmap = create_provenance_heatmap(provenance, max_claims=5)
                            # For now, add a note that heatmap is available
                            # In a full implementation, we'd render the Rich table as HTML
                            content += "\n\n**📊 Token-Level Provenance Heatmap:**\n"
                            content += "*[Interactive heatmap showing query-document token matches]*\n"
                            
                            # Add summary of top token matches
                            claim_count = len(provenance)
                            content += f"- {claim_count} claims with provenance data\n"
                            
                            # Show top 3 claims with their sources
                            sorted_claims = sorted(
                                provenance.items(),
                                key=lambda x: x[1].get("num_sources", 0),
                                reverse=True
                            )[:3]
                            
                            for claim_text, prov_info in sorted_claims:
                                sources = prov_info.get("sources", [])
                                if sources:
                                    source_names = list(set(s.get("source", "unknown") for s in sources))[:2]
                                    content += f"- *{claim_text[:60]}...* → Sources: {', '.join(source_names)}\n"
                                    
                                    # Add relevance breakdown for top source
                                    top_source = sources[0]
                                    relevance_breakdown = top_source.get("relevance_breakdown", {})
                                    if relevance_breakdown:
                                        overall_score = relevance_breakdown.get("overall_score", 0.0)
                                        content += f"  *Relevance: {overall_score:.2f}*"
                        except Exception as e:
                            # Gracefully handle heatmap creation errors
                            content += f"\n\n*[Provenance visualization unavailable: {str(e)}]*"
                    
                    chat_html.append(f"### BOP\n{content}\n")
        
        chat_display.value = "\n".join(chat_html)
    
    # Update display when messages change
    messages.on_change(update_chat_display)
    
    # Layout
    return ui.column([
        ui.markdown("# 🧠 BOP: Knowledge Structure Research Agent"),
        ui.markdown("Chat with an AI agent specialized in knowledge structures, reasoning, and deep research."),
        ui.divider(),
        chat_display,
        ui.divider(),
        ui.row([
            research_toggle,
            show_visualizations,
            exploration_mode,
        ], gap=2),
        ui.row([
            schema_select,
        ]),
        ui.row([
            input_text,
            send_button,
        ]),
    ], gap=2)


# ============================================================================
# Marimo App
# ============================================================================

app = marimo.App(width="full")


@app.cell
def __():
    import marimo
    return marimo,


@app.cell
def chat_interface():
    """Main chat interface."""
    from .web import create_chat_interface
    return create_chat_interface()


@app.cell
def render():
    """Render the chat interface."""
    chat = create_chat_interface()
    return chat,


if __name__ == "__main__":
    marimo.run(__file__)

