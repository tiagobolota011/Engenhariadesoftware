from django.urls import path

from apps.collaboration import views

urlpatterns = [
    path("requests/<int:pk>/comments/", views.CommentCreateView.as_view(), name="comments"),
    path(
        "requests/<int:pk>/comments/<int:comment_id>/decision/",
        views.DecisionView.as_view(),
        name="comment-decision",
    ),
]
