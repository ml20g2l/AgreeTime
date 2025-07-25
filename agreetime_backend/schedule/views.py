"""
API views implementing AgreeTime endpoints.

These views use Django REST Framework to expose models defined in
``models.py`` via a set of RESTful endpoints. Authentication and
permission classes are not fully fleshed out; in a real project you
would add appropriate permission checks.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Family,
    Event,
    EventParticipant,
    EventApprover,
    Notification,
    Comment,
)
from .serializers import (
    EventSerializer,
    NotificationSerializer,
    CommentSerializer,
)

User = get_user_model()


class FamilyEventsListCreateView(generics.ListCreateAPIView):
    """List and create events for a given family."""

    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        family_id = self.kwargs["family_id"]
        return Event.objects.filter(family_id=family_id)

    def perform_create(self, serializer):
        family_id = self.kwargs["family_id"]
        family = Family.objects.get(id=family_id)
        serializer.save(family=family)


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a single event."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        event = self.get_object()
        # mark as cancelled instead of hard delete if confirmed
        if event.status == Event.CONFIRMED:
            event.status = Event.CANCELLED
            event.save(update_fields=["status"])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return super().delete(request, *args, **kwargs)


class ApproveEventView(APIView):
    """Approve or reject an event."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        decision = request.data.get("decision")
        reason = request.data.get("reason", "")
        user = request.user
        try:
            approver = EventApprover.objects.get(event_id=event_id, approver=user)
        except EventApprover.DoesNotExist:
            return Response({"detail": "Not an approver for this event."}, status=403)
        if approver.status != EventApprover.PENDING:
            return Response({"detail": "Already responded."}, status=400)
        approver.decision_time = timezone.now()
        if decision == "approve":
            approver.status = EventApprover.APPROVED
        else:
            approver.status = EventApprover.REJECTED
            approver.rejection_reason = reason
        approver.save()
        # Check overall approval
        event = approver.event
        statuses = event.approvers.values_list("status", flat=True)
        if all(s == EventApprover.APPROVED for s in statuses):
            event.status = Event.CONFIRMED
            event.save(update_fields=["status"])
        elif any(s == EventApprover.REJECTED for s in statuses):
            event.status = Event.CANCELLED
            event.save(update_fields=["status"])
        return Response({"status": approver.status})


class MyApprovalRequestsView(generics.ListAPIView):
    """List pending approval requests for the current user."""
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(
            approvers__approver=self.request.user,
            approvers__status=EventApprover.PENDING,
        )


class MyNotificationsView(generics.ListAPIView):
    """List notifications for the current user."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkNotificationReadView(APIView):
    """Mark a notification as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response(status=404)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(status=204)


class EventCommentsListCreateView(generics.ListCreateAPIView):
    """List and create comments for an event."""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        event_id = self.kwargs["event_id"]
        return Comment.objects.filter(event_id=event_id)

    def perform_create(self, serializer):
        event_id = self.kwargs["event_id"]
        serializer.save(event_id=event_id, author=self.request.user)


class CommentDeleteView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommentSerializer

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        if request.user != comment.author and request.user != comment.event.creator:
            return Response(status=403)
        return super().delete(request, *args, **kwargs)