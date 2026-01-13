//! Agent - core reasoning entity
//!
//! An agent maintains conversation state, invokes tools, and produces responses.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::llm::{LlmClient, LlmProvider, Message};
use crate::mcp::McpClient;
use crate::session::Session;
use crate::Result;

/// Agent configuration
#[derive(Debug, Clone)]
pub struct AgentConfig {
    pub system_prompt: String,
    pub max_turns: usize,
    pub tool_use_enabled: bool,
}

impl Default for AgentConfig {
    fn default() -> Self {
        Self {
            system_prompt: "You are a helpful research assistant.".into(),
            max_turns: 10,
            tool_use_enabled: true,
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
        }
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
}
