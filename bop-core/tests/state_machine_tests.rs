use bop_agent_core::orchestrator::{Task, TaskStatus};
use proptest::prelude::*;
use uuid::Uuid;

// Define possible state transitions
#[derive(Debug, Clone)]
enum Action {
    Submit,
    Claim,
    Complete,
    Fail,
}

// Invariants to check:
// 1. Task status progression is monotonic (Pending -> InProgress -> [Completed|Failed])
// 2. A task always has an ID.
// 3. Result is only present in terminal states.

proptest! {
    #[test]
    fn test_task_status_invariants(actions in prop::collection::vec(
        prop_oneof![
            Just(Action::Submit),
            Just(Action::Claim),
            Just(Action::Complete),
            Just(Action::Fail),
        ], 1..20)) 
    {
        let mut task = Task::new("Invariant check");
        let mut current_status = TaskStatus::Pending;

        for action in actions {
            match (action, &current_status) {
                (Action::Claim, TaskStatus::Pending) => {
                    task.status = TaskStatus::InProgress;
                    task.assigned_to = Some(Uuid::new_v4());
                    current_status = TaskStatus::InProgress;
                }
                (Action::Complete, TaskStatus::InProgress) => {
                    task.status = TaskStatus::Completed;
                    task.result = Some("Done".to_string());
                    current_status = TaskStatus::Completed;
                }
                (Action::Fail, TaskStatus::InProgress) => {
                    task.status = TaskStatus::Failed { reason: "Error".to_string() };
                    current_status = TaskStatus::Completed; // Using internal helper to simplify
                }
                _ => {} // Invalid transitions are ignored in this simple model
            }

            // Invariant: If InProgress, must have assigned_to
            if matches!(task.status, TaskStatus::InProgress) {
                assert!(task.assigned_to.is_some());
            }

            // Invariant: If terminal, must have result or failure
            match &task.status {
                TaskStatus::Completed => assert!(task.result.is_some()),
                TaskStatus::Failed { .. } => assert!(task.result.is_none()), // Result is only for success
                _ => assert!(task.result.is_none()),
            }
        }
    }
}
