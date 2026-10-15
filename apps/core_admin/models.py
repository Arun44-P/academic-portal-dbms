from django.db import models


class AdminAuditLog(models.Model):
    ACTION_CHOICES = (
        ('DROP_TABLE', 'Drop Table'),
        ('TRUNCATE_TABLE', 'Truncate Table'),
        ('BULK_DELETE', 'Bulk Delete Records'),
        ('ALTER_SCHEMA', 'Alter Schema / DDL'),
        ('RAW_SQL_EXECUTE', 'Raw SQL Execution'),
        ('USER_ROLE_OVERRIDE', 'User Role Override'),
    )
    STATUS_CHOICES = (
        ('ATTEMPTED', 'Attempted'),
        ('EXECUTED', 'Executed Successfully'),
        ('REJECTED_BAD_CONFIRMATION', 'Rejected - Bad Confirmation Challenge'),
        ('FAILED', 'Failed / Execution Error'),
    )
    admin = models.ForeignKey(
        'accounts.AdminProfile', on_delete=models.RESTRICT, related_name='audit_logs'
    )
    action_type = models.CharField(max_length=40, choices=ACTION_CHOICES)
    target_entity = models.CharField(max_length=100)
    query_or_command = models.TextField()
    justification_reason = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    status = models.CharField(max_length=35, choices=STATUS_CHOICES, default='EXECUTED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.action_type} on {self.target_entity} by {self.admin}"
