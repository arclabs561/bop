//! Session management - persistence and replay

use chrono::{DateTime, Utc};
use redb::{Database, TableDefinition, ReadableTable};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::llm::Message;
use crate::Result;

const SESSIONS_TABLE: TableDefinition<&[u8; 16], Vec<u8>> = TableDefinition::new("sessions");

/// A conversation session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: Uuid,
    pub messages: Vec<Message>,
    pub created_at: DateTime<Utc>,
}

impl Session {
    /// Create a new empty session
    pub fn new() -> Self {
        Self {
            id: Uuid::new_v4(),
            messages: Vec::new(),
            created_at: Utc::now(),
        }
    }

    /// Add a message to the session
    pub fn add_message(&mut self, message: Message) {
        self.messages.push(message);
    }

    /// Get the number of messages
    pub fn len(&self) -> usize {
        self.messages.len()
    }

    /// Check if the session is empty
    pub fn is_empty(&self) -> bool {
        self.messages.is_empty()
    }

    /// Export to JSON
    pub fn to_json(&self) -> Result<String> {
        Ok(serde_json::to_string_pretty(self)?)
    }

    /// Import from JSON
    pub fn from_json(json: &str) -> Result<Self> {
        Ok(serde_json::from_str(json)?)
    }
}

impl Default for Session {
    fn default() -> Self {
        Self::new()
    }
}

/// Session store backed by redb
pub struct SessionStore {
    db: Database,
}

impl SessionStore {
    /// Open or create a session store
    pub fn open(path: impl AsRef<std::path::Path>) -> Result<Self> {
        let db = Database::create(path)?;
        // Ensure table exists
        let write_txn = db.begin_write()?;
        {
            let _table = write_txn.open_table(SESSIONS_TABLE)?;
        }
        write_txn.commit()?;
        Ok(Self { db })
    }

    /// Save a session
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

    /// Load a session by ID
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

    /// List all session IDs
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

    /// Delete a session
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
