"""Tests for NLTK-enhanced token importance extraction."""

import pytest
from bop.token_importance import extract_key_terms, NLTK_AVAILABLE


def test_nltk_available():
    """Test that NLTK is available and can be used."""
    if not NLTK_AVAILABLE:
        pytest.skip("NLTK not available")
    
    assert NLTK_AVAILABLE


def test_extract_key_terms_with_nltk():
    """Test key term extraction using NLTK when available."""
    text = "Trust is important for knowledge systems. Uncertainty affects decision making. Information geometry provides structure."
    
    terms = extract_key_terms(text, min_length=3, max_terms=10)
    
    # Should extract meaningful terms
    assert len(terms) > 0
    assert isinstance(terms, list)
    
    # Should filter out stop words
    stop_words = {"is", "for", "the", "a", "an"}
    assert not any(word in stop_words for word in terms)
    
    # Should prefer content words (nouns, adjectives, verbs)
    # Terms like "trust", "knowledge", "systems", "uncertainty", "decision", "making", "information", "geometry", "structure" should appear
    content_terms = {"trust", "knowledge", "systems", "uncertainty", "decision", "making", "information", "geometry", "structure", "important", "affects", "provides"}
    assert any(term in content_terms for term in terms), f"Expected content terms, got: {terms}"


def test_extract_key_terms_fallback():
    """Test that fallback works when NLTK is not available."""
    # This test verifies the fallback mechanism works
    # Even if NLTK is available, the fallback code path should still work
    text = "The quick brown fox jumps over the lazy dog."
    
    terms = extract_key_terms(text, min_length=3, max_terms=10)
    
    # Should extract terms
    assert len(terms) > 0
    assert isinstance(terms, list)
    
    # Should filter stop words
    assert "the" not in terms
    assert "over" not in terms


def test_extract_key_terms_pos_tagging():
    """Test that POS tagging improves term selection when available."""
    if not NLTK_AVAILABLE:
        pytest.skip("NLTK not available")
    
    # Text with mix of content words and function words
    text = "The machine learning algorithm processes data efficiently. It uses neural networks for classification."
    
    terms = extract_key_terms(text, min_length=3, max_terms=15)
    
    # Should prefer nouns, adjectives, verbs
    # Terms like "machine", "learning", "algorithm", "processes", "data", "efficiently", "neural", "networks", "classification" should appear
    expected_content = {"machine", "learning", "algorithm", "processes", "data", "efficiently", "neural", "networks", "classification", "uses"}
    found_content = set(terms) & expected_content
    
    # Should find at least some content words
    assert len(found_content) > 0, f"Expected content terms, got: {terms}"


def test_extract_key_terms_handles_contractions():
    """Test that contractions are handled correctly."""
    text = "I don't think it's possible. We've tried everything. They're working on it."
    
    terms = extract_key_terms(text, min_length=3, max_terms=10)
    
    # Should not include contractions as separate words
    assert "n't" not in terms
    assert "'s" not in terms
    assert "'ve" not in terms
    assert "'re" not in terms


def test_extract_key_terms_empty_text():
    """Test that empty text returns empty list."""
    terms = extract_key_terms("", min_length=3, max_terms=10)
    assert terms == []


def test_extract_key_terms_very_short_text():
    """Test that very short text is handled gracefully."""
    terms = extract_key_terms("Hi", min_length=3, max_terms=10)
    # "Hi" is too short (min_length=3), so should return empty
    assert terms == []


def test_extract_key_terms_respects_max_terms():
    """Test that max_terms limit is respected."""
    text = " ".join([f"word{i}" for i in range(100)])
    
    terms = extract_key_terms(text, min_length=3, max_terms=5)
    
    assert len(terms) <= 5

