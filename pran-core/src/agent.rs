//! Agent - core reasoning entity
//!
//! An agent maintains conversation state, invokes tools, and produces responses.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::llm::{LlmClient, LlmProvider, Message};
use crate::mcp::McpClient;
use crate::session::Session;
use crate::Result;
use axi::Agent as AxiAgent;
use axi::ModelAdapter;

/// Agent configuration
#[derive(Debug, Clone)]
pub struct AgentConfig {
    pub system_prompt: String,
    pub max_turns: usize,
    pub tool_use_enabled: bool,
    pub use_axi: bool,
}

impl Default for AgentConfig {
    fn default() -> Self {
        Self {
            system_prompt: "You are a helpful research assistant.".into(),
            max_turns: 10,
            tool_use_enabled: true,
            use_axi: true,
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
    // Experimental: Axi agent integration
    axi_agent: Option<AxiAgent>,
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
            axi_agent: None,
        }
    }

    /// Create an agent using Axi (experimental)
    pub fn with_axi(provider: LlmProvider) -> Self {
        let mut agent = Self::new(provider);
        // Initialize Axi agent with empty context for now
        // This is a placeholder for future integration
        agent.axi_agent = Some(AxiAgent::new((), "You are a helpful research assistant."));
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
        if self.config.use_axi {
            return self.query_axi(input).await;
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

    /// Internal query using Axi engine
    async fn query_axi(&mut self, input: &str) -> Result<String> {
        use axi::adapters::{anthropic::AnthropicAdapter, openai::OpenAiAdapter, ollama::OllamaAdapter};
        use axi::RunOutcome;

        let provider = self.llm.provider();
        let adapter: Box<dyn ModelAdapter> = match provider {
            LlmProvider::Anthropic { api_key, model } => {
                Box::new(AnthropicAdapter::new(api_key.clone(), model.clone()))
            }
            LlmProvider::OpenAI { api_key, model } => {
                Box::new(OpenAiAdapter::new(api_key.clone(), model.clone()))
            }
            LlmProvider::Local { model, base_url } => {
                Box::new(OllamaAdapter::new(base_url.clone(), model.clone()))
            }
            LlmProvider::OpenRouter { api_key, model } => {
                Box::new(OpenAiAdapter::new(api_key.clone(), model.clone())
                    .with_base_url("https://openrouter.ai/api/v1"))
            }
        };

        let mut axi_agent = self.axi_agent.take().unwrap_or_else(|| {
            AxiAgent::new((), &self.config.system_prompt)
        });

        // Map history to axi messages
        for msg in &self.history {
            // axi::agent::Message mapping logic
        }
        
        let result = axi_agent.run::<String>(adapter.as_ref(), input, None);
        
        self.axi_agent = Some(axi_agent);

        match result {
            Ok(RunOutcome::Completed(run)) => {
                let output = run.output;
                self.history.push(Message::user(input));
                self.history.push(Message::assistant(&output));
                Ok(output)
            }
            Ok(RunOutcome::Deferred(_)) => Err(anyhow::anyhow!("deferred").into()),
            Err(e) => Err(anyhow::anyhow!(e).into()),
        }
    }

    pub fn config(&self) -> &AgentConfig {
        &self.config
    }
}
