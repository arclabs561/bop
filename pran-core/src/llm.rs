//! LLM provider abstraction
//!
//! Supports multiple backends:
//! - OpenRouter (unified API for many models)
//! - Anthropic (Claude)
//! - OpenAI (GPT)
//! - Local (Ollama, llama.cpp)

use serde::{Deserialize, Serialize};

use crate::{Error, Result};

/// Message role in a conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    System,
    User,
    Assistant,
}

/// A single message in a conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: Role,
    pub content: String,
}

impl Message {
    pub fn system(content: impl Into<String>) -> Self {
        Self {
            role: Role::System,
            content: content.into(),
        }
    }

    pub fn user(content: impl Into<String>) -> Self {
        Self {
            role: Role::User,
            content: content.into(),
        }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            role: Role::Assistant,
            content: content.into(),
        }
    }
}

/// LLM provider configuration
#[derive(Debug, Clone)]
pub enum LlmProvider {
    /// OpenRouter - unified API for many models
    OpenRouter {
        model: String,
        api_key: String,
    },
    Anthropic {
        model: String,
        api_key: String,
    },
    OpenAI {
        model: String,
        api_key: String,
    },
    Local {
        model: String,
        base_url: String,
    },
}

impl LlmProvider {
    /// Create an OpenRouter provider (reads API key from env)
    /// Models: anthropic/claude-3.5-sonnet, openai/gpt-4o, meta-llama/llama-3.1-70b, etc.
    pub fn openrouter(model: impl Into<String>) -> Result<Self> {
        let api_key = std::env::var("OPENROUTER_API_KEY")
            .map_err(|_| Error::Llm(
                "OPENROUTER_API_KEY not set. Run: export OPENROUTER_API_KEY='your-key'\n\
                 Get one at: https://openrouter.ai/keys".into()
            ))?;
        Ok(Self::OpenRouter {
            model: model.into(),
            api_key,
        })
    }

    /// Create an Anthropic provider (reads API key from env)
    pub fn anthropic(model: impl Into<String>) -> Result<Self> {
        let api_key = std::env::var("ANTHROPIC_API_KEY")
            .map_err(|_| Error::Llm(
                "ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY='your-key'".into()
            ))?;
        Ok(Self::Anthropic {
            model: model.into(),
            api_key,
        })
    }

    /// Create an OpenAI provider (reads API key from env)
    pub fn openai(model: impl Into<String>) -> Result<Self> {
        let api_key = std::env::var("OPENAI_API_KEY")
            .map_err(|_| Error::Llm(
                "OPENAI_API_KEY not set. Run: export OPENAI_API_KEY='your-key'".into()
            ))?;
        Ok(Self::OpenAI {
            model: model.into(),
            api_key,
        })
    }

    /// Create a local provider (Ollama, etc.)
    pub fn local(model: impl Into<String>, base_url: impl Into<String>) -> Self {
        Self::Local {
            model: model.into(),
            base_url: base_url.into(),
        }
    }

    /// Auto-detect provider from available env vars
    /// Priority: OPENROUTER > ANTHROPIC > OPENAI
    pub fn auto(model: Option<&str>) -> Result<Self> {
        if std::env::var("OPENROUTER_API_KEY").is_ok() {
            return Self::openrouter(model.unwrap_or("anthropic/claude-sonnet-4"));
        }
        if std::env::var("ANTHROPIC_API_KEY").is_ok() {
            return Self::anthropic(model.unwrap_or("claude-sonnet-4-20250514"));
        }
        if std::env::var("OPENAI_API_KEY").is_ok() {
            return Self::openai(model.unwrap_or("gpt-4o"));
        }
        Err(Error::Llm(
            "No API key found. Set one of: OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY".into()
        ))
    }
}

/// LLM client for making completions
pub struct LlmClient {
    provider: LlmProvider,
    client: reqwest::Client,
}

impl LlmClient {
    pub fn new(provider: LlmProvider) -> Self {
        Self {
            provider,
            client: reqwest::Client::new(),
        }
    }

    pub fn provider(&self) -> &LlmProvider {
        &self.provider
    }

    /// Send a completion request
    pub async fn complete(&self, messages: &[Message]) -> Result<String> {
        match &self.provider {
            LlmProvider::OpenRouter { model, api_key } => {
                self.complete_openrouter(model, api_key, messages).await
            }
            LlmProvider::Anthropic { model, api_key } => {
                self.complete_anthropic(model, api_key, messages).await
            }
            LlmProvider::OpenAI { model, api_key } => {
                self.complete_openai(model, api_key, messages).await
            }
            LlmProvider::Local { model, base_url } => {
                self.complete_local(model, base_url, messages).await
            }
        }
    }

    async fn complete_openrouter(
        &self,
        model: &str,
        api_key: &str,
        messages: &[Message],
    ) -> Result<String> {
        // OpenRouter uses OpenAI-compatible format
        #[derive(Serialize)]
        struct Request<'a> {
            model: &'a str,
            messages: &'a [Message],
        }

        #[derive(Deserialize)]
        struct Response {
            choices: Option<Vec<Choice>>,
            error: Option<ApiError>,
        }

        #[derive(Deserialize)]
        struct Choice {
            message: MessageContent,
        }

        #[derive(Deserialize)]
        struct MessageContent {
            content: String,
        }

