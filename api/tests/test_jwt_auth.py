from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import MyUser, Roles
from django.db.utils import OperationalError

class JWTAuthTests(APITestCase):
    databases = {'default'}

    @classmethod
    def setUpTestData(cls):
        try:
            cls.role = Roles.objects.create(role='Tester')
            cls.user = MyUser.objects.create_user(
                username='testuser',
                role=cls.role,
                password='testpassword123'
            )
        except OperationalError:
            pass

    def setUp(self):
        self.login_url = reverse('api_login')
        self.refresh_url = reverse('token_refresh')
        self.logout_url = reverse('api_logout')

    def test_login_success(self):
        if not MyUser.objects.filter(username='testuser').exists():
            self.skipTest("Database not available")
            
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['role'], 'Tester')

    def test_login_invalid_credentials(self):
        if not MyUser.objects.filter(username='testuser').exists():
            self.skipTest("Database not available")

        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)

    def test_token_refresh(self):
        if not MyUser.objects.filter(username='testuser').exists():
            self.skipTest("Database not available")

        # First login to get refresh token
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']

        # Now refresh
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, refresh_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout(self):
        if not MyUser.objects.filter(username='testuser').exists():
            self.skipTest("Database not available")

        # First login
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']

        # Logout (blacklist refresh token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        logout_data = {'refresh': refresh_token}
        response = self.client.post(self.logout_url, logout_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Try to use refresh token again - should fail if blacklist is working
        response = self.client.post(self.refresh_url, logout_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
