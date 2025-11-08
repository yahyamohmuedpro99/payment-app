from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from authentication.models import Merchant


class MerchantModelTest(TestCase):
    """Test cases for Merchant model"""

    def test_create_merchant(self):
        """Test creating a merchant with email and password"""
        merchant = Merchant.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(merchant.email, 'test@example.com')
        self.assertTrue(merchant.check_password('testpass123'))
        self.assertIsNotNone(merchant.api_key)
        self.assertGreater(len(merchant.api_key), 0)  # API key should exist

    def test_merchant_api_key_unique(self):
        """Test that each merchant gets a unique API key"""
        merchant1 = Merchant.objects.create_user(
            email='test1@example.com',
            password='pass123'
        )
        merchant2 = Merchant.objects.create_user(
            email='test2@example.com',
            password='pass123'
        )
        self.assertNotEqual(merchant1.api_key, merchant2.api_key)


class RegistrationAPITest(APITestCase):
    """Test cases for merchant registration endpoint"""

    def test_register_merchant(self):
        """Test successful merchant registration"""
        url = reverse('authentication:register')
        data = {
            'email': 'newmerchant@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('api_key', response.data['data'])
        self.assertIn('token', response.data['data'])
        self.assertEqual(response.data['data']['email'], 'newmerchant@example.com')

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails"""
        Merchant.objects.create_user(
            email='existing@example.com',
            password='pass123'
        )

        url = reverse('authentication:register')
        data = {
            'email': 'existing@example.com',
            'password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_register_invalid_email(self):
        """Test registration with invalid email fails"""
        url = reverse('authentication:register')
        data = {
            'email': 'notanemail',
            'password': 'pass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_register_short_password(self):
        """Test registration with short password fails"""
        url = reverse('authentication:register')
        data = {
            'email': 'test@example.com',
            'password': '123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class LoginAPITest(APITestCase):
    """Test cases for merchant login endpoint"""

    def setUp(self):
        """Create a test merchant"""
        self.merchant = Merchant.objects.create_user(
            email='login@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Test successful login"""
        url = reverse('authentication:login')
        data = {
            'email': 'login@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data['data'])
        self.assertIn('api_key', response.data['data'])

    def test_login_wrong_password(self):
        """Test login with wrong password fails"""
        url = reverse('authentication:login')
        data = {
            'email': 'login@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_nonexistent_user(self):
        """Test login with non-existent email fails"""
        url = reverse('authentication:login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'pass123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
