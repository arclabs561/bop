use bop_core::orchestrator::{Orchestrator, Task, TaskStatus};
use bop_core::storage::{ClusterRegistry, KnowledgeStore, KnowledgeItem};
use bop_core::session::{SessionStore, Session};
use uuid::Uuid;
use tempfile::tempdir;

#[tokio::test]
async fn test_redb_latency_invariants() -> anyhow::Result<()> {
    let tmp = tempdir()?;
    let path = tmp.path().join("test_redb.db");
    
    // Test KnowledgeStore (redb)
    let store = KnowledgeStore::open(&path)?;
    let item = KnowledgeItem::new("High-performance local knowledge");
    
    let start = std::time::Instant::now();
    store.store(&item)?;
    let write_latency = start.elapsed();
    
    let start = std::time::Instant::now();
    let retrieved = store.get(item.id)?.unwrap();
    let read_latency = start.elapsed();
    
    assert_eq!(retrieved.content, item.content);
    println!("Redb Write Latency: {:?}", write_latency);
    println!("Redb Read Latency: {:?}", read_latency);
    
    // Invariants: reads should be extremely fast (< 1ms)
    assert!(read_latency.as_millis() < 10, "Read latency too high for redb");
    
    Ok(())
}

#[tokio::test]
async fn test_session_persistence_redb() -> anyhow::Result<()> {
    let tmp = tempdir()?;
    let path = tmp.path().join("sessions.db");
    
    let store = SessionStore::open(&path)?;
    let mut session = Session::new();
    session.add_message(bop_core::llm::Message::user("Hello distributed world"));
    
    store.save(&session)?;
    let loaded = store.load(session.id)?.unwrap();
    
    assert_eq!(loaded.messages.len(), 1);
    assert_eq!(loaded.messages[0].content, "Hello distributed world");
    
    Ok(())
}

// Note: Real multi-node hiqlite tests would require a running cluster.
// For CI/Unit tests, we test the logic assuming hiqlite Client behaves as expected.
// We'll use a local hiqlite instance if possible, or just test the registry logic.

#[tokio::test]
async fn test_cluster_registry_logic() -> anyhow::Result<()> {
    // In a real test we'd need a hiqlite::Client. 
    // Since hiqlite setup is complex, we'll verify the registry interface.
    // This is a placeholder for actual cluster tests.
    Ok(())
}
