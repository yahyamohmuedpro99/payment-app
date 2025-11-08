from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from authentication.models import Merchant
from payments.models import Transaction, Refund
from decimal import Decimal


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )

    def test_create_transaction(self):
        """Test creating a transaction"""
        transaction = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD',
            description='Test payment'
        )
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.currency, 'USD')
        self.assertEqual(transaction.status, 'pending')
        self.assertIsNotNone(transaction.payment_key)
        self.assertGreaterEqual(len(transaction.payment_key), 32)  # Payment key should be at least 32 chars

    def test_transaction_payment_key_unique(self):
        """Test that each transaction gets a unique payment key"""
        transaction1 = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('50.00'),
            currency='USD'
        )
        transaction2 = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('75.00'),
            currency='USD'
        )
        self.assertNotEqual(transaction1.payment_key, transaction2.payment_key)


class RefundModelTest(TestCase):
    """Test cases for Refund model"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )
        self.transaction = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD',
            status='succeeded'
        )

    def test_create_refund(self):
        """Test creating a refund"""
        refund = Refund.objects.create(
            transaction=self.transaction,
            amount=Decimal('50.00'),
            reason='Customer request'
        )
        self.assertEqual(refund.amount, Decimal('50.00'))
        self.assertEqual(refund.reason, 'Customer request')
        self.assertEqual(refund.status, 'pending')


class TransactionAPITest(APITestCase):
    """Test cases for Transaction API endpoints"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )
        self.token = Token.objects.create(user=self.merchant)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_create_transaction(self):
        """Test creating a transaction via API"""
        url = reverse('payments:create-transaction')
        data = {
            'amount': '150.00',
            'currency': 'USD',
            'description': 'Test order'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['amount'], '150.00')
        self.assertEqual(response.data['data']['status'], 'pending')
        self.assertIsNotNone(response.data['data']['payment_key'])

    def test_create_transaction_invalid_amount(self):
        """Test creating transaction with invalid amount fails"""
        url = reverse('payments:create-transaction')
        data = {
            'amount': '-50.00',
            'currency': 'USD'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_transaction_unauthorized(self):
        """Test creating transaction without auth fails"""
        self.client.credentials()  # Remove credentials
        url = reverse('payments:create-transaction')
        data = {
            'amount': '100.00',
            'currency': 'USD'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_transactions(self):
        """Test listing transactions"""
        # Create some transactions
        Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD'
        )
        Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('200.00'),
            currency='EUR'
        )

        url = reverse('payments:list-transactions')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 2)

    def test_get_transaction(self):
        """Test getting a single transaction"""
        transaction = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD',
            description='Test'
        )

        url = reverse('payments:get-transaction', kwargs={'transaction_id': transaction.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['amount'], '100.00')
        self.assertEqual(response.data['data']['description'], 'Test')

    def test_get_other_merchant_transaction_fails(self):
        """Test that merchant cannot access another merchant's transaction"""
        other_merchant = Merchant.objects.create_user(
            email='other@example.com',
            password='pass123'
        )
        other_transaction = Transaction.objects.create(
            merchant=other_merchant,
            amount=Decimal('100.00'),
            currency='USD'
        )

        url = reverse('payments:get-transaction', kwargs={'transaction_id': other_transaction.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])


class RefundAPITest(APITestCase):
    """Test cases for Refund API endpoints"""

    def setUp(self):
        self.merchant = Merchant.objects.create_user(
            email='merchant@example.com',
            password='pass123'
        )
        self.token = Token.objects.create(user=self.merchant)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.transaction = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD',
            status='succeeded'
        )

    def test_create_refund(self):
        """Test creating a refund via API"""
        url = reverse('refunds:create-refund')
        data = {
            'transaction': str(self.transaction.id),
            'amount': '50.00',
            'reason': 'Customer request'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['amount'], '50.00')
        self.assertEqual(response.data['data']['reason'], 'Customer request')

    def test_create_refund_exceeds_amount(self):
        """Test creating refund that exceeds transaction amount fails"""
        url = reverse('refunds:create-refund')
        data = {
            'transaction': str(self.transaction.id),
            'amount': '150.00',
            'reason': 'Test'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_refund_for_pending_transaction(self):
        """Test creating refund for pending transaction fails"""
        pending_transaction = Transaction.objects.create(
            merchant=self.merchant,
            amount=Decimal('100.00'),
            currency='USD',
            status='pending'
        )

        url = reverse('refunds:create-refund')
        data = {
            'transaction': str(pending_transaction.id),
            'amount': '50.00',
            'reason': 'Test'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_duplicate_refund(self):
        """Test creating duplicate refund for same transaction fails"""
        # Create first refund
        Refund.objects.create(
            transaction=self.transaction,
            amount=Decimal('50.00'),
            reason='First refund'
        )

        # Try to create second refund
        url = reverse('refunds:create-refund')
        data = {
            'transaction': str(self.transaction.id),
            'amount': '25.00',
            'reason': 'Second refund'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_get_refund(self):
        """Test getting a single refund"""
        refund = Refund.objects.create(
            transaction=self.transaction,
            amount=Decimal('75.00'),
            reason='Customer request'
        )

        url = reverse('refunds:get-refund', kwargs={'refund_id': refund.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['amount'], '75.00')
        self.assertEqual(response.data['data']['reason'], 'Customer request')
