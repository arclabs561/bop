//! Explainability helpers (optional).
//!
//! BOP should not depend on heavyweight math by default. These helpers are
//! feature-gated and produce artifacts that are meant to be *shown* to users
//! or logged for debugging.

#[cfg(feature = "token-ot-explain")]
pub mod token_ot;

