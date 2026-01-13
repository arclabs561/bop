//! Research agent - specialized for literature review and synthesis

use crate::agent::{Agent, AgentConfig};
use crate::llm::LlmProvider;
use crate::Result;

const RESEARCH_SYSTEM_PROMPT: &str = r#"You are a research assistant specialized in:
- Literature review and synthesis
- Finding relevant papers and sources
- Summarizing complex technical content
- Identifying gaps in research
- Connecting ideas across domains

When given a research question:
1. Break it down into sub-questions
2. Identify key concepts and terminology
3. Search for relevant sources
4. Synthesize findings
5. Identify limitations and future directions

Be rigorous, cite sources, and acknowledge uncertainty."#;

/// Research agent with specialized prompting
pub struct ResearchAgent {
    inner: Agent,
}

impl ResearchAgent {
    /// Create a new research agent
    pub fn new(provider: LlmProvider) -> Self {
        let config = AgentConfig {
            system_prompt: RESEARCH_SYSTEM_PROMPT.into(),
            max_turns: 20,
            tool_use_enabled: true,
        };
        Self {
            inner: Agent::with_config(provider, config),
        }
    }

    /// Research a topic
    pub async fn research(&mut self, topic: &str) -> Result<String> {
        let query = format!(
            "Research the following topic and provide a comprehensive summary:\n\n{}",
            topic
        );
        self.inner.query(&query).await
    }

    /// Find related work for a given paper/concept
    pub async fn find_related(&mut self, concept: &str) -> Result<String> {
        let query = format!(
            "Find related work and connections for:\n\n{}\n\nList key papers, concepts, and how they relate.",
            concept
        );
        self.inner.query(&query).await
    }

    /// Synthesize multiple sources
    pub async fn synthesize(&mut self, sources: &[&str]) -> Result<String> {
        let sources_text = sources.join("\n---\n");
        let query = format!(
            "Synthesize the following sources into a coherent summary:\n\n{}",
            sources_text
        );
        self.inner.query(&query).await
    }

    /// Identify gaps in research
    pub async fn identify_gaps(&mut self, area: &str) -> Result<String> {
        let query = format!(
            "Identify research gaps and open questions in:\n\n{}\n\nWhat problems remain unsolved? What directions seem promising?",
            area
        );
        self.inner.query(&query).await
    }

    /// Get the inner agent for direct access
    pub fn inner(&self) -> &Agent {
        &self.inner
    }

    /// Get mutable access to the inner agent
    pub fn inner_mut(&mut self) -> &mut Agent {
        &mut self.inner
    }
}
