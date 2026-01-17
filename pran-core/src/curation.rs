//! Curation - knowledge hygiene and consolidation
//!
//! Based on multi-agent research:
//! - Memory is critical for low-density agent coordination (ρ < 0.20)
//! - Individual memory provides 68.7% improvement over baselines
//! - Curation consolidates, cleans, and resolves conflicts in shared memory

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc, Duration};
use anyhow::Result;
use std::collections::HashMap;

use crate::storage::{KnowledgeStore, KnowledgeItem};
use hop_core::deduplication::{DuplicateDetector, SemanticDuplicateDetector};

/// Curation statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CurationStats {
    pub checked: usize,
    pub stale_removed: usize,
    pub consolidated: usize,
    pub conflicts_detected: usize,
    pub timestamp: DateTime<Utc>,
}

pub struct CurationAgent {
    store: KnowledgeStore,
    detector: Option<SemanticDuplicateDetector>,
    stale_days: i64,
}

impl CurationAgent {
    pub fn new(store: KnowledgeStore) -> Self {
        let detector = SemanticDuplicateDetector::new().ok();
        Self {
            store,
            detector,
            stale_days: 30,
        }
    }

    pub fn with_stale_days(mut self, days: i64) -> Self {
        self.stale_days = days;
        self
    }

    /// Run a curation cycle
    pub async fn curate(&self) -> Result<CurationStats> {
        let mut stats = CurationStats {
            checked: 0,
            stale_removed: 0,
            consolidated: 0,
            conflicts_detected: 0,
            timestamp: Utc::now(),
        };

        let items = self.store.list(0, 1000)?;
        stats.checked = items.len();

        let cutoff = Utc::now() - Duration::days(self.stale_days);

        for item in &items {
            // 1. Clean stale facts
            if let Some(ts_val) = item.metadata.get("timestamp") {
                if let Some(ts_str) = ts_val.as_str() {
                    if let Ok(ts) = DateTime::parse_from_rfc3339(ts_str) {
                        if ts.with_timezone(&Utc) < cutoff {
                            self.store.delete(item.id)?;
                            stats.stale_removed += 1;
                            continue;
                        }
                    }
                }
            }

            // 2. Consolidate similar facts
            if let Some(ref detector) = self.detector {
                // This is a naive O(N^2) or O(N*K) implementation for now
                // In a real system, we'd use vector search to find candidates
                let candidates: Vec<(hop_core::types::DocumentId, String)> = items.iter()
                    .filter(|i| i.id != item.id)
                    .map(|i| (hop_core::types::DocumentId::new(i.id.to_string()), i.content.clone()))
                    .collect();

                let threshold = 0.85; // High similarity for consolidation
                let duplicates = detector.find_duplicates(&item.content, &candidates, threshold)?;

                for (dup_id, result) in duplicates {
                    if result.is_duplicate {
                        // Consolidate: for now just remove the duplicate
                        // Real logic might merge metadata or reinforcement counts
                        if let Ok(uuid) = Uuid::parse_str(&dup_id.to_string()) {
                            self.store.delete(uuid)?;
                            stats.consolidated += 1;
                        }
                    }
                }
            }
        }

        Ok(stats)
    }
}
