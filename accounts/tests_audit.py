from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings
from accounts.models import AuditLog, Roles
from accounts.services import log_audit, audit_scope
from accounts.middleware import RequestStoreMiddleware
import json

User = get_user_model()

class AuditTrailTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Roles and User creation will trigger their own audit logs
        self.role = Roles.objects.create(role="Admin")
        self.user = User.objects.create_user(username="testuser", role=self.role, password="password123")
        self.user.first_name = "Test"
        self.user.last_name = "User"
        self.user.save()

    def test_create_log(self):
        # Model creation should trigger signal and create AuditLog
        new_role = Roles.objects.create(role="NewRole")
        log = AuditLog.objects.filter(model_name='roles', object_pk=str(new_role.pk), action='CREATE').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.new_state['role'], "NewRole")

    def test_update_log_with_diff(self):
        # Ensure we have a clean state
        role = Roles.objects.create(role="Initial")
        
        # Update
        role.role = "Updated"
        role.save()
        
        log = AuditLog.objects.filter(model_name='roles', object_pk=str(role.pk), action='UPDATE').first()
        self.assertIsNotNone(log)
        self.assertIn('role', log.changes)
        self.assertEqual(log.changes['role']['from'], "Initial")
        self.assertEqual(log.changes['role']['to'], "Updated")

    def test_delete_log(self):
        role = Roles.objects.create(role="ToDelete")
        pk = role.pk
        role.delete()
        
        log = AuditLog.objects.filter(model_name='roles', object_pk=str(pk), action='DELETE').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.old_state['role'], "ToDelete")

    def test_sanitization(self):
        # Test that sensitive fields are sanitized
        self.user.set_password("newpassword")
        self.user.save()
        
        log = AuditLog.objects.filter(model_name='myuser', object_pk=str(self.user.pk), action='UPDATE').first()
        self.assertIsNotNone(log, "AuditLog for MyUser update not found")
        # Check if password was recorded in changes and if it's sanitized
        if log.changes and 'password' in log.changes:
            self.assertEqual(log.changes['password']['to'], "********")

    def test_request_attribution(self):
        # Test that request info is captured via middleware
        request = self.factory.get('/some-path/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent'
        request.headers = {}
        
        def mock_view(r):
            Roles.objects.create(role="RequestRole")
            return None
            
        middleware = RequestStoreMiddleware(mock_view)
        middleware(request)
        
        log = AuditLog.objects.filter(action='CREATE', object_repr__contains="RequestRole").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertEqual(log.user_agent, 'TestAgent')
        self.assertIsNotNone(log.request_id)

    def test_audit_scope(self):
        with audit_scope(action="IMPORT_ROLES", extra={"batch_id": "123"}):
            Roles.objects.create(role="ScopedRole")
            
        log = AuditLog.objects.filter(action="IMPORT_ROLES", object_repr__contains="ScopedRole").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.extra.get('batch_id'), "123")

    def test_recursion_prevention(self):
        # Creating an AuditLog should not create another AuditLog because it's in EXCLUDE_MODELS
        initial_count = AuditLog.objects.count()
        AuditLog.objects.create(
            action="TEST", 
            app_label="accounts", 
            model_name="auditlog", # This should be excluded via settings
            object_pk="1"
        )
        # Should be +1 (the one we manually created) and NOT +2 (which would happen if signals were active for it)
        # Note: In Django, signals still trigger but is_audited() should return False
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)

    def test_bulk_operations(self):
        # Test that bulk update is logged
        Roles.objects.all().update(role="BulkUpdated")
        log = AuditLog.objects.filter(action="BULK_UPDATE", model_name="roles").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.object_pk, "MULTIPLE")
        self.assertIn("Bulk BULK_UPDATE on", log.object_repr)
        self.assertIn("role", log.changes['updated_fields'])

    def test_bulk_delete(self):
        Roles.objects.filter(role="BulkUpdated").delete()
        log = AuditLog.objects.filter(action="BULK_DELETE", model_name="roles").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.object_pk, "MULTIPLE")
