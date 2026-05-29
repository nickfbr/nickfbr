import pytest

from app.errors import AppError
from app.rate_limit import InMemoryRateLimiter, build_rate_limiter
from app.routers import recipes as recipes_router
from tests.test_parse_endpoint import LLM_RECIPE
from app.parsing import service


def test_in_memory_limiter_blocks_over_limit():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=3600)
    limiter.check("user:1")
    limiter.check("user:1")
    with pytest.raises(AppError) as exc:
        limiter.check("user:1")
    assert exc.value.code == "RATE_LIMITED"
    assert exc.value.status_code == 429
    # A different key has its own budget.
    limiter.check("user:2")


def test_factory_defaults_to_in_memory():
    # No REDIS_URL in the test environment.
    assert isinstance(build_rate_limiter(), InMemoryRateLimiter)


def test_parse_endpoint_returns_429_when_over_limit(auth_client, monkeypatch):
    monkeypatch.setattr(service, "parse_with_llm", lambda text: dict(LLM_RECIPE))
    monkeypatch.setattr(
        recipes_router, "parse_rate_limiter", InMemoryRateLimiter(limit=1, window_seconds=3600)
    )
    first = auth_client.post("/api/recipes/parse", json={"text": "x"})
    assert first.status_code == 200
    second = auth_client.post("/api/recipes/parse", json={"text": "x"})
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "RATE_LIMITED"
