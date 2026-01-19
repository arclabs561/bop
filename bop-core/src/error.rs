//! Error types for BOP core

use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("LLM error: {0}")]
    Llm(String),

    #[error("MCP error: {0}")]
    Mcp(String),

    #[error("Storage error: {0}")]
    Storage(String),

    #[error("Distributed error: {0}")]
    Distributed(#[from] hiqlite::Error),

    #[error("UUID error: {0}")]
    Uuid(#[from] uuid::Error),

    #[error("Chrono parse error: {0}")]
    Chrono(#[from] chrono::ParseError),

    #[error("Anyhow error: {0}")]
    Anyhow(#[from] anyhow::Error),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Session not found: {0}")]
    SessionNotFound(uuid::Uuid),

    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    #[error("Agent error: {0}")]
    Agent(#[from] axi::Error),

    #[error("Invalid state: {0}")]
    InvalidState(String),
}
pub type Result<T> = std::result::Result<T, Error>;
