//! Stigmergy - indirect coordination via environmental markers (S3)
//!
//! Based on the "Sober Engineering" model for distributed agent coordination.
//! Agents leave markers in S3 that other agents sense and act upon.

use anyhow::Result;
use aws_sdk_s3::Client;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Marker types for stigmergy coordination
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum MarkerType {
    Signal,
    Issue,
    Resolved,
    Investigating,
    Consensus,
    Error,
}

impl std::fmt::Display for MarkerType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::Signal => "signal",
            Self::Issue => "issue",
            Self::Resolved => "resolved",
            Self::Investigating => "investigating",
            Self::Consensus => "consensus",
            Self::Error => "error",
        };
        write!(f, "{}", s)
    }
}

/// A stigmergy marker stored in S3
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StigmergyMarker {
    pub id: String,
    pub marker_type: MarkerType,
    pub topic: String,
    pub agent_id: String,
    pub intensity: f32,
    pub urgency: String,
    pub ttl_hours: u32,
    pub timestamp: DateTime<Utc>,
    pub metadata: HashMap<String, serde_json::Value>,
}

impl StigmergyMarker {
    pub fn is_expired(&self) -> bool {
        let now = Utc::now();
        let age = now - self.timestamp;
        age.num_hours() >= self.ttl_hours as i64
    }
}

pub struct Stigmergy {
    client: Client,
    bucket: String,
    prefix: String,
}

impl Stigmergy {
    pub async fn new(bucket: String) -> Result<Self> {
        let config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
        let client = Client::new(&config);
        Ok(Self {
            client,
            bucket,
            prefix: "stigmergy/".into(),
        })
    }

    /// List active markers for a topic or type
    pub async fn sense_markers(
        &self,
        topic: Option<&str>,
        marker_type: Option<MarkerType>,
    ) -> Result<Vec<StigmergyMarker>> {
        let prefix = if let Some(ref mt) = marker_type {
            format!("{}{}/", self.prefix, mt)
        } else {
            self.prefix.clone()
        };

        let mut markers = Vec::new();
        let response = self
            .client
            .list_objects_v2()
            .bucket(&self.bucket)
            .prefix(prefix)
            .send()
            .await?;

        if let Some(objects) = response.contents {
            for obj in objects {
                if let Some(key) = obj.key() {
                    if !key.ends_with(".json") {
                        continue;
                    }

                    // Purposeful fetching: skip if recently seen or stale metadata
                    // For now, fetch all active markers
                    let data = self
                        .client
                        .get_object()
                        .bucket(&self.bucket)
                        .key(key)
                        .send()
                        .await?
                        .body
                        .collect()
                        .await?;

                    match serde_json::from_slice::<StigmergyMarker>(&data.into_bytes()) {
                        Ok(marker) => {
                            // Filter by topic if requested
                            if let Some(t) = topic {
                                if marker.topic != t {
                                    continue;
                                }
                            }

                            // Check expiration
                            if !marker.is_expired() {
                                markers.push(marker);
                            }
                        }
                        Err(e) => {
                            tracing::warn!("Skipping corrupted marker {}: {}", key, e);
                        }
                    }
                }
            }
        }

        Ok(markers)
    }

    /// Leave a new marker in the environment
    pub async fn leave_marker(&self, marker: StigmergyMarker) -> Result<()> {
        let key = format!(
            "{}{}/{}_{}.json",
            self.prefix, marker.marker_type, marker.topic, marker.id
        );

        let body = serde_json::to_vec(&marker)?;

        self.client
            .put_object()
            .bucket(&self.bucket)
            .key(key)
            .body(body.into())
            .content_type("application/json")
            .send()
            .await?;

        Ok(())
    }

    /// Delete a marker from the environment
    pub async fn delete_marker(&self, marker: &StigmergyMarker) -> Result<()> {
        let key = format!(
            "{}{}/{}_{}.json",
            self.prefix, marker.marker_type, marker.topic, marker.id
        );

        self.client
            .delete_object()
            .bucket(&self.bucket)
            .key(key)
            .send()
            .await?;

        Ok(())
    }

    /// Reinforce a marker by increasing its intensity
    pub async fn reinforce_marker(
        &self,
        marker: &mut StigmergyMarker,
        agent_id: &str,
        action_taken: bool,
    ) -> Result<()> {
        let reinforcement = if action_taken { 0.2 } else { 0.1 };
        marker.intensity = (marker.intensity + reinforcement).min(1.0);

        // Record who reinforced it in metadata
        let reinforced_by = marker
            .metadata
            .entry("reinforced_by".to_string())
            .or_insert(serde_json::Value::Array(Vec::new()));

        if let Some(arr) = reinforced_by.as_array_mut() {
            let agent_val = serde_json::Value::String(agent_id.to_string());
            if !arr.contains(&agent_val) {
                arr.push(agent_val);
            }
        }

        self.leave_marker(marker.clone()).await
    }
}
