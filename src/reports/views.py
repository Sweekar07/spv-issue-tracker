from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from issues.models import Issue
from reports.serializers import TopAssigneesSerializer, LatencyReportSerializer


class TopAssigneesView(APIView):
    def get(self, request):
        top_assignees = (
            Issue.objects
            .filter(assignee__isnull=False)
            .values('assignee__id', 'assignee__username', 'assignee__email')
            .annotate(
                total_issues=Count('id'),
                resolved_issues=Count('id', filter=Q(status='resolved')),
                open_issues=Count('id', filter=Q(status='open'))
            )
            .order_by('-total_issues')[:10]
        )
        
        serializer = TopAssigneesSerializer(top_assignees, many=True)
        return Response(serializer.data)


class LatencyReportView(APIView):
    def get(self, request):
        resolved_issues = Issue.objects.filter(
            status='resolved',
            resolved_at__isnull=False
        ).annotate(
            resolution_time=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=DurationField()
            )
        )
        
        avg_resolution = resolved_issues.aggregate(
            average_seconds=Avg('resolution_time')
        )
        
        if avg_resolution['average_seconds']:
            avg_hours = avg_resolution['average_seconds'].total_seconds() / 3600
        else:
            avg_hours = 0
        
        data = {
            'total_resolved': resolved_issues.count(),
            'average_resolution_hours': round(avg_hours, 2)
        }
        
        serializer = LatencyReportSerializer(data)
        return Response(serializer.data)
