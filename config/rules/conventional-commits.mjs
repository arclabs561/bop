/**
 * Custom conventional commits rules for BOP project
 * 
 * Adds BOP-specific commit types for research and theoretical work.
 */

// Standard types + BOP-specific types
export const CONVENTIONAL_TYPES = [
  'feat',      // New feature
  'fix',       // Bug fix
  'docs',      // Documentation
  'style',     // Code style (formatting, etc.)
  'refactor',  // Code refactoring
  'perf',      // Performance improvement
  'test',      // Tests
  'chore',     // Maintenance tasks
  // BOP-specific types
  'research', // Research work, theoretical exploration
  'theory',    // Theoretical contributions
  'analysis',  // Analysis or evaluation
  'agent',     // Agent-related changes
  'mcp',       // MCP tool integration
];

export function validateFormat(message) {
  if (!message || message.trim().length === 0) {
    return { 
      valid: false, 
      error: 'Commit message cannot be empty' 
    };
  }
  
  // Check for WIP commits (auto-allow)
  const wipPattern = /^(wip|WIP|\[wip\]|\[WIP\])\s*:?/i;
  if (wipPattern.test(message.trim())) {
    return { valid: true, wip: true };
  }
  
  // Check for conventional commits format: type(scope): subject
  const typeMatch = message.match(/^(\w+)(?:\(([^)]+)\))?\s*:\s*(.+)$/);
  if (!typeMatch) {
    return { 
      valid: false, 
      error: 'Must follow format: type(scope): subject\n' +
             'Example: feat(agent): add belief-evidence alignment\n' +
             'Types: ' + CONVENTIONAL_TYPES.join(', ')
    };
  }
  
  const type = typeMatch[1].toLowerCase();
  const scope = typeMatch[2] || '';
  const subject = typeMatch[3].trim();
  
  // Validate type
  if (!CONVENTIONAL_TYPES.includes(type)) {
    return { 
      valid: false, 
      error: `Type "${type}" not recognized. Must be one of: ${CONVENTIONAL_TYPES.join(', ')}` 
    };
  }
  
  // Validate subject (not empty, reasonable length)
  if (subject.length === 0) {
    return { 
      valid: false, 
      error: 'Subject cannot be empty' 
    };
  }
  
  if (subject.length > 72) {
    return { 
      valid: false, 
      error: `Subject too long (${subject.length} chars, max 72). Keep it concise.` 
    };
  }
  
  // BOP-specific guidance
  const suggestions = [];
  if (type === 'research' && !subject.toLowerCase().includes('research') && !subject.toLowerCase().includes('explore')) {
    suggestions.push('Consider mentioning the research aspect or question');
  }
  if (type === 'theory' && !subject.toLowerCase().match(/(theory|theoretical|concept|framework)/)) {
    suggestions.push('Consider mentioning the theoretical contribution');
  }
  if (type === 'mcp' && !subject.toLowerCase().match(/(mcp|tool|integration)/)) {
    suggestions.push('Consider mentioning which MCP tool or integration');
  }
  if (type === 'agent' && !scope && !subject.toLowerCase().match(/(agent|orchestrator|research)/)) {
    suggestions.push('Consider adding scope (e.g., agent(KnowledgeAgent)) or mentioning agent component');
  }
  if (type === 'analysis' && !subject.toLowerCase().match(/(analysis|evaluate|analyze|study)/)) {
    suggestions.push('Consider mentioning what is being analyzed or evaluated');
  }
  
  // Scope recommendations for major types
  if (['feat', 'fix', 'refactor'].includes(type) && !scope) {
    const commonScopes = ['agent', 'orchestrator', 'research', 'topology', 'constraints', 'eval', 'cli', 'web'];
    suggestions.push(`Consider adding scope (e.g., ${type}(${commonScopes[0]}): ...) for better organization`);
  }
  
  return { 
    valid: true, 
    type, 
    scope, 
    subject,
    suggestions: suggestions.length > 0 ? suggestions : undefined
  };
}

