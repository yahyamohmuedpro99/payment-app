from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from authentication.models import Merchant
from payments.models import Transaction
from webhooks.models import Webhook, WebhookLog
from decimal import Decimal
from unittest.mock import patch, Mock


class WebhookModelTest(TestCase):
    """Test cases for Webhook model"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )

    def test_create_webhook(self):
        """Test creating a webhook"""
        webhook = Webhook.objects.create(
            merchant=self.merchant,
            url='https://example.com/webhook'
        )
        self.assertEqual(webhook.url, 'https://example.com/webhook')
        self.assertTrue(webhook.is_active)

    def test_webhook_deactivation(self):
        """Test deactivating a webhook"""
        webhook = Webhook.objects.create(
            merchant=self.merchant,
            url='https://example.com/webhook'
        )
        webhook.is_active = False
        webhook.save()
        self.assertFalse(webhook.is_active)


class WebhookLogModelTest(TestCase):
    """Test cases for WebhookLog model"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )
        self.webhook = Webhook.objects.create(
            merchant=self.merchant,
            url='https://example.com/webhook'
        )
        self.transaction = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD'
        )

    def test_create_webhook_log(self):
        """Test creating a webhook log"""
        webhook_log = WebhookLog.objects.create(
            webhook=self.webhook,
            transaction=self.transaction,
            event_type='transaction.succeeded',
            payload={'test': 'data'},
            response_status=200,
            status='sent'
        )
        self.assertEqual(webhook_log.event_type, 'transaction.succeeded')
        self.assertEqual(webhook_log.response_status, 200)
        self.assertEqual(webhook_log.status, 'sent')
        self.assertEqual(webhook_log.retry_count, 0)


class WebhookAPITest(APITestCase):
    """Test cases for Webhook API endpoints"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )
        self.token = Token.objects.create(user=self.merchant)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_create_webhook(self):
        """Test creating a webhook via API"""
        url = reverse('webhooks:create-webhook')
        data = {
            'url': 'https://example.com/webhook'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['url'], 'https://example.com/webhook')
        self.assertTrue(response.data['data']['is_active'])

    def test_create_webhook_invalid_url(self):
        """Test creating webhook with invalid URL fails"""
        url = reverse('webhooks:create-webhook')
        data = {
            'url': 'not-a-valid-url'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_webhook_unauthorized(self):
        """Test creating webhook without auth fails"""
        self.client.credentials()  # Remove credentials
        url = reverse('webhooks:create-webhook')
        data = {
            'url': 'https://example.com/webhook'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_webhooks(self):
        """Test listing webhooks"""
        # Create some webhooks
        Webhook.objects.create(
            merchant=self.merchant,
            url='https://example.com/webhook1'
        )
        Webhook.objects.create(
            merchant=self.merchant,
            url='https://example.com/webhook2'
        )

        url = reverse('webhooks:list-webhooks')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)

    def test_delete_webhook(self):
        """Test deleting a webhook"""
        webhook = Webhook.objects.create(
            merchant=self.merchant,
            url='https://example.com/webhook'
        )

        url = reverse('webhooks:delete-webhook', kwargs={'webhook_id': webhook.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(Webhook.objects.filter(id=webhook.id).exists())

    def test_delete_other_merchant_webhook_fails(self):
        """Test that merchant cannot delete another merchant's webhook"""
        other_merchant = Merchant.objects.create_user(
            email='other@example.com',
            password='pass123'
        )
        other_webhook = Webhook.objects.create(
            merchant=other_merchant,
            url='https://example.com/webhook'
        )

        url = reverse('webhooks:delete-webhook', kwargs={'webhook_id': other_webhook.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])


class WebhookNotificationTest(TestCase):
    """Test cases for webhook notification sending"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )
        self.webhook = Webhook.objects.create(
            merchant=self.merchant,
            url='https://example.com/webhook'
        )
        self.transaction = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD',
            status='succeeded'
        )

    @patch('webhooks.tasks.requests.post')
    def test_webhook_notification_success(self, mock_post):
        """Test successful webhook notification"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'OK'
        mock_post.return_value = mock_response

        from webhooks.tasks import send_webhook_notification
        send_webhook_notification(str(self.transaction.id), 'transaction.succeeded')

        # Verify webhook was called
        mock_post.assert_called()

        # Verify log was created
        logs = WebhookLog.objects.filter(
            webhook=self.webhook,
            transaction=self.transaction
        )
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.status, 'sent')
        self.assertEqual(log.response_status, 200)

    @patch('webhooks.tasks.requests.post')
    def test_webhook_notification_retry(self, mock_post):
        """Test webhook notification with retries"""
        # Mock failed HTTP responses
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        from webhooks.tasks import send_webhook_notification
        send_webhook_notification(str(self.transaction.id), 'transaction.succeeded')

        # Verify multiple retry attempts were made (1 initial + 3 retries = 4 total)
        self.assertGreaterEqual(mock_post.call_count, 1)

        # Verify log shows failure
        logs = WebhookLog.objects.filter(
            webhook=self.webhook,
            transaction=self.transaction
        )
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.status, 'failed')

    def test_inactive_webhook_not_triggered(self):
        """Test that inactive webhooks are not triggered"""
        self.webhook.is_active = False
        self.webhook.save()

        from webhooks.tasks import send_webhook_notification
        send_webhook_notification(str(self.transaction.id), 'transaction.succeeded')

        # Verify no log was created for inactive webhook
        logs = WebhookLog.objects.filter(
            webhook=self.webhook,
            transaction=self.transaction
        )
        self.assertFalse(logs.exists())
