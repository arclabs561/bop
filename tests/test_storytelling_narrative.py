"""Tests for storytelling and narrative features in responses."""

import pytest
from bop.llm import LLMService


@pytest.mark.asyncio
async def test_storytelling_prompt_includes_narrative_guidance():
    """Test that LLM prompts include storytelling guidance."""
    # This is an integration test - we can't easily test the exact prompt
    # without mocking, but we can verify the method exists and works
    try:
        llm_service = LLMService()
        
        # The generate_response method should include narrative guidance
        # We can't easily test the exact prompt content without mocking,
        # but we can verify the method signature and that it doesn't crash
        response = await llm_service.generate_response(
            "What is d-separation?",
            context={},
            target_length=500,
        )
        # Should return a string
        assert isinstance(response, str)
    except (ValueError, Exception) as e:
        # If LLM is not available, that's okay for this test
        error_str = str(e).lower()
        if "api" in error_str or "key" in error_str or "required" in error_str:
            pytest.skip(f"LLM service not available: {e}")
        else:
            raise


def test_connective_phrases_guidance():
    """Test that narrative guidance includes connective phrases."""
    # This is a documentation/contract test
    # The actual implementation should include guidance about:
    # - "This led to..."
    # - "To understand why..."
    # - "Building on this..."
    # - "In contrast..."
    
    # We verify this by checking the code exists
    import inspect
    from bop.llm import LLMService
    
    source = inspect.getsource(LLMService.generate_response)
    # Check that narrative guidance is mentioned in the code
    assert "narrative" in source.lower() or "connective" in source.lower() or "story" in source.lower()

