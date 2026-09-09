import pytest

from app.config import Config, ConfigError


def test_load_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ConfigError):
        Config.load()


def test_load_applies_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://localhost/test")
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("REDIS_STREAM", raising=False)

    cfg = Config.load()

    assert cfg.database_url == "postgres://localhost/test"
    assert cfg.port == 8000
    assert cfg.redis_stream == "clicks"
    assert cfg.consumer_group == "analytics-worker"


def test_load_rejects_invalid_int(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://localhost/test")
    monkeypatch.setenv("PORT", "not-a-number")
    with pytest.raises(ConfigError):
        Config.load()
