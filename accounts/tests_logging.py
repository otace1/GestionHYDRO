from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import UserActivityLog, AuditLog
from accounts.services import log_action, sanitize_data
from django.utils import timezone
import json

User = get_user_model()

class LoggingSystemTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # MyUser.create_user takes username, role, password
        from accounts.models import Roles
        self.role = Roles.objects.create(role='Admin')
        self.user = User.objects.create_user(username='testuser', role=self.role, password='password123')

    def test_sanitize_data(self):
        data = {
            'username': 'testuser',
            'password': 'secretpassword',
            'nested': {
                'token': 'secrettoken',
                'other': 'safe'
            },
            'card_number': '1234-5678',
            'api_key': 'abc-123'
        }
        sanitized = sanitize_data(data)
        self.assertEqual(sanitized['password'], '********')
        self.assertEqual(sanitized['nested']['token'], '********')
        self.assertEqual(sanitized['card_number'], '********')
        self.assertEqual(sanitized['api_key'], '********')
        self.assertEqual(sanitized['username'], 'testuser')
        self.assertEqual(sanitized['nested']['other'], 'safe')

    def test_log_action_with_request(self):
        UserActivityLog.objects.all().delete()
        request = self.factory.get('/some-path/')
        request.user = self.user
        
        log_action(request, 'TEST_ACTION', 'Test description')
        
        log = UserActivityLog.objects.filter(action='TEST_ACTION').last()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.path, '/some-path/')
        self.assertEqual(log.username_snapshot, 'testuser')

    def test_log_action_without_request(self):
        UserActivityLog.objects.all().delete()
        log_action(None, 'SYSTEM_ACTION', 'System description')
        
        log = UserActivityLog.objects.filter(action='SYSTEM_ACTION').last()
        self.assertIsNotNone(log)
        self.assertIsNone(log.user)
        self.assertEqual(log.username_snapshot, 'System')

    def test_log_action_with_user_no_request(self):
        UserActivityLog.objects.all().delete()
        log_action(None, 'TASK_ACTION', 'Task description', user=self.user, module='test_module')
        
        log = UserActivityLog.objects.filter(action='TASK_ACTION').last()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.username_snapshot, 'testuser')
        self.assertEqual(log.module, 'test_module')

    def test_log_action_keyword_only(self):
        UserActivityLog.objects.all().delete()
        log_action(action='KEYWORD_ACTION', description='Keyword only call')
        
        log = UserActivityLog.objects.filter(action='KEYWORD_ACTION').last()
        self.assertIsNotNone(log)
        self.assertEqual(log.username_snapshot, 'System')

    def test_logging_does_not_crash_on_error(self):
        # This should not raise an exception even if obj is weird
        log_action(None, 'CRASH_TEST', obj="not a model object")
        
        # Verify that we didn't break execution
        self.assertTrue(True)

    def test_activity_log_response_filters(self):
        UserActivityLog.objects.create(user=self.user, action='ACTION1', description='Desc 1', status='success')
        UserActivityLog.objects.create(user=self.user, action='ACTION2', description='Desc 2', status='failure')
        
        self.client.login(username='testuser', password='password123')
        
        # Test action filter
        response = self.client.post(reverse('activityLogResponse'), {'action': 'ACTION1', 'source': 'activity'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['recordsFiltered'], 1)
        self.assertEqual(data['data'][0]['action'], 'ACTION1')
        
        # Test global search
        response = self.client.post(reverse('activityLogResponse'), {'q': 'Desc 2', 'source': 'activity'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['recordsFiltered'], 1)
        self.assertEqual(data['data'][0]['description'], 'Desc 2')

    def test_middleware_request_storage(self):
        from accounts.middleware import get_current_request
        request = self.factory.get('/')
        request.user = self.user
        
        from accounts.middleware import RequestStoreMiddleware
        def get_response(req):
            self.assertEqual(get_current_request(), req)
            return None
            
        middleware = RequestStoreMiddleware(get_response)
        middleware(request)
        
        # Should be cleared after request
        self.assertIsNone(get_current_request())

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_activity_log_purge(self):
        # Create some old logs
        old_date = timezone.now() - timezone.timedelta(days=100)
        u1 = UserActivityLog.objects.create(user=self.user, action='OLD', description='Old activity')
        UserActivityLog.objects.filter(id=u1.id).update(timestamp=old_date)

        a1 = AuditLog.objects.create(actor=self.user, action='OLD', app_label='accounts', model_name='MyUser', object_pk='1')
        AuditLog.objects.filter(id=a1.id).update(timestamp=old_date)

        # Create some recent logs
        UserActivityLog.objects.create(user=self.user, action='NEW', description='New activity')
        AuditLog.objects.create(actor=self.user, action='NEW', app_label='accounts', model_name='MyUser', object_pk='1')

        self.client.login(username='testuser', password='password123')

        # Call purge for logs older than 90 days
        response = self.client.post(reverse('activityLogPurge'), {'days': '90'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')

        # Verify old logs are gone
        self.assertEqual(UserActivityLog.objects.filter(action='OLD').count(), 0)
        self.assertEqual(AuditLog.objects.filter(action='OLD').count(), 0)

        # Verify new logs remain
        self.assertEqual(UserActivityLog.objects.filter(action='NEW').count(), 1)
        self.assertEqual(AuditLog.objects.filter(action='NEW').count(), 1)

    def test_get_task_status_exception_serialization(self):
        """
        Verify that get_task_status correctly handles Exception objects in task_result.result.
        """
        from unittest.mock import patch, MagicMock
        
        with patch('accounts.views.AsyncResult') as mock_async_result:
            mock_task = MagicMock()
            mock_task.status = 'FAILURE'
            mock_task.result = TypeError("Some error message")
            mock_async_result.return_value = mock_task
            
            self.client.login(username='testuser', password='password123')
            response = self.client.get(reverse('task_status', kwargs={'task_id': 'fake-id'}))
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['task_status'], 'FAILURE')
            self.assertEqual(data['task_result'], "Some error message")
