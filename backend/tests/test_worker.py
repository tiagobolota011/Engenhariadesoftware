import logging

import pytest
from django.core.management import call_command

from apps.core.worker import run_once


@pytest.mark.django_db
def test_run_once_db_up(caplog):
    with caplog.at_level(logging.INFO, logger="featurehub.worker"):
        assert run_once() is True
    assert "worker heartbeat db=up" in caplog.text


def test_run_once_db_down_does_not_raise(caplog, monkeypatch):
    monkeypatch.setattr("apps.core.worker.check_db", lambda: False)
    with caplog.at_level(logging.INFO, logger="featurehub.worker"):
        assert run_once() is False
    assert "db=down" in caplog.text


@pytest.mark.django_db
def test_command_once():
    call_command("run_worker", "--once")
