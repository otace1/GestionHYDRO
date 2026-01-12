from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from crispy_forms.bootstrap import FormActions
from enreg.models import BureauDGDA, Banques, LiquidationModel, Importateur, Entrepot, Ville, Produit, Voie

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

class ImportateurForm(forms.ModelForm):
    class Meta:
        model = Importateur
        fields = ['nomimportateur', 'adresseimportateur', 'nifimportateur', 'email']
        labels = {
            'nomimportateur': "Nom de l'Importateur",
            'adresseimportateur': 'Adresse',
            'nifimportateur': 'NIF',
            'email': 'Email',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nomimportateur', css_class='form-group col-md-6 mb-0'),
                Column('nifimportateur', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('adresseimportateur', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
        )

class EntrepotForm(forms.ModelForm):
    class Meta:
        model = Entrepot
        fields = ['nomentrepot', 'adresseentrepot', 'ville']
        labels = {
            'nomentrepot': "Nom de l'Entrepôt",
            'adresseentrepot': 'Adresse Physique',
            'ville': 'Ville',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nomentrepot', css_class='form-group col-md-6 mb-0'),
                Column('ville', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('adresseentrepot', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
        )

class VilleForm(forms.ModelForm):
    class Meta:
        model = Ville
        fields = ['nomville', 'province']
        labels = {
            'nomville': 'Nom de la Ville',
            'province': 'Province',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nomville', css_class='form-group col-md-6 mb-0'),
                Column('province', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
        )

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nomproduit']
        labels = {
            'nomproduit': 'Nom du Produit',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nomproduit', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
        )

class VoieForm(forms.ModelForm):
    class Meta:
        model = Voie
        fields = ['nomvoie']
        labels = {
            'nomvoie': "Nom de la Voie",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('nomvoie', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
        )