        #[derive(Deserialize)]
        struct ApiError {
            message: String,
        }

        let response = self
            .client
            .post("https://openrouter.ai/api/v1/chat/completions")
            .bearer_auth(api_key)
            .header("HTTP-Referer", "https://github.com/scholar-stack/bop")
            .header("X-Title", "bop")
            .json(&Request { model, messages })
            .send()
            .await?;

        let status = response.status();
        let body = response.text().await?;

        if !status.is_success() {
            if let Ok(err_resp) = serde_json::from_str::<serde_json::Value>(&body) {
                if let Some(err) = err_resp.get("error") {
                    let msg = err.get("message").and_then(|m| m.as_str()).unwrap_or("unknown");
                    return Err(Error::Llm(format!("OpenRouter error: {}", msg)));
                }
            }
            return Err(Error::Llm(format!("OpenRouter error ({}): {}", status, body)));
        }

        let resp: Response = serde_json::from_str(&body)
            .map_err(|e| Error::Llm(format!("Failed to parse response: {}", e)))?;

        if let Some(err) = resp.error {
            return Err(Error::Llm(format!("OpenRouter: {}", err.message)));
        }

        resp.choices
            .and_then(|c| c.into_iter().next())
            .map(|c| c.message.content)
            .ok_or_else(|| Error::Llm("No response from OpenRouter".into()))
    }

    async fn complete_anthropic(
        &self,
        model: &str,
        api_key: &str,
        messages: &[Message],
    ) -> Result<String> {
        #[derive(Serialize)]
        struct Request<'a> {
            model: &'a str,
            max_tokens: u32,
            #[serde(skip_serializing_if = "Option::is_none")]
            system: Option<&'a str>,
            messages: Vec<&'a Message>,
        }

        #[derive(Deserialize)]
        struct Response {
            content: Option<Vec<ContentBlock>>,
            error: Option<ApiError>,
        }

        #[derive(Deserialize)]
        struct ContentBlock {
            text: String,
        }

        #[derive(Deserialize)]
        struct ApiError {
            #[serde(rename = "type")]
            error_type: String,
            message: String,
        }

        // Extract system message and filter it out of messages
        let system_msg = messages
            .iter()
            .find(|m| matches!(m.role, Role::System))
            .map(|m| m.content.as_str());

        let filtered_messages: Vec<&Message> = messages
            .iter()
            .filter(|m| !matches!(m.role, Role::System))
            .collect();

        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", api_key)
            .header("anthropic-version", "2023-06-01")
            .json(&Request {
                model,
                max_tokens: 4096,
                system: system_msg,
                messages: filtered_messages,
            })
            .send()
            .await?;

        let status = response.status();
        let body = response.text().await?;

        if !status.is_success() {
            // Try to parse error
            if let Ok(err_resp) = serde_json::from_str::<serde_json::Value>(&body) {
                if let Some(err) = err_resp.get("error") {
                    let msg = err.get("message").and_then(|m| m.as_str()).unwrap_or("unknown");
                    return Err(Error::Llm(format!("Anthropic API error: {}", msg)));
                }
            }
            return Err(Error::Llm(format!("Anthropic API error ({}): {}", status, body)));
        }

        let resp: Response = serde_json::from_str(&body)
            .map_err(|e| Error::Llm(format!("Failed to parse response: {} - body: {}", e, body)))?;

        if let Some(err) = resp.error {
            return Err(Error::Llm(format!("{}: {}", err.error_type, err.message)));
        }

        let content = resp.content.ok_or_else(|| Error::Llm("No content in response".into()))?;

        Ok(content
            .into_iter()
            .map(|c| c.text)
            .collect::<Vec<_>>()
            .join(""))
    }

    async fn complete_openai(
        &self,
        model: &str,
        api_key: &str,
        messages: &[Message],
    ) -> Result<String> {
        #[derive(Serialize)]
        struct Request<'a> {
            model: &'a str,
            messages: &'a [Message],
        }

        #[derive(Deserialize)]
        struct Response {
            choices: Vec<Choice>,
        }

        #[derive(Deserialize)]
        struct Choice {
            message: MessageContent,
        }

        #[derive(Deserialize)]
        struct MessageContent {
            content: String,
        }

        let resp: Response = self
            .client
            .post("https://api.openai.com/v1/chat/completions")
            .bearer_auth(api_key)
            .json(&Request { model, messages })
            .send()
            .await?
            .json()
            .await?;

        resp.choices
            .into_iter()
            .next()
            .map(|c| c.message.content)
            .ok_or_else(|| Error::Llm("No response from OpenAI".into()))
    }

    async fn complete_local(
        &self,
        model: &str,
        base_url: &str,
        messages: &[Message],
    ) -> Result<String> {
        // Ollama-compatible API
        #[derive(Serialize)]
        struct Request<'a> {
            model: &'a str,
            messages: &'a [Message],
            stream: bool,
        }

        #[derive(Deserialize)]
        struct Response {
            message: MessageContent,
        }

        #[derive(Deserialize)]
        struct MessageContent {
            content: String,
        }

        let url = format!("{}/api/chat", base_url.trim_end_matches('/'));
        let resp: Response = self
            .client
            .post(&url)
            .json(&Request {
                model,
                messages,
                stream: false,
            })
            .send()
            .await?
            .json()
            .await?;

        Ok(resp.message.content)
    }
}
