from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from payment_api.utils import api_response
from .models import Webhook
from .serializers import WebhookSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_webhook(request):
    """Register a new webhook"""
    serializer = WebhookSerializer(data=request.data)

    if serializer.is_valid():
        webhook = serializer.save(merchant=request.user)
        response_serializer = WebhookSerializer(webhook)

        return api_response(
            success=True,
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return api_response(
        success=False,
        error=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_webhooks(request):
    """List all webhooks for the authenticated merchant"""
    webhooks = Webhook.objects.filter(merchant=request.user)
    serializer = WebhookSerializer(webhooks, many=True)

    return api_response(
        success=True,
        data=serializer.data
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_webhook(request, webhook_id):
    """Delete a webhook"""
    try:
        webhook = Webhook.objects.get(
            id=webhook_id,
            merchant=request.user
        )
        webhook.delete()

        return api_response(
            success=True,
            data={'message': 'Webhook deleted successfully'}
        )

    except Webhook.DoesNotExist:
        return api_response(
            success=False,
            error='Webhook not found',
            status_code=status.HTTP_404_NOT_FOUND
        )
