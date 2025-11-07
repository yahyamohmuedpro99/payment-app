import uuid
from django.db import models
from django.conf import settings


class Webhook(models.Model):
    """Model for webhook registration"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhooks'
        verbose_name = 'Webhook'
        verbose_name_plural = 'Webhooks'
        ordering = ['-created_at']
        unique_together = ['merchant', 'url']

    def __str__(self):
        return f"{self.merchant.email} - {self.url}"


class WebhookLog(models.Model):
    """Model for tracking webhook delivery attempts"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    EVENT_TYPE_CHOICES = [
        ('transaction.created', 'Transaction Created'),
        ('transaction.processing', 'Transaction Processing'),
        ('transaction.succeeded', 'Transaction Succeeded'),
        ('transaction.failed', 'Transaction Failed'),
        ('refund.created', 'Refund Created'),
        ('refund.succeeded', 'Refund Succeeded'),
        ('refund.failed', 'Refund Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.CASCADE,
        related_name='webhook_logs',
        null=True,
        blank=True
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    retry_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_logs'
        verbose_name = 'Webhook Log'
        verbose_name_plural = 'Webhook Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', 'status']),
            models.Index(fields=['transaction', 'event_type']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.webhook.url} - {self.status}"
