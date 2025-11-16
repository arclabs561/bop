# Python Best Practices Skill

**Purpose:** Guide BOP in writing high-quality Python code following best practices.

**Tags:** python, code-quality, best-practices, style

## Code Quality Rules

### Print Statements
- **Never use `print()` in production code**
- Use `logging` module instead
- Exception: `print()` is acceptable in:
  - Test files
  - `if __name__ == "__main__":` blocks
  - Debug scripts

### Error Handling
- **Never use bare `except:` clauses**
- Always specify exception types: `except ValueError:`, `except KeyError:`
- Use `except Exception as e:` only when necessary, with logging

### TODO Comments
- **TODO/FIXME/XXX/HACK must have context (≥10 characters)**
- Bad: `# TODO: fix this`
- Good: `# TODO: Refactor to use async/await for better performance`
- Include issue references when possible: `# TODO(#123): Add error handling`

### Test Patterns
- **Never use `time.sleep()` in tests**
- Use `async/await` or test utilities instead
- Use `pytest.skip()` with `reason=` parameter
- Use proper async test patterns

## Code Style

### Imports
- Group imports: stdlib, third-party, local
- Use absolute imports
- Avoid `from module import *`

### Type Hints
- Use type hints for function parameters and return values
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` for collections

### Documentation
- Use docstrings for all public functions/classes
- Follow Google or NumPy docstring style
- Include Args, Returns, Raises sections

## Performance

### Avoid Anti-patterns
- Don't use `list.append()` in tight loops (use list comprehensions)
- Don't concatenate strings in loops (use `join()`)
- Don't use `eval()` or `exec()` unless absolutely necessary

### Memory Management
- Be aware of memory leaks in long-running processes
- Use generators for large datasets
- Clean up resources (files, connections) properly

## Security

### Input Validation
- Always validate user input
- Sanitize file paths
- Use parameterized queries for databases

### Secrets
- Never commit secrets to version control
- Use environment variables for configuration
- Use `.env` files (gitignored) for local development

## Usage

This skill should be loaded when:
- Writing or reviewing Python code
- Analyzing code quality
- Providing code improvement recommendations
- Debugging Python issues

