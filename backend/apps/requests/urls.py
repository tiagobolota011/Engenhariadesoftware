from django.urls import path

from apps.requests import views

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("requests/", views.RequestListView.as_view(), name="requests"),
    path("requests/similar/", views.SimilarRequestsView.as_view(), name="requests-similar"),
    path("requests/<int:pk>/", views.RequestDetailView.as_view(), name="request-detail"),
    path("requests/<int:pk>/assessment/", views.AssessmentView.as_view(), name="assessment"),
    path("roadmap/public/", views.PublicRoadmapView.as_view(), name="roadmap-public"),
]
