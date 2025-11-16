# Code Quality Skill

**Purpose:** Guide BOP in evaluating and improving code quality across multiple dimensions.

**Tags:** code-quality, review, best-practices, maintainability

## Quality Dimensions

### 1. Readability
- **Clear naming:** Variables, functions, classes have descriptive names
- **Consistent style:** Follow project style guide
- **Appropriate comments:** Explain why, not what
- **Logical structure:** Code flows naturally

### 2. Maintainability
- **Modularity:** Functions/classes have single responsibility
- **DRY principle:** Don't Repeat Yourself
- **Low coupling:** Minimal dependencies between modules
- **High cohesion:** Related code grouped together

### 3. Testability
- **Testable design:** Functions are easy to test
- **Test coverage:** Critical paths have tests
- **Test quality:** Tests are clear and maintainable
- **Mocking:** External dependencies can be mocked

### 4. Performance
- **Efficient algorithms:** Appropriate complexity
- **Resource usage:** Memory, CPU usage reasonable
- **Scalability:** Handles expected load
- **Bottlenecks:** Identified and optimized

### 5. Security
- **Input validation:** All inputs validated
- **No secrets:** No hardcoded credentials
- **Safe defaults:** Secure by default
- **Error handling:** Errors don't leak information

## Code Smells

### Common Issues
1. **Long functions** (>50 lines) - Break into smaller functions
2. **Deep nesting** (>3 levels) - Extract functions or use early returns
3. **Magic numbers** - Use named constants
4. **Duplicate code** - Extract to shared functions
5. **God objects** - Split into smaller, focused classes
6. **Feature envy** - Move methods to appropriate classes
7. **Data clumps** - Group related data into objects

### Python-Specific
- **Bare except clauses** - Specify exception types
- **Mutable default arguments** - Use `None` and assign in function
- **Import * statements** - Use explicit imports
- **Global variables** - Pass as parameters
- **Print statements** - Use logging

## Review Checklist

### Function Level
- [ ] Single responsibility
- [ ] Clear name
- [ ] Appropriate length (<50 lines)
- [ ] Type hints
- [ ] Docstring
- [ ] Error handling
- [ ] Testable

### Class Level
- [ ] Single responsibility
- [ ] Clear name
- [ ] Appropriate size
- [ ] Low coupling
- [ ] High cohesion
- [ ] Proper encapsulation

### Module Level
- [ ] Clear purpose
- [ ] Appropriate organization
- [ ] Minimal dependencies
- [ ] Well-documented
- [ ] Testable

## Improvement Recommendations

When suggesting improvements:
1. **Prioritize:** High/Medium/Low impact
2. **Be specific:** Exact locations, line numbers
3. **Explain why:** Context for recommendations
4. **Provide examples:** Show before/after
5. **Actionable:** Clear steps to fix

## Usage

This skill should be loaded when:
- Reviewing code quality
- Analyzing code structure
- Providing improvement recommendations
- Evaluating maintainability

