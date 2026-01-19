//! Session management - persistence and replay.
//!
//! This module is intentionally thin:
//! - pure session types live in `riff-agent-core`
//! - persistence lives in `riff-agent-store`

pub use riff_agent_core::Session;
pub use riff_agent_store::SessionStore;
