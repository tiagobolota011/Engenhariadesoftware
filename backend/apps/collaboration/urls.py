from django.urls import path

from apps.collaboration import views

urlpatterns = [
    path("requests/<int:pk>/comments/", views.CommentCreateView.as_view(), name="comments"),
    path(
        "requests/<int:pk>/comments/<int:comment_id>/decision/",
        views.DecisionView.as_view(),
        name="comment-decision",
    ),
    path("members/", views.MemberListView.as_view(), name="members"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/unread/", views.UnreadCountView.as_view(), name="notifications-unread"),
    path(
        "notifications/read-all/",
        views.NotificationReadAllView.as_view(),
        name="notifications-read-all",
    ),
    path(
        "notifications/<int:pk>/read/",
        views.NotificationReadView.as_view(),
        name="notification-read",
    ),
]
