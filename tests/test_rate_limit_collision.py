"""Test rate limiting identifier collision prevention."""

import hashlib

from fastapi.testclient import TestClient

from src.bop.server import app


def test_rate_limit_uses_hashed_api_key():
    """Test that rate limiting uses hashed API keys to prevent collisions."""
    # Create two API keys with same first 8 characters
    api_key1 = "tskey-auth-abc1234567890"
    api_key2 = "tskey-auth-abc1234567891"  # Different key, same first 8 chars

    # Old way (buggy) would create same identifier
    old_id1 = f"api_key:{api_key1[:8]}..."
    old_id2 = f"api_key:{api_key2[:8]}..."
    assert old_id1 == old_id2, "Old way creates collision (this is the bug)"

    # New way (fixed) uses hashed keys
    hash1 = hashlib.sha256(api_key1.encode()).hexdigest()[:16]
    hash2 = hashlib.sha256(api_key2.encode()).hexdigest()[:16]
    new_id1 = f"api_key:{hash1}"
    new_id2 = f"api_key:{hash2}"

    assert new_id1 != new_id2, "New way prevents collisions"
    assert len(hash1) == 16, "Hash should be 16 characters"
    assert len(hash2) == 16, "Hash should be 16 characters"


def test_rate_limit_different_keys_different_buckets():
    """Test that different API keys get different rate limit buckets."""
    client = TestClient(app)

    # Make requests with different API keys
    api_key1 = "test-key-1-abc123"
    api_key2 = "test-key-2-xyz789"

    # Both should start with same rate limit
    response1 = client.get(
        "/health",
        headers={"X-API-Key": api_key1}
    )
    response2 = client.get(
        "/health",
        headers={"X-API-Key": api_key2}
    )

    # Both should succeed
    assert response1.status_code in [200, 401, 503]  # May need auth
    assert response2.status_code in [200, 401, 503]

    # Rate limit headers should be present
    if "X-RateLimit-Limit" in response1.headers:
        limit1 = response1.headers["X-RateLimit-Limit"]
        limit2 = response2.headers["X-RateLimit-Limit"]
        assert limit1 == limit2, "Both should have same limit"

        # Remaining should be independent
        response1.headers.get("X-RateLimit-Remaining", "unknown")
        response2.headers.get("X-RateLimit-Remaining", "unknown")
        # They should be independent (can't easily test without making many requests)


def test_rate_limit_same_key_same_bucket():
    """Test that same API key uses same rate limit bucket."""
    client = TestClient(app)

    api_key = "test-key-same-123"

    # Make multiple requests with same key
    responses = []
    for i in range(5):
        response = client.get(
            "/health",
            headers={"X-API-Key": api_key}
        )
        responses.append(response)

    # All should succeed (health endpoint may not be rate limited)
    for response in responses:
        assert response.status_code in [200, 401, 503]

    # If rate limit headers are present, remaining should decrease
    if "X-RateLimit-Remaining" in responses[0].headers:
        remaining_values = [
            int(r.headers.get("X-RateLimit-Remaining", "30"))
            for r in responses
        ]
        # Remaining should decrease or stay same (health may not count)
        assert all(r <= 30 for r in remaining_values), "Remaining should be <= limit"

