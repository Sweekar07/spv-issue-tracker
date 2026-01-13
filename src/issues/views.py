from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

from issues.models import Issue
from issues import serializers
from issues.services import IssueService
from comments.models import Comment

User = get_user_model()

class IssueListCreateView(ListCreateAPIView):
    
    queryset = Issue.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority']
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.IssueCreateSerializer
        return serializers.IssueListSerializer


class IssueDetail(APIView):

    def get(self, request, pk, format=None):
        """
        Return issue details with comments and labels.
        """
        issue = Issue.objects.select_related('assignee', 'creator').prefetch_related('labels', 'comments').get(pk=pk)
        return Response(serializers.IssueDetailSerializer(issue).data)

    def patch(self, request, pk, format=None):
        """
        Update issue with version check (optimistic concurrency).
        """
        issue = Issue.objects.get(pk=pk)
        serializer = serializers.IssueUpdateSerializer(issue, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updater_user_id = request.data.get("updated_by")
        if not updater_user_id:
            return Response(
                {"updated_by": "updated_by user id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = get_object_or_404(User, id=updater_user_id)

        updated_issue = IssueService.update_issue(issue, user=user, **serializer.validated_data)
        return Response(
            serializers.IssueDetailSerializer(updated_issue).data,
            status=status.HTTP_200_OK
        )


class IssueComments(APIView):

    def post(self, request, pk, format=None):
        """
        Add a comment to the issue.
        """
        issue = Issue.objects.get(pk=pk)
        serializer = serializers.CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        author_id = get_object_or_404(User, id=request.data.get("author_id"))

        comment = Comment.objects.create(
            issue=issue,
            author=author_id,
            body=serializer.validated_data['body']
        )
        return Response(serializers.CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class IssueLabels(APIView):
    """
    View to replace labels on specific issue.
    """

    def put(self, request, pk, format=None):
        """
        Replace all labels on the issue.
        """
        issue = Issue.objects.get(pk=pk)
        label_ids = request.data.get('label_ids', [])

        labels = IssueService.replace_labels(issue, label_ids)
        return Response({
            'message': 'Labels updated successfully',
            'labels': serializers.LabelSerializer(labels, many=True).data
        })


class BulkStatusUpdate(APIView):
    """
    View to bulk update issue statuses transactionally.
    """

    def post(self, request, format=None):
        """
        Update status of multiple issues.
        """
        serializer = serializers.BulkStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            count = IssueService.bulk_update_status(
                serializer.validated_data['issue_ids'],
                serializer.validated_data['status']
            )
            return Response({
                'message': f'Successfully updated {count} issues',
                'updated_count': count
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CSVImport(APIView):

    def post(self, request, format=None):
        """
        Import issues from CSV file with validation.
        """
        serializer = serializers.CSVImportSerializer(data=request.FILES)
        serializer.is_valid(raise_exception=True)
        
        admin_user = User.objects.filter(username="admin").first()

        results = IssueService.import_from_csv(
            serializer.validated_data['file'],
            admin_user
        )
        
        if results['failed'] > 0:
            return Response(results, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(results, status=status.HTTP_201_CREATED)


class IssueTimeline(APIView):

    pagination_class = PageNumberPagination

    def get(self, request, pk, format=None):
        """
        Return issue history timeline.
        """
        issue = get_object_or_404(Issue, pk=pk)
        history = issue.history.all().order_by("-changed_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(history, request)

        serializer = serializers.IssueHistorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
