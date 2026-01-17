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

    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),

    #[error("Session not found: {0}")]
    SessionNotFound(uuid::Uuid),

    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    #[error("Invalid state: {0}")]
    InvalidState(String),
}

impl From<redb::DatabaseError> for Error {
    fn from(e: redb::DatabaseError) -> Self {
        Self::Storage(e.to_string())
    }
}

impl From<redb::TableError> for Error {
    fn from(e: redb::TableError) -> Self {
        Self::Storage(e.to_string())
    }
}

impl From<redb::TransactionError> for Error {
    fn from(e: redb::TransactionError) -> Self {
        Self::Storage(e.to_string())
    }
}

impl From<redb::StorageError> for Error {
    fn from(e: redb::StorageError) -> Self {
        Self::Storage(e.to_string())
    }
}

impl From<redb::CommitError> for Error {
    fn from(e: redb::CommitError) -> Self {
        Self::Storage(e.to_string())
    }
}

pub type Result<T> = std::result::Result<T, Error>;
