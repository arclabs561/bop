//! BOP CLI - Research agent command line interface
//!
//! Design principles (following hop-cli):
//! - Silent success by default
//! - Errors to stderr with helpful hints
//! - JSON output option for machine parsing
//! - Fast startup and execution
//!
//! Examples:
//!   bop query "What is the capital of France?"
//!   bop research "transformer architectures" --depth 3
//!   bop session list
//!   bop tui  # Launch interactive TUI (requires --features tui)

use anyhow::{Context, Result};
use clap::{CommandFactory, Parser, Subcommand};
use clap_complete::{generate, Shell};
use indicatif::{ProgressBar, ProgressStyle};
use rustyline::error::ReadlineError;
use rustyline::DefaultEditor;
use std::path::PathBuf;

mod output;

#[cfg(feature = "tui")]
mod tui;

#[derive(Parser)]
#[command(name = "bop")]
#[command(about = "BOP: Research agent - query, research, synthesize")]
#[command(version)]
#[command(after_help = r#"EXAMPLES:
    bop query "What causes aurora borealis?"
    bop research "graph neural networks" --output notes.md
    bop session list --json
    bop chat  # Interactive REPL
"#)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Output as JSON (for scripting)
    #[arg(long, global = true)]
    json: bool,

    /// Verbose output
    #[arg(short, long, global = true)]
    verbose: bool,

    /// Quiet mode (errors only)
    #[arg(short, long, global = true)]
    quiet: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// Ask a single question
    ///
    /// Quick query with immediate response.
    /// For multi-turn conversations, use `bop chat`.
    Query {
        /// The question to ask
        question: String,

        /// Model to use (provider-specific, or leave empty for default)
        #[arg(short, long)]
        model: Option<String>,

        /// Provider: auto, openrouter, anthropic, openai, local
        #[arg(short, long, default_value = "auto")]
        provider: String,

        /// Local model URL (for provider=local)
        #[arg(long, default_value = "http://localhost:11434")]
        local_url: String,

        /// System prompt override
        #[arg(long)]
        system: Option<String>,
    },

    /// Research a topic in depth
    ///
    /// Performs multi-step research with source gathering.
    Research {
        /// Topic to research
        topic: String,

        /// Research depth (1-5, higher = more thorough)
        #[arg(short, long, default_value = "2")]
        depth: u8,

        /// Output file (markdown)
        #[arg(short, long)]
        output: Option<PathBuf>,

        /// Model to use (or leave empty for default)
        #[arg(short, long)]
        model: Option<String>,

        /// Provider: auto, openrouter, anthropic, openai
        #[arg(short, long, default_value = "auto")]
        provider: String,
    },

    /// Interactive chat REPL
    ///
    /// Multi-turn conversation in the terminal.
    /// Type 'exit' or Ctrl-D to quit.
    Chat {
        /// Model to use (provider-specific, or leave empty for default)
        #[arg(short, long)]
        model: Option<String>,

        /// Provider: auto, openrouter, anthropic, openai, local
        #[arg(short, long, default_value = "auto")]
        provider: String,

        /// Local model URL (for provider=local)
        #[arg(long, default_value = "http://localhost:11434")]
        local_url: String,

        /// Resume a previous session
        #[arg(long)]
        session: Option<String>,
    },

    /// Manage sessions
    Session {
        #[command(subcommand)]
        action: SessionAction,
    },

    /// Launch TUI interface
    #[cfg(feature = "tui")]
    Tui {
        /// Model to use
        #[arg(short, long, default_value = "claude-sonnet-4-20250514")]
        model: String,

        /// Provider (anthropic, openai, local)
        #[arg(short, long, default_value = "anthropic")]
        provider: String,
    },

    /// Generate shell completions
    Completions {
        /// Shell to generate completions for
        #[arg(value_enum)]
        shell: Shell,
    },
}

