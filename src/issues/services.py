import csv
import io
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from issues.models import Issue, IssueHistory, IssueLabel
from labels.models import Label

User = get_user_model()

class ConcurrencyError(Exception):
    pass


class IssueService:
    
    @staticmethod
    @transaction.atomic
    def create_issue(creator, **data):
        assignee_id = data.pop('assignee_id', None)
        label_ids = data.pop('label_ids', [])

        assignee = User.objects.filter(id=assignee_id).first() if assignee_id else None
        issue = Issue.objects.create(creator=creator, assignee=assignee, **data)

        if label_ids:
            labels = Label.objects.filter(id__in=label_ids)
            if labels.count() != len(set(label_ids)):
                raise ValueError("One or more invalid label IDs")

            IssueLabel.objects.bulk_create([IssueLabel(issue=issue, label=l) for l in labels])
        
        return issue
    
    @staticmethod
    @transaction.atomic
    def update_issue(issue, user, **data):
        version = data.pop('version')
        
        # Optimistic Concurrency Check
        issue_to_update = Issue.objects.select_for_update().get(id=issue.id)
        if issue_to_update.version != version:
            raise ConcurrencyError(f"Version mismatch. Current version is {issue_to_update.version}")
        
        # Track changes for history
        changes = {}
        for field, new_value in data.items():
            if field == 'assignee_id':
                old_value = issue_to_update.assignee_id
                issue_to_update.assignee_id = new_value
                if old_value != new_value:
                    changes['assignee'] = (old_value, new_value)
            else:
                old_value = getattr(issue_to_update, field)
                if old_value != new_value:
                    setattr(issue_to_update, field, new_value)
                    changes[field] = (str(old_value), str(new_value))
        
        # Update resolved_at timestamp
        if 'status' in data and data['status'] == 'resolved' and not issue_to_update.resolved_at:
            issue_to_update.resolved_at = timezone.now()
        
        # Increment version
        issue_to_update.version += 1
        issue_to_update.save()
        
        # Create history entries
        for field_name, (old_val, new_val) in changes.items():
            IssueHistory.objects.create(
                issue=issue_to_update,
                changed_by=user,
                field_name=field_name,
                old_value=old_val,
                new_value=new_val
            )
        
        return issue_to_update
    
    @staticmethod
    @transaction.atomic
    def bulk_update_status(issue_ids, status):
        issues = Issue.objects.filter(id__in=issue_ids).select_for_update()
        
        if issues.count() != len(issue_ids):
            missing_ids = set(issue_ids) - set(issues.values_list('id', flat=True))
            raise ValueError(f"Issues not found: {missing_ids}")
        
        # Validate status transition rules (example rule)
        for issue in issues:
            if issue.status == 'closed' and status != 'closed':
                raise ValueError(f"Cannot reopen closed issue #{issue.id}")
        
        # Update all issues
        updated_count = 0
        for issue in issues:
            issue.status = status
            issue.version += 1
            if status == 'resolved' and not issue.resolved_at:
                issue.resolved_at = timezone.now()
            issue.save()
            updated_count += 1
        
        return updated_count
    
    @staticmethod
    @transaction.atomic
    def replace_labels(issue, label_ids):
        # Remove existing labels
        IssueLabel.objects.filter(issue=issue).delete()
        
        # Add new labels
        labels = Label.objects.filter(id__in=label_ids)
        
        if labels.count() != len(label_ids):
            raise ValueError("One or more invalid label IDs")
        
        IssueLabel.objects.bulk_create([
            IssueLabel(issue=issue, label=label)
            for label in labels
        ])
        
        return labels
    
    @staticmethod
    def import_from_csv(csv_file, creator):
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            required_fields = ['title', 'status', 'priority']
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):
                    results['total'] += 1
                    
                    try:
                        # Validate required fields
                        for field in required_fields:
                            if not row.get(field):
                                raise ValueError(f"Missing required field: {field}")
                        
                        # Validate status
                        status = row['status'].lower()
                        valid_statuses = dict(Issue.STATUS_CHOICES).keys()
                        if status not in valid_statuses:
                            raise ValueError(f"Invalid status: {status}")
                        
                        # Validate priority
                        priority = row['priority'].lower()
                        valid_priorities = dict(Issue.PRIORITY_CHOICES).keys()
                        if priority not in valid_priorities:
                            raise ValueError(f"Invalid priority: {priority}")
                        
                        # Get assignee if provided
                        assignee = None
                        if row.get('assignee_email'):
                            assignee = User.objects.filter(email=row['assignee_email']).first()
                            if not assignee:
                                raise ValueError(f"Assignee not found: {row['assignee_email']}")
                        
                        # Create issue
                        Issue.objects.create(
                            title=row['title'],
                            description=row.get('description', ''),
                            status=status,
                            priority=priority,
                            creator=creator,
                            assignee=assignee
                        )
                        
                        results['success'] += 1
                    
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append({
                            'row': row_num,
                            'error': str(e),
                            'data': row
                        })
                        # Rollback transaction if any row fails
                        raise
        
        except Exception as e:
            # If any error occurs, rollback entire import
            transaction.set_rollback(True)
            results['error'] = f"Import failed: {str(e)}"
        
        return results
