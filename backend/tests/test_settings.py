import pytest
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from featurehub.env import require_env

MODULE_LABELS = {
    "core",
    "feature_requests",
    "prioritization",
    "backlog",
    "roadmap",
    "requirements",
    "collaboration",
    "analytics",
}


def test_require_env_missing_names_variable():
    with pytest.raises(ImproperlyConfigured, match="DATABASE_URL"):
        require_env("DATABASE_URL", {})


def test_require_env_returns_value():
    assert require_env("X", {"X": "1"}) == "1"


def test_module_apps_installed():
    labels = {config.label for config in apps.get_app_configs()}
    assert MODULE_LABELS <= labels
