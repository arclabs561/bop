//! Persistence for `riff-agent-core` types.
//!
//! This crate is intentionally “persistence-only”:
//! - it may depend on databases
//! - it should not depend on HTTP clients, MCP transports, or LLM providers

use redb::{Database, ReadableTable, ReadableTableMetadata, TableDefinition};
use serde::{Deserialize, Serialize};
use thiserror::Error;
use uuid::Uuid;

pub use riff_agent_core::{Message, Role, Session};

#[derive(Error, Debug)]
pub enum StoreError {
    #[error("storage error: {0}")]
    Storage(String),

    #[error("distributed storage error: {0}")]
    Distributed(#[from] hiqlite::Error),

    #[error("chrono parse error: {0}")]
    Chrono(#[from] chrono::ParseError),

    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

impl From<redb::DatabaseError> for StoreError {
    fn from(e: redb::DatabaseError) -> Self {
        Self::Storage(e.to_string())
    }
}
impl From<redb::TableError> for StoreError {
    fn from(e: redb::TableError) -> Self {
        Self::Storage(e.to_string())
    }
}
impl From<redb::TransactionError> for StoreError {
    fn from(e: redb::TransactionError) -> Self {
        Self::Storage(e.to_string())
    }
}
impl From<redb::StorageError> for StoreError {
    fn from(e: redb::StorageError) -> Self {
        Self::Storage(e.to_string())
    }
}
impl From<redb::CommitError> for StoreError {
    fn from(e: redb::CommitError) -> Self {
        Self::Storage(e.to_string())
    }
}

pub type Result<T> = std::result::Result<T, StoreError>;

// -----------------------------------------------------------------------------
// Sessions (redb)
// -----------------------------------------------------------------------------

const SESSIONS_TABLE: TableDefinition<&[u8; 16], Vec<u8>> = TableDefinition::new("sessions");

/// Session store backed by redb.
pub struct SessionStore {
    db: Database,
}

impl SessionStore {
    /// Open or create a session store.
    pub fn open(path: impl AsRef<std::path::Path>) -> Result<Self> {
        let db = Database::create(path)?;
        let write_txn = db.begin_write()?;
        {
            let _table = write_txn.open_table(SESSIONS_TABLE)?;
        }
        write_txn.commit()?;
        Ok(Self { db })
    }

    /// Save a session.
    pub fn save(&self, session: &Session) -> Result<()> {
        let key = session.id.as_bytes();
        let value = serde_json::to_vec(session)?;

        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(SESSIONS_TABLE)?;
            table.insert(key, value)?;
        }
        write_txn.commit()?;
        Ok(())
    }

    /// Load a session by ID.
    pub fn load(&self, id: Uuid) -> Result<Option<Session>> {
        let key = id.as_bytes();
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(SESSIONS_TABLE)?;

        match table.get(key)? {
            Some(access) => {
                let value = access.value();
                let session: Session = serde_json::from_slice(&value)?;
                Ok(Some(session))
            }
            None => Ok(None),
        }
    }

    /// List all session IDs.
    pub fn list(&self) -> Result<Vec<Uuid>> {
        let mut ids = Vec::new();
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(SESSIONS_TABLE)?;

        for result in table.iter()? {
            let (key, _) = result?;
            ids.push(Uuid::from_bytes(*key.value()));
        }
        Ok(ids)
    }

    /// Delete a session.
    pub fn delete(&self, id: Uuid) -> Result<()> {
        let key = id.as_bytes();
        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(SESSIONS_TABLE)?;
            table.remove(key)?;
        }
        write_txn.commit()?;
        Ok(())
    }
}

// -----------------------------------------------------------------------------
// Knowledge store (redb)
// -----------------------------------------------------------------------------

const KNOWLEDGE_TABLE: TableDefinition<&[u8; 16], Vec<u8>> = TableDefinition::new("knowledge");

/// A knowledge item in the store.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeItem {
    pub id: Uuid,
    pub content: String,
    pub source: Option<String>,
    pub embedding: Option<Vec<f32>>,
    pub metadata: serde_json::Value,
}

impl KnowledgeItem {
    pub fn new(content: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4(),
            content: content.into(),
            source: None,
            embedding: None,
            metadata: serde_json::Value::Null,
        }
    }

    pub fn with_source(mut self, source: impl Into<String>) -> Self {
        self.source = Some(source.into());
        self
    }

    pub fn with_embedding(mut self, embedding: Vec<f32>) -> Self {
        self.embedding = Some(embedding);
        self
    }

    pub fn with_metadata(mut self, metadata: serde_json::Value) -> Self {
        self.metadata = metadata;
        self
    }
}

/// Knowledge store backed by redb.
pub struct KnowledgeStore {
    db: Database,
}

impl KnowledgeStore {
    pub fn open(path: impl AsRef<std::path::Path>) -> Result<Self> {
        let db = Database::create(path)?;
        let write_txn = db.begin_write()?;
        {
            let _table = write_txn.open_table(KNOWLEDGE_TABLE)?;
        }
        write_txn.commit()?;
        Ok(Self { db })
    }

