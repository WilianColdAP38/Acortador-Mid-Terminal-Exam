import pytest

from app import config


def test_falta_variable_detiene_la_app(monkeypatch):
    monkeypatch.delenv("DYNAMODB_TABLE")
    with pytest.raises(RuntimeError, match="DYNAMODB_TABLE"):
        config.load_settings()


def test_base_url_sin_barra_final_y_cors_por_coma(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://1.2.3.4:8000/")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com/, http://b.com")
    s = config.load_settings()
    assert s.public_base_url == "http://1.2.3.4:8000"
    assert s.cors_origins == ["http://a.com", "http://b.com"]
