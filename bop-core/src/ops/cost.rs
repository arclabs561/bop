//! Cost monitoring and analysis
//!
//! Tracks AWS spend patterns and detects anomalies.

use anyhow::Result;
use aws_sdk_costexplorer::Client;
use aws_sdk_costexplorer::types::{DateInterval, Granularity, GroupDefinition, GroupDefinitionType};
use chrono::{Utc, Datelike};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostStats {
    pub total_usd: f64,
    pub top_services: Vec<(String, f64)>,
    pub period_start: String,
    pub period_end: String,
}

pub struct CostMonitor {
    client: Client,
}

impl CostMonitor {
    pub async fn new() -> Result<Self> {
        let config = aws_config::load_defaults(aws_config::BehaviorVersion::latest()).await;
        let client = Client::new(&config);
        Ok(Self { client })
    }

    /// Get month-to-date cost statistics
    pub async fn get_mtd_stats(&self) -> Result<CostStats> {
        let now = Utc::now();
        let start = format!("{}-{:02}-01", now.year(), now.month());
        let end = now.format("%Y-%m-%d").to_string();

        let interval = DateInterval::builder()
            .start(&start)
            .end(&end)
            .build()?;

        let response = self.client
            .get_cost_and_usage()
            .time_period(interval)
            .granularity(Granularity::Monthly)
            .metrics("UnblendedCost")
            .group_by(
                GroupDefinition::builder()
                    .r#type(GroupDefinitionType::Dimension)
                    .key("SERVICE")
                    .build()
            )
            .send()
            .await?;

        let mut total = 0.0;
        let mut services = Vec::new();

        if let Some(results) = response.results_by_time {
            for result in results {
                if let Some(groups) = result.groups {
                    for group in groups {
                        let service_name = group.keys.and_then(|k| k.first().cloned()).unwrap_or_else(|| "Unknown".to_string());
                        let amount = group.metrics
                            .and_then(|m| m.get("UnblendedCost").cloned())
                            .and_then(|v| v.amount)
                            .and_then(|a| a.parse::<f64>().ok())
                            .unwrap_or(0.0);
                        
                        total += amount;
                        services.push((service_name, amount));
                    }
                }
            }
        }

        // Sort by amount descending
        services.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        Ok(CostStats {
            total_usd: total,
            top_services: services.into_iter().take(10).collect(),
            period_start: start,
            period_end: end,
        })
    }
}
