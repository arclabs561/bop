//! BOP Core - Agentic research and orchestration
//!
//! This crate provides the core building blocks for research agents:
//! - LLM provider abstraction
//! - MCP client for tool integration
//! - Agent state machines
//! - Research orchestration
//!
//! # Example
//!
//! ```ignore
//! use bop_agent_core::{Agent, LlmProvider};
//!
//! let provider = LlmProvider::anthropic("claude-sonnet-4-20250514");
//! let agent = Agent::new(provider);
//! let response = agent.query("What is the capital of France?").await?;
//! ```

pub mod agent;
pub mod curation;
pub mod error;
pub mod explain;
pub mod llm;
pub mod mcp;
pub mod ops;
pub mod orchestrator;
pub mod research;
pub mod retrieval;
pub mod session;
pub mod stigmergy;
pub mod storage;

pub use agent::Agent;
pub use curation::{CurationAgent, CurationStats};
pub use error::{Error, Result};
pub use llm::LlmProvider;
pub use ops::cost::{CostMonitor, CostStats};
pub use orchestrator::Orchestrator;
pub use research::ResearchAgent;
pub use riff_agent_core::{Message, Role, Session};
pub use riff_agent_store::{
    ClusterRegistry, KnowledgeItem, KnowledgeStore, SessionStore, StoreError,
};
pub use stigmergy::{MarkerType, Stigmergy, StigmergyMarker};
