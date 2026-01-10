import json

from dotenv import load_dotenv
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.conf import settings
from jsignature.mixins import JSignatureFieldsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import jwt
import firebase_admin
from firebase_admin import credentials, auth
import datetime
import os

#Env File loading here
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

from enreg.models import Entrepot, Ville

USERNAME_REGEX = '^[a-zA-Z0-9.+-]*$'


# Tables des roles
class AuditedQuerySet(models.QuerySet):
    def update(self, **kwargs):
        # We import here to avoid circular dependency
        from .services import log_bulk_audit
        log_bulk_audit(self, 'BULK_UPDATE', changes={'updated_fields': list(kwargs.keys()), 'values': kwargs})
        return super().update(**kwargs)

    def delete(self):
        from .services import log_bulk_audit
        log_bulk_audit(self, 'BULK_DELETE')
        return super().delete()


class AuditedManager(models.Manager):
    def get_queryset(self):
        return AuditedQuerySet(self.model, using=self._db)


class Roles(models.Model):
    idrole = models.AutoField(primary_key=True, auto_created=True)
    role = models.CharField(max_length=32, verbose_name='Role')

    objects = AuditedManager()

    def __str__(self):
        return self.role

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idrole})

    def natural_key(self):
        return self.my_natural_key


class MyUserManager(BaseUserManager):
    def create_user(self, username, role, password=None):
        if not username:
            raise ValueError("Nom d'utilisateur invalid")
        user = self.model(
            username=username,
            role=role
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, role, password=None):
        user = self.create_user(username, role, password=password)
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user


# Table des utilisateurs
class MyUser(AbstractBaseUser):
    username = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(regex=USERNAME_REGEX,
                           message="Le nom d'utilisateur doit etre alphanumerique",
                           code="Nom d'utilisateur invalid"
                           )], unique=True)

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True)
    fonction = models.CharField(max_length=256, null=True, blank=True)
    poste = models.CharField(max_length=100, null=True, blank=True)
    # fonctions = models.CharField(max_length=256, null=True, blank=True)
    # signature = JSignatureField(blank=True, null=True)

    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role']

    objects = MyUserManager()

    def has_perm(self, perm, obj=None):
        "L'utilisateur a t'il des permissions specifiques?"
        return True

    def has_module_perms(self, app_label):
        "L'utilisateur a t'il l apermissions de voir une appli?"
        return True

    def get_absolute_url(self):
        return reverse('edit', kwargs={'pk': self.id})

    def natural_key(self):
        return self.my_natural_key

    @property
    def token(self):
        """
        Allows us to get a user's token by calling `user.token` instead of
        `user.generate_jwt_token().
        The `@property` decorator above makes this possible. `token` is called
        a "dynamic property".
        """
        return self._generate_jwt_token()

    def refreshToken(self):
        """
        Get Refresh Token for user continues access to data
        """
        return self._generate_jwt_refresh_token()

    def get_full_name(self):
        """
        This method is required by Django for things like handling emails.
        Typically this would be the user's first and last name. Since we do
        not store the user's real name, we return their username instead.
        """
        return self.first_name + " " + self.last_name


    def _generate_jwt_token(self):
        """
                        Generates a JSON Web Token that stores this user's ID and has an expiry
                        date set to 60 days into the future.
        """
        if not firebase_admin._apps:

            # Load Firebase config from JSON file
            with open('hydrocarbures/firebaseData.json') as f:
                firebase_config = json.load(f)

            crt = {
                "type": firebase_config.get("type"),
                "project_id": firebase_config.get("project_id"),
                "private_key_id": firebase_config.get("private_key_id"),
                "private_key": firebase_config.get("private_key"),
                "client_email": firebase_config.get("client_email"),
                "client_id": firebase_config.get("client_id"),
                "auth_uri": firebase_config.get("auth_uri"),
                "token_uri": firebase_config.get("token_uri"),
                "auth_provider_x509_cert_url": firebase_config.get("auth_provider_x509_cert_url"),
                "client_x509_cert_url": firebase_config.get("client_x509_cert_url")
            }

            cred = credentials.Certificate(crt)
            firebase_admin.initialize_app(cred)

        additional_claims = {
            'names': self.get_full_name(),
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

        uid = str(self.id)
        token = auth.create_custom_token(uid, additional_claims)
        return token

    def _generate_jwt_refresh_token(self):
        refresh_token_payload = {
            'user_id': self.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'iat': datetime.datetime.utcnow()
        }

        refresh_token = jwt.encode(
            refresh_token_payload, settings.SECRET_KEY, algorithm='HS256')

        return refresh_token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


# Tables des affectations aux entrepots
class AffectationEntrepot(models.Model):
    idaffectation_entrepot = models.AutoField(primary_key=True, auto_created=True)
    username = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE)

    def __str__(self):
        return self.idaffectation_entrepot

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idaffectation_entrepot})

    def natural_key(self):
        return self.my_natural_key


