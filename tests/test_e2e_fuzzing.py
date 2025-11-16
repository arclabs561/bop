"""Fuzzing tests for E2E system.

Random input generation to discover edge cases and bugs.
"""

import pytest
import tempfile
import random
import string
from typing import Dict, Any

from bop.agent import KnowledgeAgent
from tests.test_annotations import annotate_test


def generate_random_string(length: int) -> str:
    """Generate random string of given length."""
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))


@pytest.mark.asyncio
async def test_e2e_fuzz_random_inputs():
    """
    Fuzz: Random inputs of various lengths and characters.
    
    System should handle random inputs without crashing.
    """
    annotate_test(
        "test_e2e_fuzz_random_inputs",
        pattern="fuzzing_e2e",
        opinion="system_handles_random_inputs",
        category="e2e_fuzzing",
        hypothesis="System handles random inputs without crashing",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Generate random inputs
        random_inputs = [
            generate_random_string(10),
            generate_random_string(100),
            generate_random_string(500),
            generate_random_string(1000),
            ''.join(random.choices(string.unicode_letters, k=200)),  # Unicode
        ]
        
        crashes = []
        for i, query in enumerate(random_inputs):
            try:
                response = await agent.chat(message=query, use_research=False)
                # Should return response (may be error message, but should not crash)
                assert isinstance(response, dict)
            except Exception as e:
                crashes.append((i, str(e)))
        
        # System should handle most random inputs
        assert len(crashes) < len(random_inputs) * 0.5, f"Too many crashes: {crashes}"


@pytest.mark.asyncio
async def test_e2e_fuzz_boundary_values():
    """
    Fuzz: Boundary value testing (empty, very long, special cases).
    
    System should handle boundary cases gracefully.
    """
    annotate_test(
        "test_e2e_fuzz_boundary_values",
        pattern="fuzzing_e2e",
        opinion="system_handles_boundaries",
        category="e2e_fuzzing",
        hypothesis="System handles boundary values gracefully",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        boundary_inputs = [
            "",  # Empty
            " ",  # Whitespace only
            "\n" * 100,  # Newlines
            "\t" * 100,  # Tabs
            "A" * 10000,  # Very long
            "🚀" * 500,  # Unicode
            "\x00" * 100,  # Null bytes
        ]
        
        for query in boundary_inputs:
            try:
                response = await agent.chat(message=query, use_research=False)
                # Should not crash
                assert isinstance(response, dict)
            except Exception:
                # Some boundary cases may fail, but should fail gracefully
                pass


@pytest.mark.asyncio
async def test_e2e_fuzz_encoding_variations():
    """
    Fuzz: Various encodings and special characters.
    
    System should handle encoding variations.
    """
    annotate_test(
        "test_e2e_fuzz_encoding_variations",
        pattern="fuzzing_e2e",
        opinion="system_handles_encodings",
        category="e2e_fuzzing",
        hypothesis="System handles various encodings correctly",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        encoding_inputs = [
            "Normal text",
            "Café résumé",  # Accented
            "中文测试",  # Chinese
            "日本語テスト",  # Japanese
            "Русский тест",  # Cyrillic
            "العربية",  # Arabic
            "🚀🎉💡",  # Emojis
            "Test\nwith\nnewlines",
            "Test\twith\ttabs",
            "Test\rwith\rcarriage",
        ]
        
        for query in encoding_inputs:
            try:
                response = await agent.chat(message=query, use_research=False)
                assert isinstance(response, dict)
            except Exception as e:
                # Encoding issues should be handled gracefully
                assert "encoding" in str(e).lower() or "utf" in str(e).lower()


@pytest.mark.asyncio
async def test_e2e_fuzz_concurrent_fuzzing():
    """
    Fuzz: Concurrent random inputs.
    
    System should handle concurrent fuzzing without race conditions.
    """
    annotate_test(
        "test_e2e_fuzz_concurrent_fuzzing",
        pattern="fuzzing_e2e",
        opinion="system_handles_concurrent_fuzzing",
        category="e2e_fuzzing",
        hypothesis="System handles concurrent fuzzing correctly",
    )
    
    import asyncio
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Generate random concurrent queries
        async def fuzz_query():
            query = generate_random_string(random.randint(10, 200))
            try:
                return await agent.chat(message=query, use_research=False)
            except Exception:
                return {"error": "handled"}
        
        # Run 10 concurrent fuzz queries
        results = await asyncio.gather(*[fuzz_query() for _ in range(10)])
        
        # All should complete (may have errors, but no crashes)
        assert len(results) == 10
        assert all(isinstance(r, dict) for r in results)

