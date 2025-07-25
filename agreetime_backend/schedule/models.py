"""
Data models for the AgreeTime scheduling application.

This file defines Django ORM models corresponding to the database tables
outlined in the database design. Each model maps to a table and defines
relationships and fields required to implement family calendar, event
management and approval workflows.

Note: This file is a skeleton; additional fields such as indexing,
authentication logic, and custom managers should be added in a full
implementation.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Family(models.Model):
    """A family or group of users who share a calendar."""

    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Custom user model that attaches a user to a family."""

    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True, related_name="members")
    # additional fields for OAuth (e.g. google account) could go here


class Event(models.Model):
    """Represents a scheduled event belonging to a family."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DELETED = "DELETED"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (CANCELLED, "Cancelled"),
        (DELETED, "Deleted"),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="events")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.start_time:%Y-%m-%d})"


class EventParticipant(models.Model):
    """Join table linking events to their participants."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_participations")

    class Meta:
        unique_together = ("event", "user")


class EventApprover(models.Model):
    """Tracks approval status for each event approver."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (EXPIRED, "Expired"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="approvers")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="approvals")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    decision_time = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        unique_together = ("event", "approver")


class Notification(models.Model):
    """Represents a push notification or message sent to a user."""

    EVENT_CREATED = "EVENT_CREATED"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    APPROVAL_RESULT = "APPROVAL_RESULT"
    EVENT_CANCELLED = "EVENT_CANCELLED"
    TYPE_CHOICES = [
        (EVENT_CREATED, "Event Created"),
        (APPROVAL_REQUEST, "Approval Request"),
        (APPROVAL_RESULT, "Approval Result"),
        (EVENT_CANCELLED, "Event Cancelled"),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Attachment(models.Model):
    """Stores references to files attached to events."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attachments")
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploaded_attachments")
    file = models.FileField(upload_to="event_attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    """Represents comments left on an event."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecurringEvent(models.Model):
    """Defines a recurrence rule for an event."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    RECURRENCE_TYPE_CHOICES = [
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
        (YEARLY, "Yearly"),
    ]

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="recurrence")
    recurrence_type = models.CharField(max_length=16, choices=RECURRENCE_TYPE_CHOICES)
    interval = models.PositiveIntegerField(default=1)
    day_of_week = models.PositiveSmallIntegerField(null=True, blank=True)
    day_of_month = models.PositiveSmallIntegerField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class EventHistory(models.Model):
    """Stores an audit log of changes made to an event."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="event_history_entries")
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)


class UserSettings(models.Model):
    """Stores per-user configuration such as notification preferences."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    notifications_enabled = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default="ko")
    created_at = models.DateTimeField(auto_now_add=True)