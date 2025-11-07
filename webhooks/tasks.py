import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import Webhook, WebhookLog
from payments.models import Transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=settings.WEBHOOK_MAX_RETRIES)
def send_webhook_notification(self, transaction_id, event_type):
    """
    Send webhook notification for transaction event

    Args:
        transaction_id (str): UUID of the transaction
        event_type (str): Type of event (e.g., 'transaction.succeeded')

    Returns:
        dict: Notification result
    """
    try:
        # Get transaction
        transaction = Transaction.objects.select_related('merchant').get(id=transaction_id)

        # Get active webhooks for the merchant
        webhooks = Webhook.objects.filter(
            merchant=transaction.merchant,
            is_active=True
        )

        if not webhooks.exists():
            logger.info(f"No active webhooks for merchant {transaction.merchant.email}")
            return {'status': 'no_webhooks'}

        # Prepare payload
        payload = {
            'event': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': {
                'transaction_id': str(transaction.id),
                'payment_key': transaction.payment_key,
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'status': transaction.status,
                'merchant_id': str(transaction.merchant.id),
                'created_at': transaction.created_at.isoformat(),
                'processed_at': transaction.processed_at.isoformat() if transaction.processed_at else None,
            }
        }

        # Send to each webhook
        results = []
        for webhook in webhooks:
            result = _send_single_webhook(webhook, transaction, event_type, payload)
            results.append(result)

        return {'status': 'sent', 'results': results}

    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
        return {'status': 'error', 'message': 'Transaction not found'}

    except Exception as exc:
        logger.error(f"Error sending webhook notification: {str(exc)}")
        raise


def _send_single_webhook(webhook, transaction, event_type, payload):
    """
    Send webhook to a single URL with retry logic

    Args:
        webhook (Webhook): Webhook instance
        transaction (Transaction): Transaction instance
        event_type (str): Event type
        payload (dict): Webhook payload

    Returns:
        dict: Send result
    """
    # Create or get webhook log
    webhook_log = WebhookLog.objects.create(
        webhook=webhook,
        transaction=transaction,
        event_type=event_type,
        payload=payload,
        status='pending'
    )

    max_attempts = 1 + settings.WEBHOOK_MAX_RETRIES  # Initial attempt + retries
    attempt = 0

    while attempt < max_attempts:
        try:
            logger.info(f"Sending webhook to {webhook.url} (attempt {attempt + 1}/{max_attempts})")

            # Send POST request
            response = requests.post(
                webhook.url,
                json=payload,
                timeout=settings.WEBHOOK_TIMEOUT_SECONDS,
                headers={'Content-Type': 'application/json'}
            )

            # Update log
            webhook_log.retry_count = attempt
            webhook_log.last_attempt_at = timezone.now()
            webhook_log.response_status = response.status_code
            webhook_log.response_body = response.text[:1000]  # Limit response body size

            # Check if successful
            if 200 <= response.status_code < 300:
                webhook_log.status = 'sent'
                webhook_log.save()
                logger.info(f"Webhook sent successfully to {webhook.url}")
                return {
                    'webhook_id': str(webhook.id),
                    'status': 'sent',
                    'status_code': response.status_code
                }
            else:
                logger.warning(
                    f"Webhook failed with status {response.status_code}: {response.text[:200]}"
                )

        except requests.exceptions.Timeout:
            logger.warning(f"Webhook timeout for {webhook.url}")
            webhook_log.response_body = 'Request timeout'

        except requests.exceptions.RequestException as e:
            logger.warning(f"Webhook request failed for {webhook.url}: {str(e)}")
            webhook_log.response_body = f'Request error: {str(e)[:500]}'

        except Exception as e:
            logger.error(f"Unexpected error sending webhook: {str(e)}")
            webhook_log.response_body = f'Unexpected error: {str(e)[:500]}'

        # Increment attempt
        attempt += 1

        # If not the last attempt, wait before retry
        if attempt < max_attempts:
            import time
            logger.info(f"Retrying in {settings.WEBHOOK_RETRY_DELAY_SECONDS} seconds...")
            time.sleep(settings.WEBHOOK_RETRY_DELAY_SECONDS)

    # All attempts failed
    webhook_log.status = 'failed'
    webhook_log.retry_count = max_attempts - 1
    webhook_log.last_attempt_at = timezone.now()
    webhook_log.save()

    logger.error(f"Webhook failed after {max_attempts} attempts to {webhook.url}")
    return {
        'webhook_id': str(webhook.id),
        'status': 'failed',
        'attempts': max_attempts
    }
