use assert_cmd::prelude::*;
use predicates::prelude::*;
use std::process::Command;

#[test]
fn bop_completions_works() {
    let mut cmd = Command::new(assert_cmd::cargo::cargo_bin!("bop-agent"));
    cmd.args(["completions", "bash"]);
    cmd.assert()
        .success()
        // Completions are for the *user-facing command name*, which is `bop`
        // even though the dev binary is currently named `bop-agent`.
        .stdout(predicate::str::contains("cmd=\"bop\""));
}

#[test]
fn bop_session_list_json_is_versioned() {
    let tmp = tempfile::tempdir().unwrap();
    // Keep this test hermetic: store session data in a temp XDG dir.
    let mut cmd = Command::new(assert_cmd::cargo::cargo_bin!("bop-agent"));
    cmd.env("XDG_DATA_HOME", tmp.path());
    cmd.args(["--json", "session", "list"]);
    cmd.assert()
        .success()
        .stdout(predicate::str::contains("\"schema_version\": 1"))
        .stdout(predicate::str::contains("\"ok\": true"));
}