#[derive(Subcommand)]
enum SessionAction {
    /// List all sessions
    List,
    /// Show a specific session
    Show {
        /// Session ID
        id: String,
    },
    /// Export a session to file
    Export {
        /// Session ID
        id: String,
        /// Output file
        #[arg(short, long)]
        output: PathBuf,
    },
    /// Delete a session
    Delete {
        /// Session ID
        id: String,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    // Load .env from current dir, parent dirs, or home
    load_env();

    let cli = Cli::parse();

    // Set up logging
    if cli.verbose {
        tracing_subscriber::fmt()
            .with_env_filter("bop=debug")
            .with_writer(std::io::stderr)
            .init();
    } else if !cli.quiet {
        tracing_subscriber::fmt()
            .with_env_filter("bop=info")
            .with_writer(std::io::stderr)
            .init();
    }

    let result = match cli.command {
        Commands::Query {
            question,
            model,
            provider,
            local_url,
            system,
        } => cmd_query(&question, model.as_deref(), &provider, &local_url, system.as_deref(), cli.json).await,

        Commands::Research {
            topic,
            depth,
            output,
            model,
            provider,
        } => cmd_research(&topic, depth, output.as_deref(), model.as_deref(), &provider, cli.json).await,

        Commands::Chat {
            model,
            provider,
            local_url,
            session,
        } => cmd_chat(model.as_deref(), &provider, &local_url, session.as_deref()).await,

        Commands::Session { action } => cmd_session(action, cli.json).await,

        #[cfg(feature = "tui")]
        Commands::Tui { model, provider } => tui::run(&model, &provider).await,

        Commands::Completions { shell } => {
            let mut cmd = Cli::command();
            generate(shell, &mut cmd, "bop", &mut std::io::stdout());
            Ok(())
        }
    };

    if let Err(e) = &result {
        if cli.json {
            let err_json = serde_json::json!({
                "error": e.to_string(),
                "chain": e.chain().skip(1).map(|c| c.to_string()).collect::<Vec<_>>()
            });
            eprintln!("{}", serde_json::to_string_pretty(&err_json)?);
        } else {
            eprintln!("error: {e}");
            for cause in e.chain().skip(1) {
                eprintln!("  caused by: {cause}");
            }
        }
        std::process::exit(1);
    }

    Ok(())
}

async fn cmd_query(
    question: &str,
    model: Option<&str>,
    provider: &str,
    local_url: &str,
    system: Option<&str>,
    json_output: bool,
) -> Result<()> {
    use bop_core::Agent;

    let llm = make_provider(provider, model, local_url)?;
    let model_name = get_model_name(&llm);

    let mut agent = Agent::new(llm);

    // Override system prompt if provided
    if let Some(_sys) = system {
        // TODO: agent.set_system_prompt(sys);
    }

    let response = agent
        .query(question)
        .await
        .context("failed to get response")?;

    if json_output {
        let output = serde_json::json!({
            "question": question,
            "response": response,
            "model": model_name,
        });
        println!("{}", serde_json::to_string_pretty(&output)?);
    } else {
        println!("{}", response);
    }

    Ok(())
}

/// Create LLM provider from CLI args
fn make_provider(provider: &str, model: Option<&str>, local_url: &str) -> Result<bop_core::LlmProvider> {
    use bop_core::LlmProvider;

    match provider {
        "auto" => LlmProvider::auto(model).map_err(|e| anyhow::anyhow!("{}", e)),
        "openrouter" => {
            let m = model.unwrap_or("anthropic/claude-sonnet-4");
            LlmProvider::openrouter(m).map_err(|e| anyhow::anyhow!("{}", e))
        }
        "anthropic" => {
            let m = model.unwrap_or("claude-sonnet-4-20250514");
            LlmProvider::anthropic(m).map_err(|e| anyhow::anyhow!("{}", e))
        }
        "openai" => {
            let m = model.unwrap_or("gpt-4o");
            LlmProvider::openai(m).map_err(|e| anyhow::anyhow!("{}", e))
        }
        "local" => {
            let m = model.unwrap_or("llama3.2");
            Ok(LlmProvider::local(m, local_url))
        }
        _ => anyhow::bail!(
            "unknown provider: {}. Use: auto, openrouter, anthropic, openai, or local",
            provider
        ),
    }
}

/// Get model name from provider for display
fn get_model_name(provider: &bop_core::LlmProvider) -> String {
    use bop_core::LlmProvider;
    match provider {
        LlmProvider::OpenRouter { model, .. } => model.clone(),
        LlmProvider::Anthropic { model, .. } => model.clone(),
        LlmProvider::OpenAI { model, .. } => model.clone(),
        LlmProvider::Local { model, .. } => model.clone(),
    }
}

async fn cmd_research(
    topic: &str,
    depth: u8,
    output: Option<&std::path::Path>,
    model: Option<&str>,
    provider: &str,
    json_output: bool,
) -> Result<()> {
    use bop_core::ResearchAgent;

    let llm = make_provider(provider, model, "")?;
    let model_name = get_model_name(&llm);
    let mut agent = ResearchAgent::new(llm);

    // Show progress
    let spinner = ProgressBar::new_spinner();
    spinner.set_style(
        ProgressStyle::default_spinner()
            .template("{spinner:.cyan} {msg}")
            .unwrap(),
    );
    spinner.set_message(format!("Researching: {} (depth {})", topic, depth));
    spinner.enable_steady_tick(std::time::Duration::from_millis(100));

    let result = agent
        .research(topic)
        .await
        .context("research failed")?;

    spinner.finish_and_clear();

    if let Some(path) = output {
        std::fs::write(path, &result).context("failed to write output")?;
        eprintln!("Wrote: {}", path.display());
    }

    if json_output {
        let output = serde_json::json!({
            "topic": topic,
            "depth": depth,
            "result": result,
            "model": model_name,
        });
        println!("{}", serde_json::to_string_pretty(&output)?);
    } else if output.is_none() {
        println!("{}", result);
    }

    Ok(())
}

async fn cmd_chat(model: Option<&str>, provider: &str, local_url: &str, _session_id: Option<&str>) -> Result<()> {
    use bop_core::Agent;

    let llm = make_provider(provider, model, local_url)?;
    let model_name = get_model_name(&llm);

    let mut agent = Agent::new(llm);

    eprintln!("BOP Chat ({}) - Type 'exit' or Ctrl-D to quit", model_name);
    eprintln!("Commands: /clear, /model, /help");
    eprintln!();

    let mut rl = DefaultEditor::new()?;

    // Load history if exists
    let history_path = dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("bop")
        .join("chat_history.txt");
    let _ = rl.load_history(&history_path);

    loop {
        match rl.readline("> ") {
            Ok(line) => {
                let input = line.trim();
                if input.is_empty() {
                    continue;
                }

                // Add to history
                let _ = rl.add_history_entry(input);

                // Handle commands
                if input.starts_with('/') {
                    match input {
                        "/exit" | "/quit" => break,
                        "/clear" => {
                            agent.reset();
                            eprintln!("Conversation cleared.");
                            continue;
                        }
                        "/model" => {
                            eprintln!("Current model: {}", model_name);
                            continue;
                        }
                        "/help" => {
                            eprintln!("Commands:");
                            eprintln!("  /clear  - Clear conversation history");
                            eprintln!("  /model  - Show current model");
                            eprintln!("  /exit   - Exit chat");
                            continue;
                        }
                        _ => {
                            eprintln!("Unknown command: {}", input);
                            continue;
                        }
                    }
                }

                if input == "exit" || input == "quit" {
                    break;
                }

                // Show spinner while waiting
                let spinner = ProgressBar::new_spinner();
                spinner.set_style(
                    ProgressStyle::default_spinner()
                        .template("{spinner:.cyan} Thinking...")
                        .unwrap(),
                );
                spinner.enable_steady_tick(std::time::Duration::from_millis(100));

                match agent.query(input).await {
                    Ok(response) => {
                        spinner.finish_and_clear();
                        println!();
                        println!("{}", response);
                        println!();
                    }
                    Err(e) => {
                        spinner.finish_and_clear();
                        eprintln!("error: {}", e);
                    }
                }
            }
            Err(ReadlineError::Interrupted) => {
                eprintln!("^C");
                continue;
            }
            Err(ReadlineError::Eof) => {
                eprintln!();
                break;
            }
            Err(e) => {
                eprintln!("readline error: {}", e);
                break;
            }
        }
    }

    // Save history
    if let Some(parent) = history_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let _ = rl.save_history(&history_path);

    Ok(())
}

async fn cmd_session(action: SessionAction, json_output: bool) -> Result<()> {
    use bop_core::session::SessionStore;

    let store_path = dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("bop")
        .join("sessions");

    std::fs::create_dir_all(&store_path)?;
    let store = SessionStore::open(&store_path)?;

    match action {
        SessionAction::List => {
            let sessions = store.list()?;
            if json_output {
                let output = serde_json::json!({ "sessions": sessions.iter().map(|s| s.to_string()).collect::<Vec<_>>() });
                println!("{}", serde_json::to_string_pretty(&output)?);
            } else {
                // Empty list = no output (Unix convention)
                for id in sessions {
                    println!("{}", id);
                }
            }
        }
        SessionAction::Show { id } => {
            let uuid = id.parse().context("invalid session ID")?;
            let session = store
                .load(uuid)?
                .ok_or_else(|| anyhow::anyhow!("session not found: {}", id))?;

            if json_output {
                println!("{}", session.to_json()?);
            } else {
                println!("Session: {}", session.id);
                println!("Created: {}", session.created_at);
                println!("Messages: {}", session.len());
                println!();
                for msg in &session.messages {
                    println!("[{:?}] {}", msg.role, msg.content);
                }
            }
        }
        SessionAction::Export { id, output } => {
            let uuid = id.parse().context("invalid session ID")?;
            let session = store
                .load(uuid)?
                .ok_or_else(|| anyhow::anyhow!("session not found: {}", id))?;

            std::fs::write(&output, session.to_json()?)?;
            eprintln!("Exported to: {}", output.display());
        }
        SessionAction::Delete { id } => {
            let uuid = id.parse().context("invalid session ID")?;
            store.delete(uuid)?;
            eprintln!("Deleted: {}", id);
        }
    }

    Ok(())
}

/// Load environment variables from .env files
/// Searches: current dir -> parent dirs -> ~/.bop/.env -> bop repo .env
fn load_env() {
    // Try current directory and parents
    if dotenvy::dotenv().is_ok() {
        return;
    }

    // Try ~/.bop/.env
    if let Some(home) = dirs::home_dir() {
        let home_env = home.join(".bop").join(".env");
        if home_env.exists() {
            let _ = dotenvy::from_path(&home_env);
            return;
        }
    }

    // Try the bop repo's .env (for development)
    let bop_repo_env = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .map(|p| p.join(".env"));
    if let Some(path) = bop_repo_env {
        if path.exists() {
            let _ = dotenvy::from_path(&path);
        }
    }
}
