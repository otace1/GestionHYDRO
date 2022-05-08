from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from jsignature.forms import JSignatureField
from jsignature.widgets import JSignatureWidget

from enreg.models import *
from .models import MyUser, Roles

User = get_user_model()


# Login form pour la connextion des utilisateurs sur le systeme
class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user_qs_final = User.objects.filter(
            Q(username__iexact=username)
        ).distinct()

        if not user_qs_final.exists() and user_qs_final.count != 1:
            raise forms.ValidationError("Identifiants incorrects")

        user_obj = user_qs_final.first()
        if not user_obj.check_password(password):
            raise forms.ValidationError("Identifiants incorrects")
        return super(UserLoginForm, self).clean(*args, **kwargs)


# Form pour l'enregistrement de nouvel utilisateurs
class UserRegisterForm(forms.ModelForm):
    # first_name = forms.CharField(label='Prénom')
    # last_name = forms.CharField(label='Nom')
    # role = forms.ModelChoiceField(label='Rôle', queryset=Roles.objects.all())
    # fonction = forms.CharField(label='Fonction')
    # username = forms.CharField(label="Nom d'utilisateur")
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmation mot de passe', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'role']
        # , 'ville', 'entrepot', 'extras''

    def clean_password(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Mot de passe different")
        return password2

    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
        return user


# Modification de l'utilisateur
class UserEdit(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name', 'username', 'password', 'role', 'fonction']
#         ,'entrepot','ville','extras'

# Affectation des utilisateurs aux entrepots
class Affectation_Entrepot(forms.Form):
    # username = forms.ModelChoiceField(queryset=MyUser.objects.all(), label='Utilisateur')
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all().order_by('nomentrepot'),
                                      label="Entrepot d'affectation")


# Affectation des utilisateurs aux villes
class Affectation_Ville(forms.Form):
    # username = forms.ModelChoiceField(queryset=MyUser.objects.all(), label='Utilisateur')
    ville = forms.ModelChoiceField(queryset=Ville.objects.all(), label="Ville d'affectation")


# Affectation des utilisateurs aux roles
class Affectation_Role(forms.Form):
    username = forms.ModelChoiceField(queryset=MyUser.objects.all(), label='Utilisateur')
    role = forms.ModelChoiceField(queryset=Roles.objects.all(), label="Role d'utilisateur")


# Formulaire pour l'enregistrement des signatures electroniques
class SignatureForm(forms.Form):
    signature = JSignatureField(widget=JSignatureWidget(jsignature_attrs={'color': '#CCC'}))
