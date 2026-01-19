//! LLM provider abstraction (deprecated wrapper).
//!
//! This module stays in `bop-agent-core` for backwards compatibility, but the
//! provider glue lives in `riff-llm-client`.

pub use riff_agent_core::{Message, Role};
pub use riff_llm_client::LlmProvider;

use crate::{Error, Result};

/// LLM client for making completions.
#[deprecated(note = "Use axi::adapters instead")]
pub struct LlmClient(riff_llm_client::LlmClient);

#[allow(deprecated)]
impl LlmClient {
    pub fn new(provider: LlmProvider) -> Self {
        Self(riff_llm_client::LlmClient::new(provider))
    }

    pub fn provider(&self) -> &LlmProvider {
        self.0.provider()
    }

    pub async fn complete(&self, messages: &[Message]) -> Result<String> {
        self.0
            .complete(messages)
            .await
            .map_err(|e| Error::Llm(e.to_string()))
    }
}
