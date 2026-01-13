//! Output formatting utilities
//!
//! Provides consistent output formatting across CLI commands.

use std::io::{self, Write};

/// Print to stdout, respecting quiet mode
pub fn print_info(quiet: bool, msg: &str) {
    if !quiet {
        eprintln!("{}", msg);
    }
}

/// Print progress indicator
pub fn print_progress(quiet: bool, msg: &str) {
    if !quiet {
        eprint!("\r{}", msg);
        let _ = io::stderr().flush();
    }
}

/// Clear progress line
pub fn clear_progress(quiet: bool) {
    if !quiet {
        eprint!("\r\x1b[K");
        let _ = io::stderr().flush();
    }
}
