//! Orchestrator - structured multi-agent coordination
//!
//! Manages multiple agents working together on complex tasks.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

use crate::agent::Agent;
use crate::Result;

/// Task status in the orchestration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskStatus {
    Pending,
    InProgress,
    Completed,
    Failed { reason: String },
}

/// A task assigned to an agent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: Uuid,
    pub description: String,
    pub status: TaskStatus,
    pub assigned_to: Option<Uuid>,
    pub result: Option<String>,
}

impl Task {
    pub fn new(description: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4(),
            description: description.into(),
            status: TaskStatus::Pending,
            assigned_to: None,
            result: None,
        }
    }
}

/// Orchestrator manages multiple agents and tasks
pub struct Orchestrator {
    agents: HashMap<Uuid, Agent>,
    tasks: Vec<Task>,
}

impl Orchestrator {
    pub fn new() -> Self {
        Self {
            agents: HashMap::new(),
            tasks: Vec::new(),
        }
    }

    /// Register an agent
    pub fn register_agent(&mut self, agent: Agent) -> Uuid {
        let id = agent.id();
        self.agents.insert(id, agent);
        id
    }

    /// Add a task to the queue
    pub fn add_task(&mut self, task: Task) -> Uuid {
        let id = task.id;
        self.tasks.push(task);
        id
    }

    /// Execute all pending tasks
    pub async fn execute(&mut self) -> Result<Vec<Task>> {
        let mut results = Vec::new();

        for task in &mut self.tasks {
            if !matches!(task.status, TaskStatus::Pending) {
                continue;
            }

            // Find an available agent
            if let Some((_id, agent)) = self.agents.iter_mut().next() {
                task.status = TaskStatus::InProgress;
                task.assigned_to = Some(agent.id());

                match agent.query(&task.description).await {
                    Ok(response) => {
                        task.result = Some(response);
                        task.status = TaskStatus::Completed;
                    }
                    Err(e) => {
                        task.status = TaskStatus::Failed {
                            reason: e.to_string(),
                        };
                    }
                }
            }

            results.push(task.clone());
        }

        Ok(results)
    }

    /// Get all tasks
    pub fn tasks(&self) -> &[Task] {
        &self.tasks
    }
}

impl Default for Orchestrator {
    fn default() -> Self {
        Self::new()
    }
}
