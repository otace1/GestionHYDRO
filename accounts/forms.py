from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from jsignature.forms import JSignatureField
from jsignature.widgets import JSignatureWidget
from crispy_forms.layout import Layout, Row, Column, Submit, Reset, Field
from enreg.models import *
from .models import MyUser, Roles, ListeLaboratoire

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
# class UserRegisterForm(forms.ModelForm):
#     # first_name = forms.CharField(label='Prénom')
#     # last_name = forms.CharField(label='Nom')
#     # role = forms.ModelChoiceField(label='Rôle', queryset=Roles.objects.all())
#     # fonction = forms.CharField(label='Fonction')
#     # username = forms.CharField(label="Nom d'utilisateur")
#     password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
#     password2 = forms.CharField(label='Confirmation mot de passe', widget=forms.PasswordInput)
#
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'username', 'role']
#         # , 'ville', 'entrepot', 'extras''
#
#     def clean_password(self):
#         password1 = self.cleaned_data.get('password1')
#         password2 = self.cleaned_data.get('password2')
#
#         if password1 and password2 and password1 != password2:
#             raise forms.ValidationError("Mot de passe different")
#         return password2
#
#     def save(self, commit=True):
#         user = super(UserRegisterForm, self).save(commit=False)
#         user.set_password(self.cleaned_data['password1'])
#
#         if commit:
#             user.save()
#         return user
#
#     def __init__(self, *args, **kwargs):
#         super(UserRegisterForm, self).__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_class = 'form-horizontal'
#         self.helper.form_id = 'registration-form'
#         self.helper.label_class = 'col-md-12'
#         self.helper.field_class = 'col-md-12'
#         self.helper.layout = Layout(
#             Row('produit', css_class='form-group col-md-6')
#             ),
#             Row('produit', css_class='form-group col-md-6'),
#             ),
#             Row('produit', css_class='form-group col-md-6'),
#             ),
#             FormActions(
#                 Submit('VALIDER', 'VALIDER', css_class='btn btn-success'),
#                 Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
#             ),
#         );
#         )

class UserRegisterForm(forms.ModelForm):
    first_name = forms.CharField(label='Prénom')
    last_name = forms.CharField(label='Nom')
    role = forms.ModelChoiceField(label='Rôle', queryset=Roles.objects.all())
    fonction = forms.CharField(label='Fonction')
    username = forms.CharField(label="Nom d'utilisateur")
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmation mot de passe', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'role']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row("",
                Column('first_name', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            Row("",
                Column('last_name', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('role', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            # Field('role', placeholder=""),
            Row(
                Column('fonction', css_class='form-group col-md-12 mb-0'),

            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'

            ),
            # Row(
            #     Column('fonction', css_class='form-group col-md-6 mb-0'),
            #
            # ),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )



# Modification de l'utilisateur
class UserEdit(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name', 'username', 'password', 'role', 'fonction','poste']
#         ,'entrepot','ville','extras'



# Affectation des utilisateurs aux entrepots
class Affectation_Entrepot(forms.Form):
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all().order_by('nomentrepot'),
                                      label="Sélectionner l'entrepôt d'affectation")
    def __init__(self, *args, **kwargs):
        super(Affectation_Entrepot, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
     Row("",
                Column('entrepot', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )



# Affectation des utilisateurs aux villes
class Affectation_Ville(forms.Form):
    ville = forms.ModelChoiceField(queryset=Ville.objects.all(), label="Sélectionner la ville d'affectation")

    def __init__(self, *args, **kwargs):
        super(Affectation_Ville, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
     Row("",
                Column('ville', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )



class Affectation_Labo(forms.Form):
    laboratoire = forms.ModelChoiceField(queryset=ListeLaboratoire.objects.all(), label="Sélectionner le laboratoire d'affectation")

    def __init__(self, *args, **kwargs):
        super(Affectation_Labo, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
     Row("",
                Column('laboratoire', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )





# Affectation des utilisateurs aux roles
class Affectation_Role(forms.Form):
    role = forms.ModelChoiceField(queryset=Roles.objects.all(), label="Sélectionnez le nouveau rôle")

    def __init__(self, *args, **kwargs):
        super(Affectation_Role, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
     Row("",
                Column('role', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )



# Formulaire pour l'enregistrement des signatures electroniques
class SignatureForm(forms.Form):
    signature = JSignatureField(widget=JSignatureWidget(jsignature_attrs={'color': '#CCC'}))
