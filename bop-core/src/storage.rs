//! Storage utilities - knowledge base, embeddings, etc.
//!
//! Provides a simple knowledge store backed by sled.
//! For full hybrid search capabilities, use hop-core directly.

use redb::{Database, TableDefinition, ReadableTable, ReadableTableMetadata};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::Result;

const KNOWLEDGE_TABLE: TableDefinition<&[u8; 16], Vec<u8>> = TableDefinition::new("knowledge");

/// A knowledge item in the store
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

/// Knowledge store backed by redb
///
/// For production use with hybrid search, consider using hop-core's
/// UnifiedSearcher or SqliteDocumentStore directly.
pub struct KnowledgeStore {
    db: Database,
}

impl KnowledgeStore {
    /// Open or create a knowledge store
    pub fn open(path: impl AsRef<std::path::Path>) -> Result<Self> {
        let db = Database::create(path)?;
        // Ensure table exists
        let write_txn = db.begin_write()?;
        {
            let _table = write_txn.open_table(KNOWLEDGE_TABLE)?;
        }
        write_txn.commit()?;
        Ok(Self { db })
    }

    /// Store a knowledge item
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

    /// Retrieve a knowledge item by ID
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

    /// Search for items by keyword (naive substring match)
    ///
    /// For production search, use hop-core's hybrid search instead.
    pub fn search(&self, query: &str, k: usize) -> Result<Vec<KnowledgeItem>> {
        self.search_naive(query, k)
    }

    /// Naive search - scans all items
    fn search_naive(&self, query: &str, k: usize) -> Result<Vec<KnowledgeItem>> {
        let query_lower = query.to_lowercase();
        let mut results = Vec::new();

        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(KNOWLEDGE_TABLE)?;

        for entry in table.iter()? {
            let (_, value_access) = entry?;
            let value = value_access.value();
            let item: KnowledgeItem = serde_json::from_slice(&value)?;
            if item.content.to_lowercase().contains(&query_lower) {
                results.push(item);
                if results.len() >= k {
                    break;
                }
            }
        }

        Ok(results)
    }

    /// Delete a knowledge item
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

    /// List all items (paginated)
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

    /// Count total items
    pub fn len(&self) -> Result<usize> {
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(KNOWLEDGE_TABLE)?;
        Ok(table.len()? as usize)
    }

    /// Check if empty
    pub fn is_empty(&self) -> Result<bool> {
        Ok(self.len()? == 0)
    }

    /// Flush to disk (no-op for redb as commit does this)
    pub fn flush(&self) -> Result<()> {
        Ok(())
    }
}

/// Cluster registry for node heartbeats and session mapping
pub struct ClusterRegistry {
    db: hiqlite::Client,
}

impl ClusterRegistry {
    /// Create a new cluster registry
    pub async fn new(db: hiqlite::Client) -> Result<Self> {
        db.execute("CREATE TABLE IF NOT EXISTS cluster_nodes (id TEXT PRIMARY KEY, last_seen TEXT NOT NULL);", vec![]).await?;
        db.execute("CREATE TABLE IF NOT EXISTS session_registry (session_id TEXT PRIMARY KEY, node_id TEXT NOT NULL, updated_at TEXT NOT NULL);", vec![]).await?;

        Ok(Self { db })
    }

    /// Register or update node heartbeat
    pub async fn heartbeat(&self, node_id: Uuid) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        self.db.execute(
            "INSERT INTO cluster_nodes (id, last_seen) VALUES ($1, $2)
             ON CONFLICT(id) DO UPDATE SET last_seen = $2",
            vec![node_id.to_string().into(), now.into()]
        ).await?;
        Ok(())
    }

    /// Map a session to a node
    pub async fn register_session(&self, session_id: Uuid, node_id: Uuid) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        self.db.execute(
            "INSERT INTO session_registry (session_id, node_id, updated_at) VALUES ($1, $2, $3)
             ON CONFLICT(session_id) DO UPDATE SET node_id = $2, updated_at = $3",
            vec![session_id.to_string().into(), node_id.to_string().into(), now.into()]
        ).await?;
        Ok(())
    }

    /// Find which node is handling a session
    pub async fn find_session_node(&self, session_id: Uuid) -> Result<Option<Uuid>> {
        let rows: Vec<(String,)> = self.db.query_as(
            "SELECT node_id FROM session_registry WHERE session_id = $1",
            vec![session_id.to_string().into()]
        ).await?;

        if let Some((node_id_str,)) = rows.first() {
            Ok(Some(Uuid::parse_str(node_id_str)?))
        } else {
            Ok(None)
        }
    }

    /// List active nodes (seen in last 30 seconds)
    pub async fn active_nodes(&self) -> Result<Vec<Uuid>> {
        let rows: Vec<(String, String)> = self.db.query_as("SELECT id, last_seen FROM cluster_nodes", vec![]).await?;
        let mut active = Vec::new();
        let now = chrono::Utc::now();

        for (id_str, last_seen_str) in rows {
            let last_seen = chrono::DateTime::parse_from_rfc3339(&last_seen_str)?
                .with_timezone(&chrono::Utc);
            if now.signed_duration_since(last_seen).num_seconds() < 30 {
                active.push(Uuid::parse_str(&id_str)?);
            }
        }
        Ok(active)
    }
}
