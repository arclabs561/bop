//! Output formatting utilities
//!
//! Provides consistent output formatting across CLI commands.

use std::io::{self, Write};

/// Print to stdout, respecting quiet mode
#[allow(dead_code)] // shared CLI utility; some commands don't currently use it
pub fn print_info(quiet: bool, msg: &str) {
    if !quiet {
        eprintln!("{}", msg);
    }
}

/// Print progress indicator
#[allow(dead_code)] // shared CLI utility; some commands don't currently use it
pub fn print_progress(quiet: bool, msg: &str) {
    if !quiet {
        eprint!("\r{}", msg);
        let _ = io::stderr().flush();
    }
}

/// Clear progress line
#[allow(dead_code)] // shared CLI utility; some commands don't currently use it
pub fn clear_progress(quiet: bool) {
    if !quiet {
        eprint!("\r\x1b[K");
        let _ = io::stderr().flush();
    }
}
