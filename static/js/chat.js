// Modern chat interface JavaScript

const API_BASE = window.location.origin;
const API_KEY = localStorage.getItem('bop_api_key') || '';

let isSending = false;

// DOM elements
const chatContainer = document.getElementById('chatContainer');
const messagesDiv = document.getElementById('messages');
const welcomeMessage = document.getElementById('welcomeMessage');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const researchToggle = document.getElementById('researchToggle');
const schemaSelect = document.getElementById('schemaSelect');
const loadingIndicator = document.getElementById('loadingIndicator');

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

// Send on Enter (Shift+Enter for new line)
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Set query from example
function setQuery(query) {
    messageInput.value = query;
    messageInput.focus();
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isSending) return;

    // Hide welcome message
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }

    // Add user message
    addMessage('user', message);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Disable input
    setInputEnabled(false);
    showLoading(true);

    try {
        // Show thinking message
        const thinkingId = addMessage('assistant', 'Thinking...', { thinking: true });

        // Make API call
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(API_KEY && { 'X-API-Key': API_KEY }),
            },
            body: JSON.stringify({
                message: message,
                research: researchToggle.checked,
                schema_name: schemaSelect.value || null,
            }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        
        // Update thinking message with actual response and enhanced knowledge display
        updateMessage(thinkingId, 'assistant', data.response, {
            research_conducted: data.research_conducted,
            schema_used: data.schema_used,
            quality_score: data.quality_score,
            tools_called: data.tools_called,
            // Enhanced knowledge display data
            response_tiers: data.response_tiers,
            source_matrix: data.source_matrix,
            topology_metrics: data.topology_metrics,
            token_importance: data.token_importance,
            prior_beliefs: data.prior_beliefs,
            // Temporal data
            timestamp: data.timestamp,
            source_timestamps: data.source_timestamps,
            temporal_evolution: data.temporal_evolution,
            // Session-level temporal data
            session_knowledge: data.session_knowledge,
            cross_session_evolution: data.cross_session_evolution,
            session_concepts: data.session_concepts,
        });

    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', `Error: ${error.message}`, { error: true });
    } finally {
        setInputEnabled(true);
        showLoading(false);
        messageInput.focus();
    }
}

