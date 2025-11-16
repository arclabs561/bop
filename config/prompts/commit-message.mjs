/**
 * Custom commit message prompt for BOP (Knowledge Structure Research Agent)
 * 
 * This prompt steers commits toward clear, research-focused messages that
 * reflect the theoretical and practical nature of the project.
 */

export const COMMIT_MESSAGE_PROMPT = `You are analyzing a commit message for BOP, a Knowledge Structure Research Agent.

BOP is a Python research project focused on:
- Knowledge structure research and reasoning
- LLM reasoning dynamics and structured reasoning schemas
- Information geometry, topological structure, causal inference
- Multi-agent research orchestration with MCP tools
- Theoretical foundations (d-separation, clique complexes, attractor basins)

Commit message: "{{message}}"
Staged files: {{stagedFiles}}
Recent commits: {{recentCommits}}
Branch: {{branch}}

Analyze this commit message considering:

1. **Clarity for Research Context**:
   - Does it clearly describe what changed and why?
   - Is the theoretical or practical impact clear?
   - Would a researcher understand the contribution?

2. **Conventional Commits Format**:
   - Type: feat, fix, docs, refactor, test, chore, research, theory, analysis, agent, mcp
   - Scope (recommended for feat/fix/refactor): agent, orchestrator, research, topology, constraints, eval, cli, web, mcp, etc.
   - Subject: Clear, concise description (max 72 chars)

3. **BOP-Specific Considerations**:
   - Research/theory commits should indicate theoretical contribution
   - Agent/orchestrator changes should note impact on reasoning
   - MCP tool integrations should mention tool and purpose
   - Documentation should note if it's research notes vs. user docs
   - Topology/trust changes should mention which metrics or structures
   - Constraint solver changes should note optimization impact
   - Quality feedback changes should mention evaluation dimensions

4. **Quality Indicators**:
   - Specificity (not vague like "update code")
   - Context (why this change matters)
   - Completeness (covers what was changed)

Return JSON:
{
  "score": 0-10,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1"],
  "improved_message": "better message",
  "reasoning": "explanation focusing on research clarity and BOP context"
}`;

export function formatCommitMessagePrompt(data) {
  const recentCommits = (data.recentCommits || []).join('\n');
  const stagedFiles = (data.stagedFiles || []).join('\n');
  
  return COMMIT_MESSAGE_PROMPT
    .replace('{{message}}', data.message || '')
    .replace('{{stagedFiles}}', stagedFiles || 'No files staged')
    .replace('{{recentCommits}}', recentCommits || 'No recent commits')
    .replace('{{branch}}', data.branch || 'unknown');
}

