from rest_framework import serializers
from django.contrib.auth import get_user_model

from issues.models import Issue, IssueHistory
from comments.models import Comment
from labels.models import Label
from issues.models import Issue, IssueLabel


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'color']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Comment
        fields = ['id', 'body', 'author', 'author_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_body(self, value):
        body = value.strip()
        if not body:
            raise serializers.ValidationError("Comment body cannot be empty")
        return body


class IssueListSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    
    class Meta:
        model = Issue
        fields = [
            'id', 'title', 'status', 'priority', 'creator', 
            'assignee', 'labels', 'created_at', 'updated_at', 'version'
        ]


class IssueDetailSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Issue
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'creator', 'assignee', 'labels', 'comments',
            'created_at', 'updated_at', 'resolved_at', 'version'
        ]


class IssueCreateSerializer(serializers.ModelSerializer):
    creator_id = serializers.IntegerField(write_only=True)
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    label_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Issue
        fields = ['title', 'description', 'status', 'priority', 'creator_id', 'assignee_id', 'label_ids']

    def validate_creator_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid creator ID")
        return value
    
    def validate_assignee_id(self, value):
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid assignee ID")
        return value
    
    def create(self, validated_data):
        creator_id = validated_data.pop('creator_id')
        assignee_id = validated_data.pop('assignee_id', None)
        label_ids = validated_data.pop('label_ids', [])

        issue = Issue.objects.create(
            creator=User.objects.get(id=creator_id),
            assignee=User.objects.get(id=assignee_id) if assignee_id else None,
            **validated_data
        )

        if label_ids:
            labels = Label.objects.filter(id__in=label_ids)
            IssueLabel.objects.bulk_create([
                IssueLabel(issue=issue, label=label)
                for label in labels
            ])

        return issue


class IssueUpdateSerializer(serializers.ModelSerializer):
    version = serializers.IntegerField(required=True)
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Issue
        fields = ['title', 'status', 'version', 'assignee_id']
    
    def validate(self, attrs):
        instance = self.instance
        if instance.version != attrs['version']:
            raise serializers.ValidationError({
                'version': f'Version mismatch. Current version is {instance.version}'
            })
        return attrs


class BulkStatusUpdateSerializer(serializers.Serializer):
    issue_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    status = serializers.ChoiceField(choices=Issue.STATUS_CHOICES)


class CSVImportSerializer(serializers.Serializer):
    file = serializers.FileField()


class IssueHistorySerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = IssueHistory
        fields = ['id', 'field_name', 'old_value', 'new_value', 'changed_by', 'changed_at']
