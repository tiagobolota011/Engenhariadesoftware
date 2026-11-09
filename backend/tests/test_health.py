import pytest

from apps.core.health import check_db


@pytest.mark.django_db
def test_health_ok(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "up"}


def test_health_db_down(client, monkeypatch):
    monkeypatch.setattr("apps.core.views.check_db", lambda: False)
    response = client.get("/api/health/")
    assert response.status_code == 503
    # Só estas duas chaves: o endpoint não expõe detalhes internos.
    assert response.json() == {"status": "degraded", "db": "down"}


@pytest.mark.django_db
def test_db_connection_roundtrip():
    # Teste de persistência: liga a um PostgreSQL real (local ou serviço do CI).
    assert check_db() is True
