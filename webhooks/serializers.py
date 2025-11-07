from rest_framework import serializers
from .models import Webhook, WebhookLog


class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for webhooks"""

    merchant_email = serializers.EmailField(source='merchant.email', read_only=True)

    class Meta:
        model = Webhook
        fields = ['id', 'merchant_email', 'url', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'merchant_email', 'created_at', 'updated_at']

    def validate_url(self, value):
        """Validate webhook URL"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError('URL must start with http:// or https://')
        return value


class WebhookLogSerializer(serializers.ModelSerializer):
    """Serializer for webhook logs"""

    webhook_url = serializers.URLField(source='webhook.url', read_only=True)
    transaction_payment_key = serializers.CharField(
        source='transaction.payment_key',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = WebhookLog
        fields = [
            'id', 'webhook_url', 'transaction_payment_key', 'event_type',
            'payload', 'status', 'retry_count', 'last_attempt_at',
            'response_status', 'response_body', 'created_at'
        ]
        read_only_fields = fields
