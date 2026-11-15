from django.urls import include, path

from apps.core.auth_views import CsrfView, LoginView, LogoutView, MeView
from apps.core.views import HealthView

urlpatterns = [
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/", include("apps.requests.urls")),
    path("api/", include("apps.prioritization.urls")),
    path("api/", include("apps.collaboration.urls")),
]
