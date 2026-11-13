import pytest
from src.onshape_client import OnshapeClient


def test_missing_credentials(monkeypatch):
    monkeypatch.delenv("ONSHAPE_ACCESS_KEY", raising=False)
    monkeypatch.delenv("ONSHAPE_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        OnshapeClient()


def test_https_required(monkeypatch):
    monkeypatch.setenv("ONSHAPE_ACCESS_KEY", "abc")
    monkeypatch.setenv("ONSHAPE_SECRET_KEY", "xyz")
    monkeypatch.setenv("ONSHAPE_BASE_URL", "http://example.org")
    with pytest.raises(ValueError):
        OnshapeClient()
