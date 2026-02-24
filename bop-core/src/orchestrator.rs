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
    db: Option<hiqlite::Client>,
}

impl Orchestrator {
    pub fn new() -> Self {
        Self {
            agents: HashMap::new(),
            tasks: Vec::new(),
            db: None,
        }
    }

    /// Create a new distributed orchestrator
    pub async fn with_db(db: hiqlite::Client) -> Result<Self> {
        // Initialize schema
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, description TEXT NOT NULL, status TEXT NOT NULL, assigned_to TEXT, result TEXT);", vec![]).await?;

        Ok(Self {
            agents: HashMap::new(),
            tasks: Vec::new(),
            db: Some(db),
        })
    }

    /// Register an agent
    pub fn register_agent(&mut self, agent: Agent) -> Uuid {
        let id = agent.id();
        self.agents.insert(id, agent);
        id
    }

    /// Add a task to the queue
    pub async fn add_task(&mut self, task: Task) -> Result<Uuid> {
        let id = task.id;

        if let Some(db) = &self.db {
            let status_str = serde_json::to_string(&task.status)?;
            db.execute(
                "INSERT INTO tasks (id, description, status, assigned_to, result) VALUES ($1, $2, $3, $4, $5)",
                vec![
                    id.to_string().into(),
                    task.description.into(),
                    status_str.into(),
                    task.assigned_to.map(|u| u.to_string()).into(),
                    task.result.into(),
                ]
            ).await?;
        } else {
            self.tasks.push(task);
        }

        Ok(id)
    }

    /// Execute all pending tasks
    pub async fn execute(&mut self) -> Result<Vec<Task>> {
        let mut results = Vec::new();

        // If distributed, sync tasks from DB first
        if let Some(db) = &self.db {
            // This is a naive implementation; in a real distributed system,
            // we'd use hiqlite's dlock to claim tasks.
            let rows: Vec<TaskRow> = db.query_as("SELECT id, description, status, assigned_to, result FROM tasks WHERE status = '\"Pending\"'", vec![]).await?;
            for row in rows {
                let task_id = Uuid::parse_str(&row.id)?;
                let status: TaskStatus = serde_json::from_str(&row.status)?;
                let assigned_to = match row.assigned_to {
                    Some(s) => Some(Uuid::parse_str(&s)?),
                    None => None,
                };

                self.tasks.push(Task {
                    id: task_id,
                    description: row.description,
                    status,
                    assigned_to,
                    result: row.result,
                });
            }
        }

        for task in &mut self.tasks {
            if !matches!(task.status, TaskStatus::Pending) {
                continue;
            }

            // Find an available agent
            if let Some((_id, agent)) = self.agents.iter_mut().next() {
                // Try to claim the task (optimistic locking)
                if let Some(db) = &self.db {
                    let status_str = serde_json::to_string(&TaskStatus::InProgress)?;
                    let pending_str = serde_json::to_string(&TaskStatus::Pending)?;

                    let rows_affected = db.execute(
                        "UPDATE tasks SET status = $1, assigned_to = $2 WHERE id = $3 AND status = $4",
                        vec![
                            status_str.into(),
                            Some(agent.id().to_string()).into(),
                            task.id.to_string().into(),
                            pending_str.into()
                        ]
                    ).await?;

                    if rows_affected == 0 {
                        // Task was claimed by another node between read and write
                        continue;
                    }
                }

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

                // Update DB with result
                if let Some(db) = &self.db {
                    let status_str = serde_json::to_string(&task.status)?;
                    db.execute(
                        "UPDATE tasks SET status = $1, result = $2 WHERE id = $3",
                        vec![
                            status_str.into(),
                            task.result.clone().into(),
                            task.id.to_string().into(),
                        ],
                    )
                    .await?;
                }
            }

            results.push(task.clone());
        }

        Ok(results)
    }

    /// Get all tasks
    pub async fn tasks(&self) -> Result<Vec<Task>> {
        if let Some(db) = &self.db {
            let rows: Vec<TaskRow> = db
                .query_as(
                    "SELECT id, description, status, assigned_to, result FROM tasks",
                    vec![],
                )
                .await?;
            let mut tasks = Vec::new();
            for row in rows {
                let status: TaskStatus = serde_json::from_str(&row.status)?;
                let assigned_to = match row.assigned_to {
                    Some(s) => Some(Uuid::parse_str(&s)?),
                    None => None,
                };
                tasks.push(Task {
                    id: Uuid::parse_str(&row.id)?,
                    description: row.description,
                    status,
                    assigned_to,
                    result: row.result,
                });
            }
            Ok(tasks)
        } else {
            Ok(self.tasks.clone())
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct TaskRow {
    id: String,
    description: String,
    status: String,
    assigned_to: Option<String>,
    result: Option<String>,
}

impl Default for Orchestrator {
    fn default() -> Self {
        Self::new()
    }
}