    pub fn store(&self, item: &KnowledgeItem) -> Result<()> {
        let key = item.id.as_bytes();
        let value = serde_json::to_vec(item)?;

        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(KNOWLEDGE_TABLE)?;
            table.insert(key, value)?;
        }
        write_txn.commit()?;
        Ok(())
    }

    pub fn get(&self, id: Uuid) -> Result<Option<KnowledgeItem>> {
        let key = id.as_bytes();
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(KNOWLEDGE_TABLE)?;

        match table.get(key)? {
            Some(access) => {
                let value = access.value();
                let item: KnowledgeItem = serde_json::from_slice(&value)?;
                Ok(Some(item))
            }
            None => Ok(None),
        }
    }

    /// Naive substring search (scans all items).
    pub fn search(&self, query: &str, k: usize) -> Result<Vec<KnowledgeItem>> {
        let query_lower = query.to_lowercase();
        let mut results = Vec::new();

        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(KNOWLEDGE_TABLE)?;

        for entry in table.iter()? {
            let (_, value_access) = entry?;
            let item: KnowledgeItem = serde_json::from_slice(&value_access.value())?;
            if item.content.to_lowercase().contains(&query_lower) {
                results.push(item);
                if results.len() >= k {
                    break;
                }
            }
        }

        Ok(results)
    }

    pub fn delete(&self, id: Uuid) -> Result<()> {
        let key = id.as_bytes();
        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(KNOWLEDGE_TABLE)?;
            table.remove(key)?;
        }
        write_txn.commit()?;
        Ok(())
    }

    pub fn list(&self, offset: usize, limit: usize) -> Result<Vec<KnowledgeItem>> {
        let mut items = Vec::new();
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(KNOWLEDGE_TABLE)?;

        for (i, entry) in table.iter()?.enumerate() {
            if i < offset {
                continue;
            }
            if items.len() >= limit {
                break;
            }
            let (_, value_access) = entry?;
            let item: KnowledgeItem = serde_json::from_slice(&value_access.value())?;
            items.push(item);
        }
        Ok(items)
    }

    pub fn len(&self) -> Result<usize> {
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(KNOWLEDGE_TABLE)?;
        Ok(table.len()? as usize)
    }

    pub fn is_empty(&self) -> Result<bool> {
        Ok(self.len()? == 0)
    }
}

// -----------------------------------------------------------------------------
// Distributed registry (hiqlite)
// -----------------------------------------------------------------------------

/// Cluster registry for node heartbeats and session mapping.
pub struct ClusterRegistry {
    db: hiqlite::Client,
}

impl ClusterRegistry {
    pub async fn new(db: hiqlite::Client) -> Result<Self> {
        db.execute(
            "CREATE TABLE IF NOT EXISTS cluster_nodes (id TEXT PRIMARY KEY, last_seen TEXT NOT NULL);",
            vec![],
        )
        .await?;
        db.execute(
            "CREATE TABLE IF NOT EXISTS session_registry (session_id TEXT PRIMARY KEY, node_id TEXT NOT NULL, updated_at TEXT NOT NULL);",
            vec![],
        )
        .await?;

        Ok(Self { db })
    }

    pub async fn heartbeat(&self, node_id: Uuid) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        self.db
            .execute(
                "INSERT INTO cluster_nodes (id, last_seen) VALUES ($1, $2)
             ON CONFLICT(id) DO UPDATE SET last_seen = $2",
                vec![node_id.to_string().into(), now.into()],
            )
            .await?;
        Ok(())
    }

    pub async fn register_session(&self, session_id: Uuid, node_id: Uuid) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        self.db
            .execute(
                "INSERT INTO session_registry (session_id, node_id, updated_at) VALUES ($1, $2, $3)
             ON CONFLICT(session_id) DO UPDATE SET node_id = $2, updated_at = $3",
                vec![
                    session_id.to_string().into(),
                    node_id.to_string().into(),
                    now.into(),
                ],
            )
            .await?;
        Ok(())
    }

    pub async fn find_session_node(&self, session_id: Uuid) -> Result<Option<Uuid>> {
        let rows: Vec<(String,)> = self
            .db
            .query_as(
                "SELECT node_id FROM session_registry WHERE session_id = $1",
                vec![session_id.to_string().into()],
            )
            .await?;

        match rows.first() {
            Some((node_id,)) => Ok(Uuid::parse_str(node_id).ok()),
            None => Ok(None),
        }
    }

    /// List active nodes (seen in last 30 seconds).
    pub async fn active_nodes(&self) -> Result<Vec<Uuid>> {
        let rows: Vec<(String, String)> = self
            .db
            .query_as("SELECT id, last_seen FROM cluster_nodes", vec![])
            .await?;

        let mut active = Vec::new();
        let now = chrono::Utc::now();

        for (id_str, last_seen_str) in rows {
            let last_seen =
                chrono::DateTime::parse_from_rfc3339(&last_seen_str)?.with_timezone(&chrono::Utc);
            if now.signed_duration_since(last_seen).num_seconds() < 30 {
                if let Ok(id) = Uuid::parse_str(&id_str) {
                    active.push(id);
                }
            }
        }

        Ok(active)
    }
}
