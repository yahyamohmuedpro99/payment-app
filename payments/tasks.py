import time
import random
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import Transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_transaction(self, transaction_id):
    """
    Process a transaction asynchronously with simulated delay

    Args:
        transaction_id (str): UUID of the transaction to process

    Returns:
        dict: Processing result with status and transaction ID
    """
    try:
        # Get the transaction
        transaction = Transaction.objects.get(id=transaction_id)

        # Update status to processing
        transaction.status = 'processing'
        transaction.save(update_fields=['status', 'updated_at'])

        logger.info(f"Processing transaction {transaction.payment_key}")

        # Simulate processing delay (3-5 seconds)
        delay = random.uniform(
            settings.TRANSACTION_PROCESSING_MIN_DELAY,
            settings.TRANSACTION_PROCESSING_MAX_DELAY
        )
        time.sleep(delay)

        # Determine success based on configured rate
        success = random.random() < settings.TRANSACTION_SUCCESS_RATE

        if success:
            transaction.status = 'succeeded'
            transaction.failure_reason = None
            logger.info(f"Transaction {transaction.payment_key} succeeded")
        else:
            transaction.status = 'failed'
            transaction.failure_reason = 'Payment processing failed (simulated failure)'
            logger.warning(f"Transaction {transaction.payment_key} failed")

        transaction.processed_at = timezone.now()
        transaction.save(update_fields=['status', 'failure_reason', 'processed_at', 'updated_at'])

        # Trigger webhook notification
        from webhooks.tasks import send_webhook_notification
        send_webhook_notification.delay(transaction_id, f'transaction.{transaction.status}')

        return {
            'status': transaction.status,
            'transaction_id': str(transaction_id),
            'payment_key': transaction.payment_key
        }

    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
        raise

    except Exception as exc:
        logger.error(f"Error processing transaction {transaction_id}: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60)
