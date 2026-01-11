from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from crispy_forms.bootstrap import FormActions
from enreg.models import BureauDGDA, Banques, LiquidationModel

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'fonction', 'poste']
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'username': "Nom d'utilisateur",
            'fonction': 'Fonction',
            'poste': 'Poste',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('fonction', css_class='form-group col-md-6 mb-0'),
                Column('poste', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Mettre à jour le profil', css_class='btn btn-primary px-4'),
            )
        )

class BureauDGDAForm(forms.ModelForm):
    class Meta:
        model = BureauDGDA
        fields = ['codebureau', 'descriptionbureau']
        labels = {
            'codebureau': 'Code Bureau',
            'descriptionbureau': 'Description',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('codebureau', css_class='form-group col-md-4 mb-0'),
                Column('descriptionbureau', css_class='form-group col-md-8 mb-0'),
                css_class='form-row'
            ),
        )

class BanqueForm(forms.ModelForm):
    class Meta:
        model = Banques
        fields = ['nombanque']
        labels = {
            'nombanque': 'Nom de la Banque',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nombanque', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
        )

class LiquidationModelForm(forms.ModelForm):
    class Meta:
        model = LiquidationModel
        fields = ['liquidationModel']
        labels = {
            'liquidationModel': 'Modèle de Liquidation',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('liquidationModel', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
        )
