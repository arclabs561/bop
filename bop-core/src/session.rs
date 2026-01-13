//! Session management - persistence and replay

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::llm::Message;
use crate::Result;

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

/// Session store backed by sled
pub struct SessionStore {
    db: sled::Db,
}

impl SessionStore {
    /// Open or create a session store
    pub fn open(path: impl AsRef<std::path::Path>) -> Result<Self> {
        let db = sled::open(path)?;
        Ok(Self { db })
    }

    /// Save a session
    pub fn save(&self, session: &Session) -> Result<()> {
        let key = session.id.as_bytes();
        let value = serde_json::to_vec(session)?;
        self.db.insert(key, value)?;
        self.db.flush()?;
        Ok(())
    }

    /// Load a session by ID
    pub fn load(&self, id: Uuid) -> Result<Option<Session>> {
        let key = id.as_bytes();
        match self.db.get(key)? {
            Some(value) => {
                let session: Session = serde_json::from_slice(&value)?;
                Ok(Some(session))
            }
            None => Ok(None),
        }
    }

    /// List all session IDs
    pub fn list(&self) -> Result<Vec<Uuid>> {
        let mut ids = Vec::new();
        for result in self.db.iter() {
            let (key, _) = result?;
            if key.len() == 16 {
                let bytes: [u8; 16] = key.as_ref().try_into().unwrap();
                ids.push(Uuid::from_bytes(bytes));
            }
        }
        Ok(ids)
    }

    /// Delete a session
    pub fn delete(&self, id: Uuid) -> Result<()> {
        let key = id.as_bytes();
        self.db.remove(key)?;
        Ok(())
    }
}
