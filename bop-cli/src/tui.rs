//! TUI mode - optional interactive interface
//!
//! Enabled with `--features tui`

use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, Borders, Paragraph, Wrap},
    Frame, Terminal,
};
use std::io;

use bop_agent_core::{Agent, LlmProvider};

struct App {
    agent: Agent,
    messages: Vec<(String, String)>,
    input: String,
    scroll: u16,
    is_loading: bool,
    model: String,
}

impl App {
    fn new(provider: &str, model: &str) -> Result<Self> {
        let llm = match provider {
            "anthropic" => LlmProvider::anthropic(model)?,
            "openai" => LlmProvider::openai(model)?,
            "local" => LlmProvider::local(model, "http://localhost:11434"),
            _ => anyhow::bail!("unknown provider: {}", provider),
        };

        Ok(Self {
            agent: Agent::new(llm),
            messages: Vec::new(),
            input: String::new(),
            scroll: 0,
            is_loading: false,
            model: model.to_string(),
        })
    }

    async fn submit(&mut self) -> Result<()> {
        let input = std::mem::take(&mut self.input);
        self.messages.push(("user".to_string(), input.clone()));
        self.is_loading = true;

        match self.agent.query(&input).await {
            Ok(response) => {
                self.messages.push(("assistant".to_string(), response));
            }
            Err(e) => {
                self.messages
                    .push(("system".to_string(), format!("Error: {}", e)));
            }
        }

        self.is_loading = false;
        self.scroll_to_bottom();
        Ok(())
    }

    fn scroll_up(&mut self) {
        self.scroll = self.scroll.saturating_sub(1);
    }

    fn scroll_down(&mut self) {
        self.scroll = self.scroll.saturating_add(1);
    }

    fn scroll_to_bottom(&mut self) {
        self.scroll = (self.messages.len() as u16).saturating_mul(3);
    }
}

pub async fn run(model: &str, provider: &str) -> Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let app = App::new(provider, model)?;
    let res = run_app(&mut terminal, app).await;

    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    res
}

async fn run_app<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
    mut app: App,
) -> Result<()> {
    loop {
        let _ = terminal.draw(|f| ui(f, &app));

        if event::poll(std::time::Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match key.code {
                        KeyCode::Char('q') if app.input.is_empty() => return Ok(()),
                        KeyCode::Esc => return Ok(()),
                        KeyCode::Enter => {
                            if !app.input.is_empty() {
                                app.submit().await?;
                            }
                        }
                        KeyCode::Char(c) => {
                            app.input.push(c);
                        }
                        KeyCode::Backspace => {
                            let _ = app.input.pop();
                        }
                        KeyCode::Up => app.scroll_up(),
                        KeyCode::Down => app.scroll_down(),
                        _ => {}
                    }
                }
            }
        }
    }
}

fn ui(f: &mut Frame<'_>, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(3),
            Constraint::Length(3),
            Constraint::Length(1),
        ])
        .split(f.area());

    // Chat history
    let history_block = Block::default()
        .title(" BOP ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan));

    let history_text: Vec<Line<'_>> = app
        .messages
        .iter()
        .flat_map(|(role, content)| {
            let style = match role.as_str() {
                "user" => Style::default().fg(Color::Green),
                "assistant" => Style::default().fg(Color::White),
                "system" => Style::default().fg(Color::Yellow),
                _ => Style::default(),
            };
            let prefix = match role.as_str() {
                "user" => "You: ",
                "assistant" => "BOP: ",
                "system" => "System: ",
                _ => "",
            };
            content
                .lines()
                .enumerate()
                .map(|(i, line)| {
                    if i == 0 {
                        Line::from(Span::styled(format!("{}{}", prefix, line), style))
                    } else {
                        Line::from(Span::styled(format!("      {}", line), style))
                    }
                })
                .collect::<Vec<_>>()
        })
        .collect();

    let history = Paragraph::new(Text::from(history_text))
        .block(history_block)
        .wrap(Wrap { trim: false })
        .scroll((app.scroll, 0));
    f.render_widget(history, chunks[0]);

    // Input
    let input_block = Block::default()
        .title(" Input (Enter to send, Esc to quit) ")
        .borders(Borders::ALL)
        .border_style(if app.is_loading {
            Style::default().fg(Color::Yellow)
        } else {
            Style::default().fg(Color::Green)
        });

    let input = Paragraph::new(app.input.as_str())
        .block(input_block)
        .style(Style::default().add_modifier(Modifier::BOLD));
    f.render_widget(input, chunks[1]);

    // Status
    let status = if app.is_loading {
        Span::styled(
            " Thinking... ",
            Style::default().fg(Color::Yellow).bg(Color::DarkGray),
        )
    } else {
        Span::styled(
            format!(" {} | {} messages ", app.model, app.messages.len()),
            Style::default().fg(Color::Cyan).bg(Color::DarkGray),
        )
    };
    f.render_widget(Paragraph::new(Line::from(status)), chunks[2]);

    if !app.is_loading {
        f.set_cursor_position((chunks[1].x + app.input.len() as u16 + 1, chunks[1].y + 1));
    }
}
