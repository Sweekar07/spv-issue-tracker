from django.db import models
from django.contrib.auth import get_user_model
from labels.models import Label

User = get_user_model()

class Issue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_issues'
    )
    assignee = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_issues'
    )
    
    labels = models.ManyToManyField(Label, through='IssueLabel', blank=True)
    
    # Optimistic Concurrency Control
    version = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'issues'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['assignee', 'status']),
            models.Index(fields=['creator']),
            models.Index(fields=['version']),
        ]
    
    def __str__(self):
        return f"#{self.id} - {self.title}"


class IssueLabel(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'issue_labels'
        unique_together = ('issue', 'label')
        indexes = [
            models.Index(fields=['issue', 'label']),
        ]


class IssueHistory(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'issue_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['issue', '-changed_at']),
        ]
