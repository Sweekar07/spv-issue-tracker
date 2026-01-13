from django.urls import path
from . import views

urlpatterns = [
    path('issues/', views.IssueListCreateView.as_view(), name='issue-list-create'),
    path('issues/<int:pk>/', views.IssueDetail.as_view(), name='issue-detail'),
    path('issues/<int:pk>/comments/', views.IssueComments.as_view(), name='issue-comments'),
    path('issues/<int:pk>/labels/', views.IssueLabels.as_view(), name='issue-labels'),
    path('issues/bulk-status/', views.BulkStatusUpdate.as_view(), name='bulk-status'),
    path('issues/import/', views.CSVImport.as_view(), name='csv-import'),
    path('issues/<int:pk>/timeline/', views.IssueTimeline.as_view(), name='issue-timeline'),
]
