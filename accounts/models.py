from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from jsignature.fields import JSignatureField
from jsignature.mixins import JSignatureFieldsMixin

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
    username = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)


# Gestion des signatures electroniques
class SignatureModel(JSignatureFieldsMixin):
    username = models.IntegerField(null=True, blank=True)

# #Tables des affectations des Roles des utilisateurs
# class AffectationRoles(models.Model):
#     idaffectation_roles = models.AutoField(primary_key=True, auto_created=True)
#     username = models.ForeignKey(MyUser, on_delete=models.CASCADE)
#     role = models.ForeignKey(Roles, on_delete=models.CASCADE)
