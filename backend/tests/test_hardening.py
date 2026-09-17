"""Tests for the production-safety fixes: signing key, rate limit, migrations."""

import pytest

from app.config import PLACEHOLDER_SECRET_KEY, Settings
from app.ratelimit import SlidingWindowRateLimiter, openfoodfacts_limiter


# ------------------------------------------------------------------ secret key
def _settings(**overrides) -> Settings:
    return Settings(use_sqlite=True, **overrides)


def test_placeholder_key_is_rejected_in_production():
    settings = _settings(environment="production", secret_key=PLACEHOLDER_SECRET_KEY)
    assert settings.secret_key_problem() is not None
    with pytest.raises(RuntimeError, match="placeholder"):
        settings.enforce_production_safety()


def test_short_key_is_rejected_in_production():
    settings = _settings(environment="production", secret_key="a" * 31)
    with pytest.raises(RuntimeError, match="31 characters"):
        settings.enforce_production_safety()


def test_strong_key_is_accepted_in_production():
    settings = _settings(environment="production", secret_key="b" * 64)
    assert settings.secret_key_problem() is None
    settings.enforce_production_safety()  # must not raise


def test_development_only_warns(caplog):
    """A weak key must not block local development — but it must be logged."""
    settings = _settings(secret_key=PLACEHOLDER_SECRET_KEY)
    assert not settings.is_production
    with caplog.at_level("WARNING"):
        settings.enforce_production_safety()
    assert "Insecure configuration" in caplog.text


# ---------------------------------------------------------------- rate limiter
def test_limiter_allows_up_to_the_limit_then_refuses():
    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60)
    assert [limiter.check("u1")[0] for _ in range(3)] == [True, True, True]

    allowed, retry_after = limiter.check("u1")
    assert allowed is False
    assert 0 < retry_after <= 61


def test_limiter_is_per_key():
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    assert limiter.check("u1")[0] is True
    assert limiter.check("u1")[0] is False
    assert limiter.check("u2")[0] is True  # one user cannot exhaust another's quota


def test_limiter_window_expires():
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=1)
    assert limiter.check("u1")[0] is True
    assert limiter.check("u1")[0] is False

    import time

    time.sleep(1.1)
    assert limiter.check("u1")[0] is True


def test_limiter_rejects_nonsense_configuration():
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(limit=0, window_seconds=60)
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(limit=5, window_seconds=0)


def test_search_endpoint_returns_429_when_limit_is_hit(client, auth_headers, monkeypatch):
    """The outbound OpenFoodFacts route must stop calling out once over quota."""
    openfoodfacts_limiter.reset()
    monkeypatch.setattr(openfoodfacts_limiter, "limit", 2)

    calls = []

    async def fake_search(query, page_size=20):
        calls.append(query)
        return []

    monkeypatch.setattr("app.routers.macros.openfoodfacts.search_foods", fake_search)

    assert client.get("/api/macros/search", params={"q": "oats"}, headers=auth_headers).status_code == 200
    assert client.get("/api/macros/search", params={"q": "oats"}, headers=auth_headers).status_code == 200

    blocked = client.get("/api/macros/search", params={"q": "oats"}, headers=auth_headers)
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"].isdigit()

    # The blocked request must not have reached OpenFoodFacts.
    assert len(calls) == 2

    openfoodfacts_limiter.reset()


def test_rate_limit_does_not_affect_other_endpoints(client, auth_headers, monkeypatch):
    openfoodfacts_limiter.reset()
    monkeypatch.setattr(openfoodfacts_limiter, "limit", 1)

    async def fake_search(query, page_size=20):
        return []

    monkeypatch.setattr("app.routers.macros.openfoodfacts.search_foods", fake_search)

    client.get("/api/macros/search", params={"q": "oats"}, headers=auth_headers)
    assert client.get("/api/macros/search", params={"q": "x"}, headers=auth_headers).status_code == 429
    # The user's own log is unaffected by the outbound quota.
    assert client.get("/api/macros/summary", headers=auth_headers).status_code == 200

    openfoodfacts_limiter.reset()
