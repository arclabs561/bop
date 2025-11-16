"""Integration tests for LLM capabilities with actual LLM service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from bop.llm import LLMService
from bop.llm_capabilities import BaseCapabilityAdapter


class TestLLMServiceCapabilities:
    """Test LLMService capability integration."""

    @pytest.mark.asyncio
    async def test_capability_info(self):
        """Test that capability info is accessible."""
        # Mock LLM service to avoid requiring API keys
        with patch('bop.llm.LLMService._detect_backend', return_value='openai'):
            with patch('bop.llm.LLMService._create_model') as mock_create:
                with patch('bop.llm.Agent') as mock_agent:
                    mock_model = Mock()
                    mock_model.model_name = "gpt-4o"
                    mock_create.return_value = mock_model
                    mock_agent_instance = Mock()
                    mock_agent.return_value = mock_agent_instance
                    
                    service = LLMService(backend="openai")
                    
                    # Check capability info
                    info = service.get_capability_info()
                    assert "backend" in info
                    assert "supports_embeddings" in info
                    assert "supports_vision" in info
                    assert "supports_logprobs" in info
                    assert info["backend"] == "openai"

    @pytest.mark.asyncio
    async def test_compute_similarity_fallback(self):
        """Test similarity computation with fallback."""
        with patch('bop.llm.LLMService._detect_backend', return_value='openai'):
            with patch('bop.llm.LLMService._create_model') as mock_create:
                with patch('bop.llm.Agent') as mock_agent:
                    mock_model = Mock()
                    mock_model.model_name = "gpt-4o"
                    mock_create.return_value = mock_model
                    mock_agent_instance = Mock()
                    mock_agent.return_value = mock_agent_instance
                    
                    service = LLMService(backend="openai")
                    
                    # Should use keyword similarity since embeddings not supported
                    similarity = await service.compute_similarity(
                        "hello world",
                        "hello",
                        use_embedding=False
                    )
                    assert 0.0 <= similarity <= 1.0
                    
                    # Test with embedding attempt (will fallback)
                    similarity2 = await service.compute_similarity(
                        "hello world",
                        "hello",
                        use_embedding=True
                    )
                    assert 0.0 <= similarity2 <= 1.0

    def test_capability_properties(self):
        """Test capability property access."""
        with patch('bop.llm.LLMService._detect_backend', return_value='openai'):
            with patch('bop.llm.LLMService._create_model') as mock_create:
                with patch('bop.llm.Agent') as mock_agent:
                    mock_model = Mock()
                    mock_model.model_name = "gpt-4o"
                    mock_create.return_value = mock_model
                    mock_agent_instance = Mock()
                    mock_agent.return_value = mock_agent_instance
                    
                    service = LLMService(backend="openai")
                    
                    # All properties should be accessible
                    assert isinstance(service.supports_embeddings, bool)
                    assert isinstance(service.supports_vision, bool)
                    assert isinstance(service.supports_logprobs, bool)
                    assert isinstance(service.supports_input_params, bool)

    def test_vision_input_types(self):
        """Test vision input types for different backends."""
        test_cases = [
            ("openai", "gpt-4o", True),
            ("openai", "gpt-3.5-turbo", False),
            ("anthropic", "claude-3-5-sonnet", True),
            ("google", "gemini-1.5-pro", True),
        ]
        
        for backend, model_name, should_support_vision in test_cases:
            with patch('bop.llm.LLMService._detect_backend', return_value=backend):
                with patch('bop.llm.LLMService._create_model') as mock_create:
                    with patch('bop.llm.Agent') as mock_agent:
                        mock_model = Mock()
                        mock_model.model_name = model_name
                        mock_create.return_value = mock_model
                        mock_agent_instance = Mock()
                        mock_agent.return_value = mock_agent_instance
                        
                        service = LLMService(backend=backend)
                        vision_types = service.get_vision_input_types()
                        
                        if should_support_vision:
                            assert len(vision_types) > 0
                            assert "image/jpeg" in vision_types or "image/png" in vision_types
                        else:
                            assert len(vision_types) == 0

    def test_custom_input_params(self):
        """Test custom input parameters for different backends."""
        with patch('bop.llm.LLMService._detect_backend', return_value='openai'):
            with patch('bop.llm.LLMService._create_model') as mock_create:
                with patch('bop.llm.Agent') as mock_agent:
                    mock_model = Mock()
                    mock_create.return_value = mock_model
                    mock_agent_instance = Mock()
                    mock_agent.return_value = mock_agent_instance
                    
                    service = LLMService(backend="openai")
                    params = service.get_custom_input_params()
                    
                    # Should have common params
                    assert "temperature" in params
                    assert "max_tokens" in params
                    assert "top_p" in params
                    
                    # OpenAI-specific params
                    assert "frequency_penalty" in params
                    assert "presence_penalty" in params


class TestOrchestratorIntegration:
    """Test orchestrator integration with capabilities."""

    @pytest.mark.asyncio
    async def test_belief_alignment_with_capabilities(self):
        """Test that orchestrator uses capabilities for belief alignment."""
        from bop.orchestrator import StructuredOrchestrator
        from bop.research import ResearchAgent
        
        with patch('bop.llm.LLMService._detect_backend', return_value='openai'):
            with patch('bop.llm.LLMService._create_model') as mock_create:
                with patch('bop.llm.Agent') as mock_agent:
                    mock_model = Mock()
                    mock_model.model_name = "gpt-4o"
                    mock_create.return_value = mock_model
                    mock_agent_instance = Mock()
                    mock_agent.return_value = mock_agent_instance
                    
                    llm_service = LLMService(backend="openai")
                    orchestrator = StructuredOrchestrator(
                        research_agent=ResearchAgent(),
                        llm_service=llm_service,
                    )
                    
                    # Test belief alignment
                    alignment = await orchestrator._compute_belief_alignment(
                        "Trust is important for knowledge systems",
                        [{"text": "I think trust is crucial"}]
                    )
                    
                    assert 0.0 <= alignment <= 1.0
                    
                    # Test with no beliefs
                    alignment2 = await orchestrator._compute_belief_alignment(
                        "Some evidence text",
                        []
                    )
                    assert alignment2 == 0.5  # Neutral

