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
class Roles(models.Model):
    idrole = models.AutoField(primary_key=True, auto_created=True)
    role = models.CharField(max_length=32, verbose_name='Role')

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
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
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
            crt = {
                  "type": os.environ.get("TYPE"),
                  "project_id": os.environ.get("POJECT_ID"),
                  "private_key_id": os.environ.get("PRIVATE_KEY_ID"),
                  "private_key": os.environ.get("PRIVATE_KEY"),
                  "client_email": os.environ.get("CLIENT_EMAIL"),
                  "client_id": os.environ.get("CLIENT_ID"),
                  "auth_uri": os.environ.get("AUTH_URL"),
                  "token_uri": os.environ.get("TOKEN_URL"),
                  "auth_provider_x509_cert_url": os.environ.get("AUTH_PROVIDER"),
                  "client_x509_cert_url": os.environ.get("CLIENT_X509")
                }

            cred = credentials.Certificate(crt)
            default_app = firebase_admin.initialize_app(cred)

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
    userId = models.ForeignKey(MyUser, on_delete=models.PROTECT)
    signatureData = models.BinaryField()


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

