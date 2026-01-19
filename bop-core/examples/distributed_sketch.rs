// Example of Distributed Coordination using hiqlite
use bop_agent_core::orchestrator::{Orchestrator, Task};
use bop_agent_core::storage::ClusterRegistry;
use uuid::Uuid;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    println!("--- Tekne Distributed Coordination Sketch ---");

    // Check for HQL_NODES environment variable to decide if we run the full sketch
    if std::env::var("HQL_NODES").is_err() {
        println!("HQL_NODES not set. Skipping distributed connection.");
        println!("Run with: HQL_NODES='1 localhost:8100 localhost:8200' cargo run --example distributed_sketch");
        
        println!("Distributed coordination logic implemented in:");
        println!(" - bop-agent-core (path: bop-core/) /src/orchestrator.rs (Task Queue)");
        println!(" - bop-agent-core (path: bop-core/) /src/storage.rs (Node Heartbeats)");
        println!(" - jin/src/persistence/locking.rs (Distributed Locks)");
        
        return Ok(());
    }

    // Initialize hiqlite
    //
    // hiqlite v0.12.x does not expose `Client::new()`; it exposes `start_node(...)`.
    // `NodeConfig::from_env()` reads the HQL_* env vars (including HQL_NODES).
    let cfg = hiqlite::NodeConfig::from_env();
    let db = hiqlite::start_node(cfg).await?;

    // Test Cluster Registry (Heartbeat)
    let registry = ClusterRegistry::new(db.clone()).await?;
    let node_id = Uuid::new_v4();
    println!("Registering node: {}", node_id);
    registry.heartbeat(node_id).await?;
    
    let active = registry.active_nodes().await?;
    println!("Active nodes: {:?}", active);

    // Test Distributed Orchestrator
    let mut orchestrator = Orchestrator::with_db(db.clone()).await?;
    let task = Task::new("Research the impact of distributed consensus on RAG performance");
    let task_id = orchestrator.add_task(task).await?;
    println!("Added distributed task: {}", task_id);

    let tasks = orchestrator.tasks().await?;
    println!("Total tasks in registry: {}", tasks.len());

    println!("--- Sketch Completed Successfully ---");
    Ok(())
}
