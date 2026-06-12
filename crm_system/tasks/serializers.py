from rest_framework import serializers

from .models import Task, TaskAttachment, TaskComment


class TaskCommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "body", "author", "author_email", "created_at"]
        read_only_fields = ["author", "created_at"]


class TaskAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAttachment
        fields = ["id", "file", "uploaded_by", "created_at"]
        read_only_fields = ["uploaded_by", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    comments = TaskCommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "assigned_to", "assigned_to_name",
            "created_by", "priority", "status", "due_date", "is_overdue",
            "comments", "attachments", "created_at", "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]
