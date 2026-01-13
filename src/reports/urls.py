from django.urls import path
from reports.views import TopAssigneesView, LatencyReportView

urlpatterns = [
    path('reports/top-assignees/', TopAssigneesView.as_view(), name='top-assignees'),
    path('reports/latency/', LatencyReportView.as_view(), name='latency-report'),
]
