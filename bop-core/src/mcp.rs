//! MCP (Model Context Protocol) client
//!
//! Implements the MCP protocol for tool discovery and invocation.
//! Supports stdio and HTTP transports.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};

use crate::{Error, Result};

use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, ChildStdout, Command};

/// MCP tool definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tool {
    pub name: String,
    pub description: String,
    pub input_schema: serde_json::Value,
}

/// MCP resource definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Resource {
    pub uri: String,
    pub name: String,
    pub description: Option<String>,
    pub mime_type: Option<String>,
}

/// Result of a tool invocation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    pub content: Vec<ContentItem>,
    pub is_error: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ContentItem {
    #[serde(rename = "text")]
    Text { text: String },
    #[serde(rename = "image")]
    Image { data: String, mime_type: String },
    #[serde(rename = "resource")]
    Resource { uri: String, text: String },
}

#[derive(Debug)]
struct JsonRpcStdio {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
    next_id: AtomicU64,
}

impl JsonRpcStdio {
    async fn spawn(command: &str, args: &[&str]) -> Result<Self> {
        let mut cmd = Command::new(command);
        cmd.args(args);
        cmd.stdin(std::process::Stdio::piped());
        cmd.stdout(std::process::Stdio::piped());
        cmd.stderr(std::process::Stdio::inherit());

        let mut child = cmd
            .spawn()
            .map_err(|e| Error::Mcp(format!("Failed to spawn MCP server: {e}")))?;

        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| Error::Mcp("Failed to open child stdin".to_string()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| Error::Mcp("Failed to open child stdout".to_string()))?;

        Ok(Self {
            child,
            stdin,
            stdout: BufReader::new(stdout),
            next_id: AtomicU64::new(1),
        })
    }

    async fn write_message(&mut self, value: &serde_json::Value) -> Result<()> {
        let body = serde_json::to_vec(value)?;
        let header = format!("Content-Length: {}\r\n\r\n", body.len());
        self.stdin
            .write_all(header.as_bytes())
            .await
            .map_err(|e| Error::Mcp(format!("Failed to write MCP header to stdin: {e}")))?;
        self.stdin
            .write_all(&body)
            .await
            .map_err(|e| Error::Mcp(format!("Failed to write MCP body to stdin: {e}")))?;
        self.stdin
            .flush()
            .await
            .map_err(|e| Error::Mcp(format!("Failed to flush MCP stdin: {e}")))?;
        Ok(())
    }

    async fn read_message(&mut self) -> Result<serde_json::Value> {
        // LSP-style framing: read headers until blank line, then read Content-Length bytes.
        let mut content_length: Option<usize> = None;

        loop {
            let mut line = String::new();
            let n = self
                .stdout
                .read_line(&mut line)
                .await
                .map_err(|e| Error::Mcp(format!("Failed to read MCP header line: {e}")))?;
            if n == 0 {
                return Err(Error::Mcp("MCP server closed stdout".to_string()));
            }

            let trimmed = line.trim_end_matches(['\r', '\n']);
            if trimmed.is_empty() {
                break;
            }

            let lower = trimmed.to_ascii_lowercase();
            if let Some(rest) = lower.strip_prefix("content-length:") {
                let len_str = rest.trim();
                content_length =
                    Some(len_str.parse::<usize>().map_err(|e| {
                        Error::Mcp(format!("Invalid Content-Length '{len_str}': {e}"))
                    })?);
            }
        }

        let len = content_length
            .ok_or_else(|| Error::Mcp("Missing Content-Length header".to_string()))?;
        let mut buf = vec![0u8; len];
        self.stdout
            .read_exact(&mut buf)
            .await
            .map_err(|e| Error::Mcp(format!("Failed to read MCP body ({len} bytes): {e}")))?;
        Ok(serde_json::from_slice(&buf)?)
    }

    async fn request(
        &mut self,
        method: &str,
        params: serde_json::Value,
    ) -> Result<serde_json::Value> {
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);
        let req = serde_json::json!({
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": params,
        });

        self.write_message(&req).await?;

        loop {
            let msg = self.read_message().await?;
            // Ignore notifications; match response by id.
            if msg.get("id").and_then(|v| v.as_u64()) == Some(id) {
                if let Some(err) = msg.get("error") {
                    return Err(Error::Mcp(format!("MCP error response: {err}")));
                }
                return Ok(msg);
            }
        }
    }

    async fn shutdown(&mut self) {
        let _ = self.child.start_kill();
    }
}

/// MCP client for connecting to MCP servers
pub struct McpClient {
    tools: HashMap<String, Tool>,
    resources: HashMap<String, Resource>,
    transport: McpTransport,
}

enum McpTransport {
    Stdio(tokio::sync::Mutex<JsonRpcStdio>),
    #[allow(dead_code)]
    Http {
        _url: String,
    },
}

impl McpClient {
    /// Create a new MCP client
    pub fn new() -> Self {
        Self {
            tools: HashMap::new(),
            resources: HashMap::new(),
            transport: McpTransport::Http {
                _url: "disabled".to_string(),
            },
        }
    }

