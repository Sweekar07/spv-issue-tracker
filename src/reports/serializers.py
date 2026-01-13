from rest_framework import serializers


class TopAssigneesSerializer(serializers.Serializer):
    assignee__id = serializers.IntegerField()
    assignee__username = serializers.CharField()
    assignee__email = serializers.EmailField()
    total_issues = serializers.IntegerField()
    resolved_issues = serializers.IntegerField()
    open_issues = serializers.IntegerField()


class LatencyReportSerializer(serializers.Serializer):
    total_resolved = serializers.IntegerField()
    average_resolution_hours = serializers.FloatField()
