//! Retrieval utilities - search and fusion
//!
//! When compiled with `retrieval` feature, uses ordino-fuse for result fusion.

/// A search result with score
#[derive(Debug, Clone)]
pub struct SearchHit {
    pub id: String,
    pub score: f32,
    pub content: Option<String>,
}

/// Fuse multiple result lists using Reciprocal Rank Fusion
///
/// RRF is robust to score scale differences between systems.
/// With `fusion` feature: uses ordino-fuse
/// Without: simple interleaving
pub fn fuse_results(lists: &[Vec<(String, f32)>], k: usize) -> Vec<(String, f32)> {
    #[cfg(feature = "fusion")]
    {
        use ordino_fuse::rrf_multi;
        let config = ordino_fuse::RrfConfig::default();
        let fused = rrf_multi(lists, config);
        fused.into_iter().take(k).collect()
    }

    #[cfg(not(feature = "fusion"))]
    {
        // Simple round-robin interleave
        let mut seen = std::collections::HashSet::new();
        let mut result = Vec::new();
        let mut indices: Vec<usize> = vec![0; lists.len()];

        while result.len() < k {
            let mut added = false;
            for (list_idx, list) in lists.iter().enumerate() {
                if indices[list_idx] < list.len() {
                    let (id, score) = &list[indices[list_idx]];
                    indices[list_idx] += 1;
                    if seen.insert(id.clone()) {
                        result.push((id.clone(), *score));
                        added = true;
                        if result.len() >= k {
                            break;
                        }
                    }
                }
            }
            if !added {
                break;
            }
        }
        result
    }
}

/// Rerank results by a scoring function
///
/// With `retrieval` feature: could use ordino-rerank for learned reranking
/// Without: uses provided score function
pub fn rerank<F>(results: &[(String, f32)], score_fn: F) -> Vec<(String, f32)>
where
    F: Fn(&str) -> f32,
{
    let mut scored: Vec<_> = results
        .iter()
        .map(|(id, _)| {
            let new_score = score_fn(id);
            (id.clone(), new_score)
        })
        .collect();

    scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    scored
}

/// Search configuration
#[derive(Debug, Clone, Default)]
pub struct SearchConfig {
    /// Number of results to return
    pub top_k: usize,
    /// Enable hybrid search (keyword + semantic)
    pub hybrid: bool,
    /// Weight for semantic results in hybrid mode (0-1)
    pub semantic_weight: f32,
}

impl SearchConfig {
    pub fn new(top_k: usize) -> Self {
        Self {
            top_k,
            hybrid: false,
            semantic_weight: 0.5,
        }
    }

    pub fn hybrid(mut self) -> Self {
        self.hybrid = true;
        self
    }

    pub fn semantic_weight(mut self, w: f32) -> Self {
        self.semantic_weight = w.clamp(0.0, 1.0);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fuse_results() {
        let list1 = vec![
            ("a".to_string(), 1.0),
            ("b".to_string(), 0.8),
            ("c".to_string(), 0.6),
        ];
        let list2 = vec![
            ("b".to_string(), 1.0),
            ("d".to_string(), 0.9),
            ("a".to_string(), 0.7),
        ];

        let fused = fuse_results(&[list1, list2], 4);
        assert!(fused.len() <= 4);
        // "a" and "b" should be ranked high (appear in both lists)
        let ids: Vec<_> = fused.iter().map(|(id, _)| id.as_str()).collect();
        assert!(ids.contains(&"a"));
        assert!(ids.contains(&"b"));
    }

    #[test]
    fn test_rerank() {
        let results = vec![
            ("a".to_string(), 1.0),
            ("b".to_string(), 0.5),
            ("c".to_string(), 0.8),
        ];

        // Rerank by string length (silly example)
        let reranked = rerank(&results, |id| id.len() as f32);
        // All same length, so order might not change
        assert_eq!(reranked.len(), 3);
    }
}
