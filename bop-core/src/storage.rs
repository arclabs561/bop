//! Storage utilities.
//!
//! This module is intentionally thin:
//! - persistence lives in `riff-agent-store`
//! - higher-level retrieval belongs in `hop-core`

pub use riff_agent_store::{ClusterRegistry, KnowledgeItem, KnowledgeStore};
