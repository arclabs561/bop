//! BOP platform entrypoint (A3+).
//!
//! For now, this is a compatibility wrapper:
//! it forwards all arguments to `bop-agent` if present.
//!
//! This reserves the *binary* name `bop` for the long-term “platform/supervisor” intent,
//! while keeping existing CLI workflows working during the transition.

use anyhow::Result;
use std::process::Command;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();

    // Compatibility path: forward to `bop-agent`.
    // (We intentionally do not try to be clever here; future `bop` subcommands can
    // be introduced behind an explicit prefix such as `bop platform ...`.)
    let status = Command::new("bop-agent").args(&args).status();

    match status {
        Ok(s) => std::process::exit(s.code().unwrap_or(1)),
        Err(_) => {
            eprintln!("bop: could not execute `bop-agent` (is it installed and on PATH?)");
            eprintln!("hint: run `cargo install --path bop-cli` (it installs the `bop-agent` binary now)");
            std::process::exit(127)
        }
    }
}

