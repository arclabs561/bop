//! LLM client helpers (provider glue only).
//!
//! This crate is intentionally “impure”:
//! - it depends on HTTP (`reqwest`)
//! - it knows about provider-specific request/response shapes
//!
//! It should *not* contain agent state machines, tool runtimes, or storage.

use riff_agent_core::{Message, Role};
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum LlmError {
    #[error("{var} not set. {hint}")]
    MissingEnv { var: &'static str, hint: &'static str },

    #[error("http error: {0}")]
    Http(#[from] reqwest::Error),

    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("provider error: {0}")]
    Provider(String),
}

pub type Result<T> = std::result::Result<T, LlmError>;

/// LLM provider configuration.
#[derive(Debug, Clone)]
pub enum LlmProvider {
    OpenRouter { model: String, api_key: String },
    Anthropic { model: String, api_key: String },
    OpenAI { model: String, api_key: String },
    Local { model: String, base_url: String },
}

impl LlmProvider {
    pub fn openrouter(model: impl Into<String>) -> Result<Self> {
        let api_key = std::env::var("OPENROUTER_API_KEY").map_err(|_| LlmError::MissingEnv {
            var: "OPENROUTER_API_KEY",
            hint: "Get one at: https://openrouter.ai/keys",
        })?;
        Ok(Self::OpenRouter {
            model: model.into(),
            api_key,
        })
    }

    pub fn anthropic(model: impl Into<String>) -> Result<Self> {
        let api_key = std::env::var("ANTHROPIC_API_KEY").map_err(|_| LlmError::MissingEnv {
            var: "ANTHROPIC_API_KEY",
            hint: "",
        })?;
        Ok(Self::Anthropic {
            model: model.into(),
            api_key,
        })
    }

    pub fn openai(model: impl Into<String>) -> Result<Self> {
        let api_key = std::env::var("OPENAI_API_KEY").map_err(|_| LlmError::MissingEnv {
            var: "OPENAI_API_KEY",
            hint: "",
        })?;
        Ok(Self::OpenAI {
            model: model.into(),
            api_key,
        })
    }

    pub fn local(model: impl Into<String>, base_url: impl Into<String>) -> Self {
        Self::Local {
            model: model.into(),
            base_url: base_url.into(),
        }
    }

    /// Auto-detect provider from available env vars.
    /// Priority: OPENROUTER > ANTHROPIC > OPENAI.
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
        Err(LlmError::MissingEnv {
            var: "OPENROUTER_API_KEY | ANTHROPIC_API_KEY | OPENAI_API_KEY",
            hint: "Set at least one API key.",
        })
    }
}

/// LLM client for making completions.
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

    pub async fn complete(&self, messages: &[Message]) -> Result<String> {
        match &self.provider {
            LlmProvider::OpenRouter { model, api_key } => {
                self.complete_openrouter(model, api_key, messages).await
            }
            LlmProvider::Anthropic { model, api_key } => {
                self.complete_anthropic(model, api_key, messages).await
            }
            LlmProvider::OpenAI { model, api_key } => self.complete_openai(model, api_key, messages).await,
            LlmProvider::Local { model, base_url } => self.complete_local(model, base_url, messages).await,
        }
    }

    async fn complete_openrouter(&self, model: &str, api_key: &str, messages: &[Message]) -> Result<String> {
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
            .json(&Request { model, messages })
            .send()
            .await?;

        let status = response.status();
        let body = response.text().await?;
        if !status.is_success() {
            return Err(LlmError::Provider(format!(
                "OpenRouter error ({}): {}",
                status, body
            )));
        }

        let resp: Response = serde_json::from_str(&body)?;
        if let Some(err) = resp.error {
            return Err(LlmError::Provider(format!("OpenRouter: {}", err.message)));
        }

        resp.choices
            .and_then(|c| c.into_iter().next())
            .map(|c| c.message.content)
            .ok_or_else(|| LlmError::Provider("No response from OpenRouter".into()))
    }

    async fn complete_anthropic(&self, model: &str, api_key: &str, messages: &[Message]) -> Result<String> {
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
            return Err(LlmError::Provider(format!(
                "Anthropic API error ({}): {}",
                status, body
            )));
        }

        let resp: Response = serde_json::from_str(&body)?;
        if let Some(err) = resp.error {
            return Err(LlmError::Provider(format!("{}: {}", err.error_type, err.message)));
        }

        let content = resp
            .content
            .ok_or_else(|| LlmError::Provider("No content in response".into()))?;

        Ok(content.into_iter().map(|c| c.text).collect::<Vec<_>>().join(""))
    }

    async fn complete_openai(&self, model: &str, api_key: &str, messages: &[Message]) -> Result<String> {
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
            .ok_or_else(|| LlmError::Provider("No response from OpenAI".into()))
    }

    async fn complete_local(&self, model: &str, base_url: &str, messages: &[Message]) -> Result<String> {
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

