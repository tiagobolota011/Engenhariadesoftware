"""Configuração do FeatureHub (monólito modular — ver SCRUM-61)."""

import os
from pathlib import Path

import dj_database_url

from featurehub.env import require_env

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

# Em desenvolvimento há um valor de recurso; fora de DEBUG a chave é obrigatória.
SECRET_KEY = (
    os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
    if DEBUG
    else require_env("DJANGO_SECRET_KEY")
)

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    # Módulos do FeatureHub (um app por módulo da arquitetura)
    "apps.core",
    "apps.requests",
    "apps.prioritization",
    "apps.backlog",
    "apps.roadmap",
    "apps.requirements",
    "apps.collaboration",
    "apps.analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "featurehub.urls"
WSGI_APPLICATION = "featurehub.wsgi.application"

DATABASES = {"default": dj_database_url.parse(require_env("DATABASE_URL"), conn_max_age=60)}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Sessão por cookies e CSRF nas escritas (SCRUM-61, NFR-07/08)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"featurehub": {"handlers": ["console"], "level": "INFO"}},
}
