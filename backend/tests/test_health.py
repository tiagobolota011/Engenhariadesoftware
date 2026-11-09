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


@pytest.mark.django_db(transaction=True)
def test_check_db_recovers_after_connection_is_killed():
    # Uma ligação estabelecida que o servidor termina (restart da BD, falha de rede)
    # não pode deixar o worker preso em db=down: o ciclo seguinte volta a ligar.
    import psycopg
    from django.db import connection

    assert check_db() is True
    pid = connection.connection.info.backend_pid
    with psycopg.connect(
        "postgres://featurehub:featurehub@localhost:5432/featurehub", autocommit=True
    ) as admin:
        admin.execute("SELECT pg_terminate_backend(%s)", [pid])

    check_db()  # este ciclo pode falhar, porque descobre a ligação morta
    assert check_db() is True