// Add message to chat
function addMessage(role, content, metadata = {}) {
    const messageId = Date.now() + Math.random();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = `message-${messageId}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🧠';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = content;
    
    contentDiv.appendChild(textDiv);
    
    // Add metadata if available
    if (!metadata.thinking && !metadata.error && (metadata.research_conducted || metadata.schema_used || metadata.quality_score)) {
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'message-metadata';
        
        if (metadata.research_conducted) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = '🔍 Research';
            metadataDiv.appendChild(badge);
        }
        
        if (metadata.schema_used) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = `📋 ${metadata.schema_used.replace(/_/g, ' ')}`;
            metadataDiv.appendChild(badge);
        }
        
        if (metadata.quality_score) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = `⭐ ${metadata.quality_score.toFixed(2)}`;
            metadataDiv.appendChild(badge);
        }
        
        if (metadata.tools_called) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = `🛠️ ${metadata.tools_called} tools`;
            metadataDiv.appendChild(badge);
        }
        
        contentDiv.appendChild(metadataDiv);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    messagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
    
    return messageId;
}

// Update existing message with enhanced knowledge display
function updateMessage(messageId, role, content, metadata = {}) {
    const messageDiv = document.getElementById(`message-${messageId}`);
    if (!messageDiv) return;
    
    const contentDiv = messageDiv.querySelector('.message-content');
    if (!contentDiv) return;
    
    // Clear existing content
    contentDiv.innerHTML = '';
    
    // Progressive disclosure: Use response_tiers if available
    const responseTiers = metadata.response_tiers;
    let displayContent = content;
    let hasTiers = false;
    
    if (responseTiers && responseTiers.summary) {
        hasTiers = true;
        displayContent = responseTiers.summary; // Start with summary (progressive disclosure)
    }
    
    // Create text div with markdown support
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMarkdown(displayContent);
    contentDiv.appendChild(textDiv);
    
    // Add progressive disclosure controls if tiers available
    if (hasTiers && (responseTiers.detailed || responseTiers.structured || responseTiers.evidence)) {
        const tierControls = document.createElement('div');
        tierControls.className = 'tier-controls';
        
        const expandBtn = document.createElement('button');
        expandBtn.className = 'tier-toggle';
        expandBtn.textContent = 'Show more details';
        expandBtn.setAttribute('aria-label', 'Expand to show full response');
        expandBtn.onclick = () => toggleTierExpansion(messageId, responseTiers, expandBtn);
        
        tierControls.appendChild(expandBtn);
        contentDiv.appendChild(tierControls);
        
        // Store tiers for expansion
        messageDiv.dataset.responseTiers = JSON.stringify(responseTiers);
        messageDiv.dataset.expanded = 'false';
    }
    
    // Add source matrix visualization if available
    if (metadata.source_matrix && Object.keys(metadata.source_matrix).length > 0) {
        const sourceMatrixDiv = createSourceMatrixVisualization(metadata.source_matrix);
        contentDiv.appendChild(sourceMatrixDiv);
    }
    
    // Add trust/credibility visualization if topology metrics available
    if (metadata.topology_metrics) {
        const trustDiv = createTrustVisualization(metadata.topology_metrics);
        if (trustDiv) {
            contentDiv.appendChild(trustDiv);
        }
    }
    
    // Add token importance visualization if available
    if (metadata.token_importance && metadata.token_importance.term_importance) {
        const tokenDiv = createTokenImportanceVisualization(metadata.token_importance);
        contentDiv.appendChild(tokenDiv);
    }
    
    // Add prior beliefs alignment if available
    if (metadata.prior_beliefs && metadata.prior_beliefs.length > 0) {
        const beliefsDiv = createBeliefAlignmentVisualization(metadata.prior_beliefs);
        contentDiv.appendChild(beliefsDiv);
    }
    
    // Add provenance traces if source matrix available
    // This shows which sources support which claims in the response
    if (metadata.source_matrix && Object.keys(metadata.source_matrix).length > 0) {
        const provenanceDiv = createProvenanceTraces(displayContent, metadata.source_matrix);
        if (provenanceDiv) {
            contentDiv.appendChild(provenanceDiv);
        }
    }
    
    // Add temporal information visualization (query-level and session-level)
    if (metadata.timestamp || metadata.source_timestamps || metadata.temporal_evolution || 
        metadata.session_knowledge || metadata.cross_session_evolution || metadata.session_concepts) {
        const temporalDiv = createTemporalVisualization(metadata);
        if (temporalDiv) {
            contentDiv.appendChild(temporalDiv);
        }
    }
    
    // Update metadata badges
    let metadataDiv = messageDiv.querySelector('.message-metadata');
    if (!metadataDiv && (metadata.research_conducted || metadata.schema_used || metadata.quality_score)) {
        metadataDiv = document.createElement('div');
        metadataDiv.className = 'message-metadata';
        contentDiv.appendChild(metadataDiv);
    }
    
    if (metadataDiv) {
        metadataDiv.innerHTML = '';
        
        if (metadata.research_conducted) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = '🔍 Research';
            metadataDiv.appendChild(badge);
        }
        
        if (metadata.schema_used) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = `📋 ${metadata.schema_used.replace(/_/g, ' ')}`;
            metadataDiv.appendChild(badge);
        }
        
        if (metadata.quality_score) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = `⭐ ${metadata.quality_score.toFixed(2)}`;
            metadataDiv.appendChild(badge);
        }
        
        if (metadata.tools_called) {
            const badge = document.createElement('span');
            badge.className = 'metadata-badge';
            badge.innerHTML = `🛠️ ${metadata.tools_called} tools`;
            metadataDiv.appendChild(badge);
        }
    }
    
    scrollToBottom();
}

// Toggle tier expansion (progressive disclosure)
function toggleTierExpansion(messageId, responseTiers, button) {
    const messageDiv = document.getElementById(`message-${messageId}`);
    if (!messageDiv) return;
    
    const textDiv = messageDiv.querySelector('.message-text');
    if (!textDiv) return;
    
    const isExpanded = messageDiv.dataset.expanded === 'true';
    
    if (!isExpanded) {
        // Expand to detailed tier
        const detailed = responseTiers.detailed || responseTiers.structured || responseTiers.evidence || responseTiers.summary;
        textDiv.innerHTML = formatMarkdown(detailed);
        button.textContent = 'Show less';
        messageDiv.dataset.expanded = 'true';
    } else {
        // Collapse to summary
        textDiv.innerHTML = formatMarkdown(responseTiers.summary);
        button.textContent = 'Show more details';
        messageDiv.dataset.expanded = 'false';
    }
    
    scrollToBottom();
}

// Create source matrix visualization (heatmap-style)
function createSourceMatrixVisualization(sourceMatrix) {
    const container = document.createElement('div');
    container.className = 'knowledge-visualization source-matrix';
    
    const header = document.createElement('div');
    header.className = 'viz-header';
    header.innerHTML = '<h4>📊 Source Agreement Matrix</h4><p>Shows which sources agree or disagree on key claims</p>';
    container.appendChild(header);
    
    const table = document.createElement('table');
    table.className = 'source-matrix-table';
    
    // Get top claims (limit to 8 for readability)
    const claims = Object.entries(sourceMatrix)
        .sort((a, b) => Object.keys(b[1].sources || {}).length - Object.keys(a[1].sources || {}).length)
        .slice(0, 8);
    
    if (claims.length === 0) {
        container.innerHTML = '<p class="viz-empty">No source agreement data available</p>';
        return container;
    }
    
    // Collect all unique sources
    const allSources = new Set();
    claims.forEach(([_, data]) => {
        Object.keys(data.sources || {}).forEach(s => allSources.add(s));
    });
    const sources = Array.from(allSources).slice(0, 6); // Limit to 6 sources for readability
    
    // Create header row
    const headerRow = document.createElement('tr');
    const claimHeader = document.createElement('th');
    claimHeader.textContent = 'Claim';
    headerRow.appendChild(claimHeader);
    sources.forEach(source => {
        const th = document.createElement('th');
        th.textContent = source.substring(0, 15);
        th.title = source;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);
    
    // Create data rows
    claims.forEach(([claim, data]) => {
        const row = document.createElement('tr');
        
        const claimCell = document.createElement('td');
        claimCell.textContent = claim.substring(0, 40) + (claim.length > 40 ? '...' : '');
        claimCell.title = claim;
        row.appendChild(claimCell);
        
        sources.forEach(source => {
            const cell = document.createElement('td');
            const position = data.sources?.[source];
            
            if (position === 'supports') {
                cell.className = 'matrix-cell supports';
                cell.textContent = '✓';
                cell.title = `${source}: supports`;
            } else if (position === 'contradicts') {
                cell.className = 'matrix-cell contradicts';
                cell.textContent = '✗';
                cell.title = `${source}: contradicts`;
            } else if (position === 'neutral') {
                cell.className = 'matrix-cell neutral';
                cell.textContent = '○';
                cell.title = `${source}: neutral`;
            } else {
                cell.className = 'matrix-cell unknown';
                cell.textContent = '—';
                cell.title = `${source}: no data`;
            }
            
            row.appendChild(cell);
        });
        
        table.appendChild(row);
    });
    
    container.appendChild(table);
    return container;
}

// Create trust/credibility visualization
function createTrustVisualization(topology) {
    if (!topology) return null;
    
    const container = document.createElement('div');
    container.className = 'knowledge-visualization trust-metrics';
    
    const header = document.createElement('div');
    header.className = 'viz-header';
    header.innerHTML = '<h4>🛡️ Trust & Credibility</h4>';
    container.appendChild(header);
    
    const metrics = document.createElement('div');
    metrics.className = 'trust-metrics-grid';
    
    // Source credibility
    const sourceCred = topology.source_credibility;
    if (sourceCred && Object.keys(sourceCred).length > 0) {
        const credSection = document.createElement('div');
        credSection.className = 'trust-section';
        credSection.innerHTML = '<h5>Source Credibility</h5>';
        
        const credList = document.createElement('ul');
        credList.className = 'credibility-list';
        
        Object.entries(sourceCred)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .forEach(([source, score]) => {
                const li = document.createElement('li');
                
                const sourceName = document.createElement('span');
                sourceName.className = 'source-name';
                sourceName.textContent = source.substring(0, 20);
                li.appendChild(sourceName);
                
                const bar = document.createElement('div');
                bar.className = 'credibility-bar';
                const fill = document.createElement('div');
                fill.className = 'credibility-fill';
                fill.style.width = `${score * 100}%`;
                bar.appendChild(fill);
                li.appendChild(bar);
                
                const scoreSpan = document.createElement('span');
                scoreSpan.className = 'credibility-score';
                scoreSpan.textContent = score.toFixed(2);
                li.appendChild(scoreSpan);
                
                credList.appendChild(li);
            });
        
        credSection.appendChild(credList);
        metrics.appendChild(credSection);
    }
    
    // Cliques (source agreement clusters)
    const cliques = topology.cliques;
    if (cliques && cliques.length > 0) {
        const cliqueSection = document.createElement('div');
        cliqueSection.className = 'trust-section';
        cliqueSection.innerHTML = '<h5>Source Agreement Clusters</h5>';
        
        const cliqueList = document.createElement('ul');
        cliqueList.className = 'clique-list';
        
        cliques.slice(0, 3).forEach((clique, i) => {
            const li = document.createElement('li');
            const sources = clique.unique_sources || clique.node_sources || [];
            const trust = clique.trust || 0;
            
            li.innerHTML = `
                <span class="clique-label">Cluster ${i + 1}</span>
                <span class="clique-sources">${sources.slice(0, 3).join(', ')}${sources.length > 3 ? '...' : ''}</span>
                <span class="clique-trust">Trust: ${trust.toFixed(2)}</span>
            `;
            
            cliqueList.appendChild(li);
        });
        
        cliqueSection.appendChild(cliqueList);
        metrics.appendChild(cliqueSection);
    }
    
    if (metrics.children.length === 0) return null;
    
    container.appendChild(metrics);
    return container;
}

// Create token importance visualization
function createTokenImportanceVisualization(tokenData) {
    if (!tokenData.term_importance) return null;
    
    const container = document.createElement('div');
    container.className = 'knowledge-visualization token-importance';
    
    const header = document.createElement('div');
    header.className = 'viz-header';
    header.innerHTML = '<h4>🔍 Token Importance</h4><p>Key terms that influenced the response</p>';
    container.appendChild(header);
    
    const terms = Object.entries(tokenData.term_importance)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    if (terms.length === 0) {
        container.innerHTML = '<p class="viz-empty">No token importance data available</p>';
        return container;
    }
    
    const termList = document.createElement('div');
    termList.className = 'term-list';
    
    const maxImportance = Math.max(...terms.map(([_, score]) => score));
    
    terms.forEach(([term, score]) => {
        const termDiv = document.createElement('div');
        termDiv.className = 'term-item';
        
        const termName = document.createElement('span');
        termName.className = 'term-name';
        termName.textContent = term;
        termDiv.appendChild(termName);
        
        const bar = document.createElement('div');
        bar.className = 'term-bar';
        const fill = document.createElement('div');
        fill.className = 'term-fill';
        fill.style.width = `${(score / maxImportance) * 100}%`;
        bar.appendChild(fill);
        termDiv.appendChild(bar);
        
        const scoreSpan = document.createElement('span');
        scoreSpan.className = 'term-score';
        scoreSpan.textContent = score.toFixed(2);
        termDiv.appendChild(scoreSpan);
        
        termList.appendChild(termDiv);
    });
    
    container.appendChild(termList);
    return container;
}

// Create belief alignment visualization
function createBeliefAlignmentVisualization(priorBeliefs) {
    const container = document.createElement('div');
    container.className = 'knowledge-visualization belief-alignment';
    
    const header = document.createElement('div');
    header.className = 'viz-header';
    header.innerHTML = '<h4>🧠 Belief-Evidence Alignment</h4><p>Your stated beliefs and how evidence aligns</p>';
    container.appendChild(header);
    
    const beliefsList = document.createElement('ul');
    beliefsList.className = 'beliefs-list';
    
    priorBeliefs.forEach(belief => {
        const li = document.createElement('li');
        li.className = 'belief-item';
        li.innerHTML = `
            <span class="belief-text">"${belief.text.substring(0, 60)}${belief.text.length > 60 ? '...' : ''}"</span>
            <span class="belief-source">${belief.source || 'user statement'}</span>
        `;
        beliefsList.appendChild(li);
    });
    
    container.appendChild(beliefsList);
    return container;
}

// Create provenance traces visualization
// Shows which sources support which claims in the response text
function createProvenanceTraces(responseText, sourceMatrix) {
    if (!responseText || !sourceMatrix) return null;
    
    const container = document.createElement('div');
    container.className = 'knowledge-visualization provenance-traces';
    
    const header = document.createElement('div');
    header.className = 'viz-header';
    header.innerHTML = '<h4>🔗 Provenance Traces</h4><p>Click on claims to see which sources support them</p>';
    container.appendChild(header);
    
    // Find claims in source matrix that appear in response text
    const traces = [];
    const responseLower = responseText.toLowerCase();
    
    Object.entries(sourceMatrix).forEach(([claim, data]) => {
        const claimLower = claim.toLowerCase();
        // Check if claim or key phrases appear in response
        if (responseLower.includes(claimLower) || 
            claimLower.split(' ').some(word => word.length > 4 && responseLower.includes(word))) {
            const sources = data.sources || {};
            const supporting = Object.entries(sources)
                .filter(([_, pos]) => pos === 'supports')
                .map(([source, _]) => source);
            const contradicting = Object.entries(sources)
                .filter(([_, pos]) => pos === 'contradicts')
                .map(([source, _]) => source);
            
            if (supporting.length > 0 || contradicting.length > 0) {
                traces.push({
                    claim: claim.substring(0, 60) + (claim.length > 60 ? '...' : ''),
                    fullClaim: claim,
                    supporting: supporting,
                    contradicting: contradicting,
                });
            }
        }
    });
    
    if (traces.length === 0) {
        container.innerHTML = '<p class="viz-empty">No provenance traces found (claims may not match response text)</p>';
        return container;
    }
    
    const tracesList = document.createElement('ul');
    tracesList.className = 'provenance-list';
    
    traces.slice(0, 5).forEach(trace => {
        const li = document.createElement('li');
        li.className = 'provenance-item';
        
        const claimDiv = document.createElement('div');
        claimDiv.className = 'provenance-claim';
        claimDiv.textContent = trace.claim;
        claimDiv.title = trace.fullClaim;
        li.appendChild(claimDiv);
        
        if (trace.supporting.length > 0) {
            const supportsDiv = document.createElement('div');
            supportsDiv.className = 'provenance-sources supports';
            supportsDiv.innerHTML = `<span class="provenance-label">Supports:</span> ${trace.supporting.slice(0, 3).join(', ')}${trace.supporting.length > 3 ? '...' : ''}`;
            li.appendChild(supportsDiv);
        }
        
        if (trace.contradicting.length > 0) {
            const contradictsDiv = document.createElement('div');
            contradictsDiv.className = 'provenance-sources contradicts';
            contradictsDiv.innerHTML = `<span class="provenance-label">Contradicts:</span> ${trace.contradicting.slice(0, 3).join(', ')}${trace.contradicting.length > 3 ? '...' : ''}`;
            li.appendChild(contradictsDiv);
        }
        
        tracesList.appendChild(li);
    });
    
    container.appendChild(tracesList);
    return container;
}

// Create temporal visualization (timeline, staleness, evolution)
function createTemporalVisualization(metadata) {
    const container = document.createElement('div');
    container.className = 'knowledge-visualization temporal-info';
    
    const header = document.createElement('div');
    header.className = 'viz-header';
    header.innerHTML = '<h4>⏱️ Temporal Information</h4><p>When information was generated and how it evolved (query-level and across sessions)</p>';
    container.appendChild(header);
    
    const temporalContent = document.createElement('div');
    temporalContent.className = 'temporal-content';
    
    // Show response timestamp
    if (metadata.timestamp) {
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'temporal-item';
        const timestamp = new Date(metadata.timestamp);
        const now = new Date();
        const ageMs = now - timestamp;
        const ageMinutes = Math.floor(ageMs / 60000);
        const ageHours = Math.floor(ageMs / 3600000);
        const ageDays = Math.floor(ageMs / 86400000);
        
        let ageText = 'just now';
        if (ageDays > 0) {
            ageText = `${ageDays} day${ageDays > 1 ? 's' : ''} ago`;
        } else if (ageHours > 0) {
            ageText = `${ageHours} hour${ageHours > 1 ? 's' : ''} ago`;
        } else if (ageMinutes > 0) {
            ageText = `${ageMinutes} minute${ageMinutes > 1 ? 's' : ''} ago`;
        }
        
        timestampDiv.innerHTML = `
            <span class="temporal-label">Response generated:</span>
            <span class="temporal-value">${timestamp.toLocaleString()}</span>
            <span class="temporal-age">(${ageText})</span>
        `;
        temporalContent.appendChild(timestampDiv);
    }
    
    // Show source timestamps
    if (metadata.source_timestamps && Object.keys(metadata.source_timestamps).length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'temporal-item';
        sourcesDiv.innerHTML = '<span class="temporal-label">Source access times:</span>';
        
        const sourcesList = document.createElement('ul');
        sourcesList.className = 'source-timestamps-list';
        
        Object.entries(metadata.source_timestamps).slice(0, 5).forEach(([source, timestamp]) => {
            const li = document.createElement('li');
            const sourceTime = new Date(timestamp);
            li.innerHTML = `
                <span class="source-name">${source.substring(0, 25)}</span>
                <span class="source-time">${sourceTime.toLocaleString()}</span>
            `;
            sourcesList.appendChild(li);
        });
        
        sourcesDiv.appendChild(sourcesList);
        temporalContent.appendChild(sourcesDiv);
    }
    
    // Show temporal evolution
    if (metadata.temporal_evolution && metadata.temporal_evolution.length > 0) {
        const evolutionDiv = document.createElement('div');
        evolutionDiv.className = 'temporal-item';
        evolutionDiv.innerHTML = '<span class="temporal-label">Knowledge Evolution:</span>';
        
        const evolutionList = document.createElement('ul');
        evolutionList.className = 'evolution-list';
        
        metadata.temporal_evolution.forEach((item, i) => {
            const li = document.createElement('li');
            li.className = 'evolution-item';
            
            const claimDiv = document.createElement('div');
            claimDiv.className = 'evolution-claim';
            claimDiv.textContent = item.claim;
            claimDiv.title = item.full_claim;
            li.appendChild(claimDiv);
            
            const metaDiv = document.createElement('div');
            metaDiv.className = 'evolution-meta';
            
            if (item.consensus !== null && item.consensus !== undefined) {
                const consensusSpan = document.createElement('span');
                consensusSpan.className = 'evolution-consensus';
                consensusSpan.textContent = `Consensus: ${(item.consensus * 100).toFixed(0)}%`;
                metaDiv.appendChild(consensusSpan);
            }
            
            if (item.conflict) {
                const conflictSpan = document.createElement('span');
                conflictSpan.className = 'evolution-conflict';
                conflictSpan.textContent = '⚠️ Conflicts detected';
                metaDiv.appendChild(conflictSpan);
            }
            
            const sourceCountSpan = document.createElement('span');
            sourceCountSpan.className = 'evolution-sources';
            sourceCountSpan.textContent = `${item.source_count} source${item.source_count !== 1 ? 's' : ''}`;
            metaDiv.appendChild(sourceCountSpan);
            
            li.appendChild(metaDiv);
            evolutionList.appendChild(li);
        });
        
        evolutionDiv.appendChild(evolutionList);
        temporalContent.appendChild(evolutionDiv);
    }
    
    // Show session-level knowledge evolution
    if (metadata.session_knowledge) {
        const sessionDiv = document.createElement('div');
        sessionDiv.className = 'temporal-item';
        sessionDiv.innerHTML = '<span class="temporal-label">Session Knowledge:</span>';
        
        const sessionInfo = document.createElement('div');
        sessionInfo.className = 'session-knowledge-info';
        
        const session = metadata.session_knowledge;
        const learnedCount = session.concepts_learned ? session.concepts_learned.length : 0;
        const refinedCount = session.concepts_refined ? session.concepts_refined.length : 0;
        
        sessionInfo.innerHTML = `
            <div class="session-stats">
                <span>📚 Concepts learned: ${learnedCount}</span>
                <span>🔄 Concepts refined: ${refinedCount}</span>
                <span>💬 Queries: ${session.query_count || 0}</span>
            </div>
        `;
        
        if (session.concepts_learned && session.concepts_learned.length > 0) {
            const learnedList = document.createElement('ul');
            learnedList.className = 'concepts-list';
            session.concepts_learned.slice(0, 5).forEach(concept => {
                const li = document.createElement('li');
                li.textContent = `✨ ${concept}`;
                learnedList.appendChild(li);
            });
            sessionInfo.appendChild(learnedList);
        }
        
        sessionDiv.appendChild(sessionInfo);
        temporalContent.appendChild(sessionDiv);
    }
    
    // Show cross-session evolution
    if (metadata.cross_session_evolution && metadata.cross_session_evolution.length > 0) {
        const crossSessionDiv = document.createElement('div');
        crossSessionDiv.className = 'temporal-item';
        crossSessionDiv.innerHTML = '<span class="temporal-label">Knowledge Evolution Across Sessions:</span>';
        
        const evolutionList = document.createElement('ul');
        evolutionList.className = 'cross-session-evolution-list';
        
        metadata.cross_session_evolution.forEach(item => {
            const li = document.createElement('li');
            li.className = 'cross-session-item';
            
            const firstDate = new Date(item.first_learned_at);
            const lastDate = new Date(item.last_updated_at);
            const daysSinceFirst = Math.floor((new Date() - firstDate) / (1000 * 60 * 60 * 24));
            const daysSinceLast = Math.floor((new Date() - lastDate) / (1000 * 60 * 60 * 24));
            
            li.innerHTML = `
                <div class="concept-name">${item.concept}</div>
                <div class="concept-timeline">
                    <span>First learned: ${daysSinceFirst} day${daysSinceFirst !== 1 ? 's' : ''} ago</span>
                    <span>Last updated: ${daysSinceLast} day${daysSinceLast !== 1 ? 's' : ''} ago</span>
                    <span>Across ${item.session_count} session${item.session_count !== 1 ? 's' : ''}</span>
                    ${item.recent_confidence ? `<span>Recent confidence: ${(item.recent_confidence * 100).toFixed(0)}%</span>` : ''}
                </div>
            `;
            evolutionList.appendChild(li);
        });
        
        crossSessionDiv.appendChild(evolutionList);
        temporalContent.appendChild(crossSessionDiv);
    }
    
    // Show concepts in this session
    if (metadata.session_concepts && metadata.session_concepts.concepts) {
        const conceptsDiv = document.createElement('div');
        conceptsDiv.className = 'temporal-item';
        conceptsDiv.innerHTML = '<span class="temporal-label">Concepts in This Session:</span>';
        
        const conceptsList = document.createElement('ul');
        conceptsList.className = 'session-concepts-list';
        
        metadata.session_concepts.concepts.forEach(item => {
            const li = document.createElement('li');
            li.className = 'session-concept-item';
            
            const firstDate = new Date(item.first_learned_at);
            const daysSinceFirst = Math.floor((new Date() - firstDate) / (1000 * 60 * 60 * 24));
            
            let status = '';
            if (item.was_new) {
                status = '✨ New';
            } else if (item.was_refined) {
                status = '🔄 Refined';
            }
            
            li.innerHTML = `
                <div class="concept-name">${item.concept} ${status}</div>
                <div class="concept-meta">
                    <span>First learned: ${daysSinceFirst} day${daysSinceFirst !== 1 ? 's' : ''} ago</span>
                    <span>Appeared in ${item.total_sessions} session${item.total_sessions !== 1 ? 's' : ''}</span>
                </div>
            `;
            conceptsList.appendChild(li);
        });
        
        conceptsDiv.appendChild(conceptsList);
        temporalContent.appendChild(conceptsDiv);
    }
    
    if (temporalContent.children.length === 0) {
        container.innerHTML = '<p class="viz-empty">No temporal information available</p>';
        return container;
    }
    
    container.appendChild(temporalContent);
    return container;
}

// Simple markdown formatter (basic support)
function formatMarkdown(text) {
    if (!text) return '';
    
    // Escape HTML first
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// Scroll to bottom
function scrollToBottom() {
    setTimeout(() => {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth',
        });
    }, 100);
}

// Set input enabled/disabled
function setInputEnabled(enabled) {
    isSending = !enabled;
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    researchToggle.disabled = !enabled;
    schemaSelect.disabled = !enabled;
}

// Show/hide loading indicator
function showLoading(show) {
    if (loadingIndicator) {
        loadingIndicator.style.display = show ? 'flex' : 'none';
        if (show) {
            loadingIndicator.setAttribute('aria-busy', 'true');
            // Update loading text based on state
            const loadingText = loadingIndicator.querySelector('.loading-text');
            if (loadingText) {
                loadingText.textContent = researchToggle?.checked 
                    ? 'Researching and thinking...' 
                    : 'Thinking...';
            }
        } else {
            loadingIndicator.setAttribute('aria-busy', 'false');
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    messageInput.focus();
    
    // Check if API key is needed
    if (!API_KEY) {
        // Try to get from health check
        fetch(`${API_BASE}/health`)
            .then(res => res.json())
            .then(data => {
                console.log('API health check:', data);
            })
            .catch(err => {
                console.error('Health check failed:', err);
            });
    }
});

