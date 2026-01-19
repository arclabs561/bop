//! Agent - core reasoning entity
//!
//! An agent maintains conversation state, invokes tools, and produces responses.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::llm::{LlmClient, LlmProvider, Message};
use crate::mcp::McpClient;
use crate::session::Session;
use crate::Result;
use axi::agent::Model;

type BopAgent = axi::Agent<()>;

/// Agent configuration
#[derive(Debug, Clone)]
pub struct AgentConfig {
    pub system_prompt: String,
    pub max_turns: usize,
    pub tool_use_enabled: bool,
    pub use_bop: bool,
}

impl Default for AgentConfig {
    fn default() -> Self {
        Self {
            system_prompt: "You are a helpful research assistant.".into(),
            max_turns: 10,
            tool_use_enabled: true,
            use_bop: true, // Default to axi-powered engine
        }
    }
}

/// Agent state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AgentState {
    Idle,
    Thinking,
    ToolUse { tool: String, input: String },
    Responding,
    Error { message: String },
}

/// The main agent struct
pub struct Agent {
    id: Uuid,
    config: AgentConfig,
    llm: LlmClient,
    mcp: Option<McpClient>,
    state: AgentState,
    history: Vec<Message>,
    // Experimental: Bop agent integration
    bop_agent: Option<BopAgent>,
}

impl Agent {
    /// Create a new agent with the given LLM provider
    pub fn new(provider: LlmProvider) -> Self {
        Self {
            id: Uuid::new_v4(),
            config: AgentConfig::default(),
            llm: LlmClient::new(provider),
            mcp: None,
            state: AgentState::Idle,
            history: Vec::new(),
            bop_agent: None,
        }
    }

    /// Create an agent using Bop (experimental)
    pub fn with_bop(provider: LlmProvider) -> Self {
        let mut agent = Self::new(provider);
        // Initialize Bop agent with empty context for now
        // This is a placeholder for future integration
        agent.bop_agent = Some(BopAgent::new((), "You are a helpful research assistant."));
        agent
    }

    /// Create an agent with custom configuration
    pub fn with_config(provider: LlmProvider, config: AgentConfig) -> Self {
        let mut agent = Self::new(provider);
        agent.config = config;
        agent
    }

    /// Connect an MCP client for tool use
    pub fn with_mcp(mut self, mcp: McpClient) -> Self {
        self.mcp = Some(mcp);
        self
    }

    /// Get the agent's ID
    pub fn id(&self) -> Uuid {
        self.id
    }

    /// Get the current state
    pub fn state(&self) -> &AgentState {
        &self.state
    }

    /// Process a user query and return a response
    pub async fn query(&mut self, input: &str) -> Result<String> {
        if self.config.use_bop {
            return self.query_bop(input).await;
        }

        self.state = AgentState::Thinking;

        // Add system prompt if this is the first message
        if self.history.is_empty() {
            self.history.push(Message::system(&self.config.system_prompt));
        }

        // Add user message
        self.history.push(Message::user(input));

        // Get completion
        self.state = AgentState::Responding;
        let response = self.llm.complete(&self.history).await?;

        // Add assistant response to history
        self.history.push(Message::assistant(&response));

        self.state = AgentState::Idle;
        Ok(response)
    }

    /// Reset the conversation history
    pub fn reset(&mut self) {
        self.history.clear();
        self.state = AgentState::Idle;
    }

    /// Export current session
    pub fn export_session(&self) -> Session {
        Session {
            id: self.id,
            messages: self.history.clone(),
            created_at: chrono::Utc::now(),
        }
    }

    /// Internal query using Bop engine (axi-based)
    async fn query_bop(&mut self, input: &str) -> Result<String> {
        use axi::adapters::{
            anthropic::AnthropicAdapter,
            ollama::OllamaAdapter,
            openai::GenericOpenAiAdapter,
            openrouter::OpenRouterAdapter,
        };
        use axi::RunOutcome;

        self.state = AgentState::Thinking;

        let provider = self.llm.provider();
        let adapter: Box<dyn Model> = match provider {
            LlmProvider::Anthropic { api_key, model } => {
                Box::new(AnthropicAdapter::new(api_key.clone(), model.clone()))
            }
            LlmProvider::OpenAI { api_key, model } => {
                Box::new(
                    GenericOpenAiAdapter::new("https://api.openai.com/v1", model.clone())
                        .with_api_key(api_key.clone()),
                )
            }
            LlmProvider::Local { model, base_url } => {
                Box::new(OllamaAdapter::new(base_url.clone(), model.clone()))
            }
            LlmProvider::OpenRouter { api_key, model } => {
                Box::new(OpenRouterAdapter::new(api_key.clone(), model.clone()))
            }
        };

        let mut bop_agent = self.bop_agent.take().unwrap_or_else(|| {
            BopAgent::new((), &self.config.system_prompt)
        });

        // Ensure system prompt is updated if config changed
        bop_agent.set_system(self.config.system_prompt.clone());

        // Map history to bop messages
        // axi::Agent::run_with_history expects the FULL conversation.
        // We construct it from self.history + new input.
        let mut axi_messages = Vec::with_capacity(self.history.len() + 1);
        for msg in &self.history {
            let m = match msg.role {
                crate::llm::Role::System => axi::agent::Message::System(msg.content.clone()),
                crate::llm::Role::User => axi::agent::Message::User(msg.content.clone()),
                crate::llm::Role::Assistant => axi::agent::Message::assistant(msg.content.clone()),
            };
            axi_messages.push(m);
        }
        
        // Add current input
        let input_str = input.to_string();
        axi_messages.push(axi::agent::Message::User(input_str.clone()));

        // Run axi agent in blocking thread (since axi uses sync ureq)
        let result = tokio::task::spawn_blocking(move || {
            bop_agent.run_with_history::<serde_json::Value>(adapter.as_ref(), axi_messages, None).map(|out| (bop_agent, out))
        }).await.map_err(|e| anyhow::anyhow!("Task join error: {e}"))??;

        let (returned_agent, outcome) = result;
        self.bop_agent = Some(returned_agent);

        match outcome {
            RunOutcome::Completed(run) => {
                let output_text = if let serde_json::Value::String(s) = run.output {
                    s
                } else {
                    serde_json::to_string(&run.output).unwrap_or_default()
                };

                // Update history
                if self.history.is_empty() {
                    self.history.push(Message::system(&self.config.system_prompt));
                }
                self.history.push(Message::user(input_str));
                self.history.push(Message::assistant(&output_text));
                
                self.state = AgentState::Idle;
                Ok(output_text)
            }
            RunOutcome::Deferred(_) => {
                self.state = AgentState::Error { message: "Deferred run not supported in chat mode".into() };
                Err(anyhow::anyhow!("deferred run").into())
            }
        }
    }

    pub fn config(&self) -> &AgentConfig {
        &self.config
    }
}