# Tables des affectations aux villes
class AffectationVille(models.Model):
    idaffectation_ville = models.AutoField(primary_key=True, auto_created=True)
    username = models.ForeignKey(MyUser, on_delete=models.PROTECT)
    ville = models.ForeignKey(Ville, on_delete=models.PROTECT)


class SignaturesModel(models.Model):
    idSignature = models.AutoField(primary_key=True, auto_created=True)
    userId = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='signature')
    signatureData = models.BinaryField()
    updated_at = models.DateTimeField(auto_now=True)


# # Gestion des signatures electroniques
# class SignatureModel(JSignatureFieldsMixin):
#     username = models.IntegerField(null=True, blank=True)


class ListeLaboratoire(models.Model):
    idLaboratoire = models.AutoField(primary_key=True, auto_created=True)
    denominationLaboratoire = models.CharField(max_length=64, blank=True, null=True)
    adresseLaboratoire = models.CharField(max_length=64, blank=True, null=True)
    typeLaboratoire = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.denominationLaboratoire


class AffectationLaboratoire(models.Model):
    idAffectation = models.AutoField(primary_key=True, auto_created=True)
    idLaboratoire = models.ForeignKey(ListeLaboratoire, on_delete=models.PROTECT)
    userId = models.ForeignKey(MyUser, on_delete=models.PROTECT)
    ville = models.ForeignKey(Ville,on_delete=models.PROTECT)
    signGauche = models.BooleanField(null=True, blank=True)




#Table to follow activity Logs
class UserActivityLog(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    user = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)
    username_snapshot = models.CharField(max_length=150, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    action = models.CharField(max_length=100, db_index=True)
    module = models.CharField(max_length=100, db_index=True, null=True, blank=True)

    object_type = models.CharField(max_length=100, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    object_repr = models.CharField(max_length=255, null=True, blank=True)

    description = models.TextField()

    request_method = models.CharField(max_length=10, null=True, blank=True)
    path = models.CharField(max_length=255, null=True, blank=True)
    query_params = models.JSONField(null=True, blank=True)
    request_body_summary = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)

    status = models.CharField(max_length=20, default='success')
    http_status_code = models.IntegerField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    extra = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['module']),
        ]

    def __str__(self):
        user_str = self.username_snapshot or (self.user.username if self.user else 'System')
        return f"{user_str} - {self.action} - {self.timestamp}"


class AuditLog(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Actor details
    actor = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)
    actor_username_snapshot = models.CharField(max_length=150, null=True, blank=True)
    actor_type = models.CharField(max_length=20, default='user') # user, system, api
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    request_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    
    # Object details
    app_label = models.CharField(max_length=100, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    object_pk = models.CharField(max_length=255, db_index=True)
    object_repr = models.CharField(max_length=255, null=True, blank=True)
    
    # Action details
    action = models.CharField(max_length=20, db_index=True) # CREATE, UPDATE, DELETE, BULK_UPDATE, BULK_DELETE
    changes = models.JSONField(null=True, blank=True) # {field: {from: X, to: Y}}
    new_state = models.JSONField(null=True, blank=True) # for CREATE
    old_state = models.JSONField(null=True, blank=True) # for DELETE
    
    # Status
    status = models.CharField(max_length=20, default='success')
    error_message = models.TextField(null=True, blank=True)
    
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['actor']),
            models.Index(fields=['model_name']),
            models.Index(fields=['object_pk']),
            models.Index(fields=['action']),
            models.Index(fields=['request_id']),
        ]

    def __str__(self):
        actor_str = self.actor_username_snapshot or (self.actor.username if self.actor else 'System')
        return f"{actor_str} - {self.action} - {self.model_name}({self.object_pk}) - {self.timestamp}"