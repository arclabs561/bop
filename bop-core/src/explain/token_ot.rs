//! Token-level OT alignment explanation (feature-gated).
//!
//! This is a thin wrapper over `hop-core`’s token-OT matcher. The goal is not to expose
//! raw matrices, but to return a compact artifact:
//! - top transport edges (token_i → token_j with mass)
//! - most-deleted query tokens (unmatched mass)
//! - summary scalars
//!
//! This is meant to answer: “why did we think these strings match?”

use crate::{Error, Result};

use hop_core::entity::semantic_matching::{token_ot_similarity, TokenOtConfig};
use ndarray::Array2;

/// A compact explanation artifact from token-level OT.
#[derive(Debug, Clone)]
pub struct TokenOtExplanation {
    /// Similarity score in \[0,1] as computed by hop-core.
    pub score: f32,
    /// OT objective value (unbalanced Sinkhorn distance).
    pub dist: f32,
    /// Query tokens used in the OT problem.
    pub query_tokens: Vec<String>,
    /// Candidate tokens used in the OT problem.
    pub candidate_tokens: Vec<String>,
    /// Top transport edges by mass: (i, j, mass).
    pub top_edges: Vec<(usize, usize, f32)>,
    /// Top deleted query tokens: (token, deleted_mass, deleted_rate).
    pub top_deleted_query: Vec<(String, f32, f32)>,
    /// Total deleted mass on the query side (sum_i max(0, wq[i] - row_sum(P[i,:]))).
    pub deleted_query_total: f32,
    /// Total unused mass on the candidate side (sum_j max(0, wd[j] - col_sum(P[:,j]))).
    pub unused_candidate_total: f32,
}

impl TokenOtExplanation {
    /// Compute an explanation artifact.
    ///
    /// `top_k_edges` controls how many edges we keep (largest masses).
    /// `top_k_deleted` controls how many deleted tokens we keep.
    pub fn compute(
        query_text: &str,
        candidate_text: &str,
        cfg: &TokenOtConfig,
        top_k_edges: usize,
        top_k_deleted: usize,
    ) -> Result<Self> {
        let (score, plan, toks_q, toks_d, w_q, w_d) =
            token_ot_similarity(query_text, candidate_text, cfg)
                .map_err(|e| Error::InvalidState(format!("token-ot failed: {e}")))?;

        let (deleted_query_total, top_deleted_query) =
            summarize_deleted_query(&plan, &toks_q, &w_q, top_k_deleted);
        let unused_candidate_total = summarize_unused_candidate(&plan, &w_d);

        let top_edges = top_edges_by_mass(&plan, top_k_edges);

        // Recover dist from score: score = 1/(1+dist) => dist = (1/score) - 1.
        let dist = if score > 0.0 {
            (1.0 / score) - 1.0
        } else {
            f32::INFINITY
        };

        Ok(Self {
            score,
            dist,
            query_tokens: toks_q.to_vec(),
            candidate_tokens: toks_d.to_vec(),
            top_edges,
            top_deleted_query,
            deleted_query_total,
            unused_candidate_total,
        })
    }
}

fn top_edges_by_mass(plan: &Array2<f32>, k: usize) -> Vec<(usize, usize, f32)> {
    if k == 0 {
        return vec![];
    }
    let (m, n) = plan.dim();
    let mut edges: Vec<(usize, usize, f32)> = Vec::with_capacity(m * n);
    for i in 0..m {
        for j in 0..n {
            let mass = plan[[i, j]];
            if mass > 0.0 {
                edges.push((i, j, mass));
            }
        }
    }
    edges.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
    edges.truncate(k);
    edges
}

fn summarize_deleted_query(
    plan: &Array2<f32>,
    toks_q: &[String],
    w_q: &ndarray::Array1<f32>,
    k: usize,
) -> (f32, Vec<(String, f32, f32)>) {
    let m = toks_q.len();
    let mut deleted: Vec<(usize, f32)> = Vec::with_capacity(m);
    let mut total = 0.0f32;
    for i in 0..m {
        let row_sum = plan.row(i).sum();
        let del = (w_q[i] - row_sum).max(0.0);
        total += del;
        deleted.push((i, del));
    }
    deleted.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    deleted.truncate(k);
    let out = deleted
        .into_iter()
        .map(|(i, del)| {
            let w = w_q[i].max(1e-12);
            let rate = (del / w).min(1.0);
            (toks_q[i].clone(), del, rate)
        })
        .collect::<Vec<_>>();
    (total, out)
}

fn summarize_unused_candidate(plan: &Array2<f32>, w_d: &ndarray::Array1<f32>) -> f32 {
    let n = w_d.len();
    let mut total = 0.0f32;
    for j in 0..n {
        let col_sum = plan.column(j).sum();
        total += (w_d[j] - col_sum).max(0.0);
    }
    total
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn token_ot_explanation_deletes_obvious_boilerplate() {
        // This is intentionally close to `wass/examples/document_alignment_demo.rs` and
        // hop-core's `token_ot_entity_matching_e2e.rs`.
        let doc_a = "Breaking: quarterly earnings show steady growth. Subscribe to our newsletter. Cookies policy. Share on Twitter.";
        let doc_b = "Quarterly earnings showed steady growth across sectors.";

        let cfg = TokenOtConfig {
            dim: 128,
            reg: 0.12,
            rho: 0.6,
            boiler_mismatch_penalty: 1.0,
            max_iter: 1200,
            tol: 2e-3,
        };

        let ex = TokenOtExplanation::compute(doc_a, doc_b, &cfg, 10, 8).unwrap();
        assert!(ex.score.is_finite());
        assert!(ex.dist.is_finite());
        // We should have at least one positive-mass edge in most realistic cases
        // (otherwise this isn't a meaningful explanation).
        assert!(!ex.top_edges.is_empty());

        // Minimal falsifiable claim: at least one obvious boilerplate token is mostly deleted.
        let focus = [
            "subscribe",
            "newsletter",
            "cookies",
            "policy",
            "share",
            "twitter",
        ];
        let mut best_rate = 0.0f32;
        let mut best_tok = "(none)";
        for (tok, _del, rate) in &ex.top_deleted_query {
            if focus.contains(&tok.as_str()) && *rate > best_rate {
                best_rate = *rate;
                best_tok = tok.as_str();
            }
        }
        assert!(
            best_rate > 0.60,
            "expected a boilerplate token to be mostly deleted; best={best_tok} rate={best_rate:.3}"
        );
    }
}