    /// Connect to an MCP server via stdio
    pub async fn connect_stdio(command: &str, args: &[&str]) -> Result<Self> {
        let stdio = JsonRpcStdio::spawn(command, args).await?;
        let mut client = Self {
            tools: HashMap::new(),
            resources: HashMap::new(),
            transport: McpTransport::Stdio(tokio::sync::Mutex::new(stdio)),
        };

        // Best-effort initialize + populate caches.
        client.initialize().await?;
        client.refresh_tools().await?;
        client.refresh_resources().await?;

        Ok(client)
    }

    /// Connect to an MCP server via HTTP
    pub async fn connect_http(_url: &str) -> Result<Self> {
        // TODO: HTTP transport
        Ok(Self::new())
    }

    async fn initialize(&mut self) -> Result<()> {
        // Minimal MCP initialize request shape; tolerate servers that ignore unknown fields.
        let params = serde_json::json!({
            "protocolVersion": "2024-11-05",
            "clientInfo": { "name": "bop", "version": env!("CARGO_PKG_VERSION") },
            "capabilities": {}
        });

        match &self.transport {
            McpTransport::Stdio(lock) => {
                let mut t = lock.lock().await;
                let _ = t.request("initialize", params).await?;
                Ok(())
            }
            McpTransport::Http { .. } => Ok(()),
        }
    }

    async fn refresh_tools(&mut self) -> Result<()> {
        let resp = match &self.transport {
            McpTransport::Stdio(lock) => {
                let mut t = lock.lock().await;
                t.request("tools/list", serde_json::json!({})).await?
            }
            McpTransport::Http { .. } => return Ok(()),
        };

        let tools_val = resp
            .get("result")
            .and_then(|r| r.get("tools"))
            .ok_or_else(|| Error::Mcp("Missing result.tools in tools/list response".to_string()))?;

        let tools: Vec<Tool> = serde_json::from_value(tools_val.clone())?;
        self.tools = tools.into_iter().map(|t| (t.name.clone(), t)).collect();
        Ok(())
    }

    async fn refresh_resources(&mut self) -> Result<()> {
        let resp = match &self.transport {
            McpTransport::Stdio(lock) => {
                let mut t = lock.lock().await;
                t.request("resources/list", serde_json::json!({})).await?
            }
            McpTransport::Http { .. } => return Ok(()),
        };

        let resources_val = resp
            .get("result")
            .and_then(|r| r.get("resources"))
            .ok_or_else(|| {
                Error::Mcp("Missing result.resources in resources/list response".to_string())
            })?;

        let resources: Vec<Resource> = serde_json::from_value(resources_val.clone())?;
        self.resources = resources.into_iter().map(|r| (r.uri.clone(), r)).collect();
        Ok(())
    }

    /// List available tools
    pub fn list_tools(&self) -> Vec<&Tool> {
        self.tools.values().collect()
    }

    /// Get a tool by name
    pub fn get_tool(&self, name: &str) -> Option<&Tool> {
        self.tools.get(name)
    }

    /// Invoke a tool
    pub async fn invoke_tool(
        &self,
        name: &str,
        arguments: serde_json::Value,
    ) -> Result<ToolResult> {
        let _tool = self
            .tools
            .get(name)
            .ok_or_else(|| Error::ToolNotFound(name.to_string()))?;

        let resp = match &self.transport {
            McpTransport::Stdio(lock) => {
                let mut t = lock.lock().await;
                t.request(
                    "tools/call",
                    serde_json::json!({
                        "name": name,
                        "arguments": arguments,
                    }),
                )
                .await?
            }
            McpTransport::Http { .. } => {
                return Err(Error::Mcp("HTTP transport not implemented".to_string()));
            }
        };

        let result_val = resp
            .get("result")
            .ok_or_else(|| Error::Mcp("Missing result in tools/call response".to_string()))?;
        Ok(serde_json::from_value(result_val.clone())?)
    }

    /// List available resources
    pub fn list_resources(&self) -> Vec<&Resource> {
        self.resources.values().collect()
    }

    /// Read a resource
    pub async fn read_resource(&self, uri: &str) -> Result<String> {
        let _resource = self
            .resources
            .get(uri)
            .ok_or_else(|| Error::Mcp(format!("Resource not found: {}", uri)))?;

        let resp = match &self.transport {
            McpTransport::Stdio(lock) => {
                let mut t = lock.lock().await;
                t.request(
                    "resources/read",
                    serde_json::json!({
                        "uri": uri,
                    }),
                )
                .await?
            }
            McpTransport::Http { .. } => {
                return Err(Error::Mcp("HTTP transport not implemented".to_string()));
            }
        };

        // MCP resources/read typically returns { contents: [...] }. Keep it minimal: if there's
        // a single text item, return it; otherwise return JSON for callers to parse.
        let result_val = resp
            .get("result")
            .ok_or_else(|| Error::Mcp("Missing result in resources/read response".to_string()))?;

        if let Some(contents) = result_val.get("contents").and_then(|c| c.as_array()) {
            if let Some(first) = contents.first() {
                if let Some(text) = first.get("text").and_then(|t| t.as_str()) {
                    return Ok(text.to_string());
                }
            }
        }

        Ok(result_val.to_string())
    }
}

impl Default for McpClient {
    fn default() -> Self {
        Self::new()
    }
}
