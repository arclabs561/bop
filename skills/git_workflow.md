# Git Workflow Skill

**Purpose:** Guide BOP in following proper git workflow and commit message conventions.

**Tags:** git, workflow, commits, version-control

## Commit Message Format

### Conventional Commits
```
type(scope): subject

body (optional)

footer (optional)
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `chore`: Maintenance tasks
- `refactor`: Code refactoring
- `test`: Test changes
- `perf`: Performance improvements
- `style`: Code style changes (formatting)

### BOP-Specific Types
- `research`: Research work, theoretical exploration
- `theory`: Theoretical contributions
- `analysis`: Analysis or evaluation
- `agent`: Agent-related changes
- `mcp`: MCP tool integration

### Scopes
**Required for:** `feat`, `fix`, `refactor`

**Common scopes:**
- `agent`, `orchestrator`, `research`, `topology`
- `constraints`, `eval`, `cli`, `web`
- `deploy`, `paths`, `hookwise`, `skills`

### Subject Rules
- **Maximum 72 characters**
- Use imperative mood: "add feature" not "added feature"
- No period at end
- Be specific and descriptive

### Examples
```
✅ Good:
feat(agent): add Skills pattern for dynamic context loading
fix(paths): update evaluation_results.json path to data/results/
docs(skills): document Skills pattern usage

❌ Bad:
fix: update path (missing scope)
feat: add new feature (too vague, missing scope)
docs: update docs (too vague, missing scope)
```

## Commit Best Practices

### Consolidation
- **Group related changes** into single commits
- **Consolidate documentation commits** when possible
- **Squash WIP commits** before merging

### Frequency
- Commit logical units of work
- Don't commit broken code
- Don't commit every single file change separately

### Branch Strategy
- Use feature branches for new features
- Keep main/master stable
- Use descriptive branch names: `feat/skills-integration`

## Workflow

### Before Committing
1. Review changes: `git diff`
2. Check status: `git status`
3. Run tests: `just test` or `uv run pytest`
4. Run linting: `just lint`

### Commit Process
1. Stage changes: `git add <files>`
2. Write commit message following conventions
3. Commit: `git commit -m "type(scope): subject"`
4. Push: `git push origin <branch>`

### After Committing
1. Verify commit: `git log -1`
2. Check hooks passed
3. Monitor CI/CD if applicable

## Usage

This skill should be loaded when:
- Analyzing git commit history
- Providing commit message recommendations
- Reviewing repository git practices
- Suggesting workflow improvements

