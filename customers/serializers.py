from rest_framework import serializers

from .models import Customer, CustomerDocument, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class CustomerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDocument
        fields = ["id", "name", "file", "uploaded_by", "created_at"]
        read_only_fields = ["uploaded_by", "created_at"]


class CustomerSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True,
        source="tags", required=False,
    )
    documents = CustomerDocumentSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id", "first_name", "last_name", "full_name", "email", "phone",
            "company", "position", "address", "city", "country", "notes",
            "status", "tags", "tag_ids", "owner", "documents",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
