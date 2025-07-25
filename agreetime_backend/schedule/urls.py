"""
URL configuration for the AgreeTime schedule app.

This file defines route patterns for the API endpoints defined in
``views.py``. It should be included in the project's root URLConf.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Events within a family
    path('families/<int:family_id>/events', views.FamilyEventsListCreateView.as_view(), name='family-events'),
    # Individual event endpoints
    path('events/<int:pk>', views.EventDetailView.as_view(), name='event-detail'),
    path('events/<int:event_id>/approve', views.ApproveEventView.as_view(), name='event-approve'),
    # Approval requests for current user
    path('users/me/approval-requests', views.MyApprovalRequestsView.as_view(), name='my-approval-requests'),
    # Notifications
    path('users/me/notifications', views.MyNotificationsView.as_view(), name='my-notifications'),
    path('users/me/notifications/<int:pk>/read', views.MarkNotificationReadView.as_view(), name='notification-read'),
    # Comments
    path('events/<int:event_id>/comments', views.EventCommentsListCreateView.as_view(), name='event-comments'),
    path('comments/<int:pk>', views.CommentDeleteView.as_view(), name='comment-delete'),
]