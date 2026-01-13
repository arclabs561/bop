//! Storage utilities - knowledge base, embeddings, etc.
//!
//! Provides a simple knowledge store backed by sled.
//! For full hybrid search capabilities, use hop-core directly.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::Result;

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

/// Knowledge store backed by sled
///
/// For production use with hybrid search, consider using hop-core's
/// UnifiedSearcher or SqliteDocumentStore directly.
pub struct KnowledgeStore {
    db: sled::Db,
}

impl KnowledgeStore {
    /// Open or create a knowledge store
    pub fn open(path: impl AsRef<std::path::Path>) -> Result<Self> {
        let db = sled::open(&path)?;
        Ok(Self { db })
    }

    /// Store a knowledge item
    pub fn store(&self, item: &KnowledgeItem) -> Result<()> {
        let key = item.id.as_bytes();
        let value = serde_json::to_vec(item)?;
        self.db.insert(key, value)?;
        Ok(())
    }

    /// Retrieve a knowledge item by ID
    pub fn get(&self, id: Uuid) -> Result<Option<KnowledgeItem>> {
        let key = id.as_bytes();
        match self.db.get(key)? {
            Some(value) => {
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

        for entry in self.db.iter() {
            let (_, value) = entry?;
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
        self.db.remove(key)?;
        Ok(())
    }

    /// List all items (paginated)
    pub fn list(&self, offset: usize, limit: usize) -> Result<Vec<KnowledgeItem>> {
        let mut items = Vec::new();
        for (i, entry) in self.db.iter().enumerate() {
            if i < offset {
                continue;
            }
            if items.len() >= limit {
                break;
            }
            let (_, value) = entry?;
            let item: KnowledgeItem = serde_json::from_slice(&value)?;
            items.push(item);
        }
        Ok(items)
    }

    /// Count total items
    pub fn len(&self) -> usize {
        self.db.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.db.is_empty()
    }

    /// Flush to disk
    pub fn flush(&self) -> Result<()> {
        self.db.flush()?;
        Ok(())
    }
}
