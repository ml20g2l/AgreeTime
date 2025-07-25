"""
DRF serializers for AgreeTime models.

These classes convert model instances into JSON representations and
validate incoming API data. Nested serializers are used to embed
related objects where appropriate.
"""

from rest_framework import serializers

from .models import (
    Family,
    User,
    Event,
    EventParticipant,
    EventApprover,
    Notification,
    Attachment,
    Comment,
    RecurringEvent,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class EventParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventParticipant
        fields = ["id", "user"]


class EventApproverSerializer(serializers.ModelSerializer):
    approver = UserSerializer(read_only=True)

    class Meta:
        model = EventApprover
        fields = ["id", "approver", "status", "decision_time", "rejection_reason"]


class EventSerializer(serializers.ModelSerializer):
    participants = EventParticipantSerializer(many=True, read_only=True)
    approvers = EventApproverSerializer(many=True, read_only=True)
    creator = UserSerializer(read_only=True)

    participant_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=True
    )
    approver_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=False, required=False
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "family",
            "creator",
            "title",
            "description",
            "location",
            "start_time",
            "end_time",
            "status",
            "participants",
            "approvers",
            "participant_ids",
            "approver_ids",
        ]

    def create(self, validated_data):
        participant_ids = validated_data.pop("participant_ids")
        approver_ids = validated_data.pop("approver_ids", [])
        user = self.context["request"].user
        # assign creator and family
        family = validated_data["family"]
        event = Event.objects.create(creator=user, **validated_data)
        # always include creator as participant
        if user.id not in participant_ids:
            participant_ids.append(user.id)
        # create participant records
        for uid in participant_ids:
            EventParticipant.objects.create(event=event, user_id=uid)
        # create approver records if more than one participant
        if len(participant_ids) > 1:
            if not approver_ids:
                raise serializers.ValidationError("At least one approver must be specified.")
            for aid in approver_ids:
                EventApprover.objects.create(event=event, approver_id=aid)
        return event


class NotificationSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    class Meta:
        model = Notification
        fields = ["id", "event", "type", "message", "is_read", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at"]