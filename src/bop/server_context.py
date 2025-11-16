"""Request-scoped context for server requests to avoid shared state."""

from typing import Optional, Dict, Any
from contextvars import ContextVar
from .agent import KnowledgeAgent

# Context variable for per-request agent state
_request_agent: ContextVar[Optional[KnowledgeAgent]] = ContextVar('request_agent', default=None)
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_agent(base_agent: KnowledgeAgent) -> KnowledgeAgent:
    """
    Get a request-scoped agent context.
    
    Creates a lightweight wrapper that isolates conversation state
    while sharing expensive resources (LLM service, research agent, etc.).
    """
    agent = _request_agent.get()
    if agent is None:
        # Create request-scoped agent with isolated state
        # Share expensive resources but isolate conversation state
        agent = RequestScopedAgent(base_agent)
        _request_agent.set(agent)
    return agent


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Set current request ID."""
    _request_id.set(request_id)


class RequestScopedAgent:
    """
    Request-scoped agent wrapper that isolates conversation state.
    
    Shares expensive resources (LLM service, research agent) but
    maintains isolated conversation history, beliefs, and queries.
    """
    
    def __init__(self, base_agent: KnowledgeAgent):
        """Initialize with base agent (shares resources)."""
        # Store reference to base agent
        self._base_agent = base_agent
        
        # Share expensive resources
        self.research_agent = base_agent.research_agent
        self.llm_service = base_agent.llm_service
        self.orchestrator = base_agent.orchestrator
        self.content_dir = base_agent.content_dir
        self.knowledge_base = base_agent.knowledge_base
        self.quality_feedback = base_agent.quality_feedback
        self.adaptive_manager = base_agent.adaptive_manager
        self.knowledge_tracker = base_agent.knowledge_tracker  # Shared (has locks)
        
        # Isolated state per request
        self.conversation_history: list = []
        self.prior_beliefs: list = []
        self.recent_queries: list = []
    
    async def chat(
        self,
        message: str,
        use_schema: Optional[str] = None,
        use_research: bool = False,
    ) -> Dict[str, Any]:
        """Delegate to base agent but with isolated state."""
        # Store reference to base agent
        base_agent = self._base_agent
        
        # Temporarily replace base agent's state with our isolated state
        original_history = base_agent.conversation_history
        original_beliefs = base_agent.prior_beliefs
        original_queries = base_agent.recent_queries
        
        try:
            # Swap in isolated state
            base_agent.conversation_history = self.conversation_history
            base_agent.prior_beliefs = self.prior_beliefs
            base_agent.recent_queries = self.recent_queries
            
            # Call base agent
            response = await base_agent.chat(
                message=message,
                use_schema=use_schema,
                use_research=use_research,
            )
            
            # Update our isolated state
            self.conversation_history = base_agent.conversation_history
            self.prior_beliefs = base_agent.prior_beliefs
            self.recent_queries = base_agent.recent_queries
            
            return response
        finally:
            # Restore original state
            base_agent.conversation_history = original_history
            base_agent.prior_beliefs = original_beliefs
            base_agent.recent_queries = original_queries

