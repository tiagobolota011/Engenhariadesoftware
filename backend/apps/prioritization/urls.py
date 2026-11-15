from django.urls import path

from apps.prioritization import views

urlpatterns = [
    path("requests/<int:pk>/vote/", views.VoteView.as_view(), name="vote"),
    path("prioritization/", views.PrioritizationView.as_view(), name="prioritization"),
    path("prioritization/reorder/", views.ReorderView.as_view(), name="prioritization-reorder"),
    path("prioritization/suggestion/", views.SuggestionView.as_view(), name="suggestion"),
    path(
        "prioritization/suggestion/accept/",
        views.AcceptSuggestionView.as_view(),
        name="suggestion-accept",
    ),
]
