from crispy_forms.bootstrap import Field
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset
from django import forms
from django_countries.fields import CountryField
from enreg.models import *

from django.contrib.auth.decorators import login_required


class Ajoutcargaison(forms.Form):
    voie = forms.ModelChoiceField(queryset=Voie.objects.all(), label="TYPE VOIE D'ENTREE")
    fournisseur = forms.CharField(label='FOURNISSEUR', required=False)
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all().order_by('nomimportateur'),
                                         label="IMPORTATEUR")
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label="NATURE DU PRODUIT")
    frontiere = forms.ModelChoiceField(queryset=Ville.objects.all().order_by('nomville'), label="FRONTIERE D'ENTREE")
    provenance = CountryField().formfield()
    origine = CountryField().formfield()
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all().order_by('nomentrepot'),
                                      label="ENTREPOT DE DESTINATION")
    transporteur = forms.CharField(label="TRANSPORTEUR")
    declarant = forms.CharField(widget=forms.TextInput(), label="TRANSITAIRE")
    poids = forms.DecimalField(min_value=1, label="MASSE EN TONNE METRIQUE (MTA)")
    volume = forms.DecimalField(min_value=1, max_value=100, label="VOLUME DECL.")
    t1d = forms.CharField(label="T1D", required=False)
    t1e = forms.CharField(label="T1E", required=False)
    numdeclaration = forms.CharField(label="# DECLARATION", required=False)
    numbtfh = forms.CharField(label="NUMERO BT/LT/FICHE CHAUFFEUR", required=False)
    manifestdgda = forms.CharField(label='# MANIFESTE', required=False)
    immatriculation = forms.CharField(label="IMMATRICULATION")

    def __init__(self, *args, **kwargs):
        super(Ajoutcargaison, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('voie', css_class='form-group col-md-4 mb-0'),
                Column('frontiere', css_class='form-group col-md-4 mb-0'),
                Column('transporteur', placeholder='Nom du Fournisseur si applicable',
                       css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('fournisseur', placeholder='Nom du Fournisseur si applicable',
                       css_class='form-group col-md-6 mb-0'),
                Column('importateur', css_class='form-group col-md-6 mb-0'),
                Column('provenance', css_class='form-group col-md-6 mb-0'),
                Column('origine', css_class='form-group col-md-6 mb-0'),
                Column('entrepot', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('declarant', css_class='form-group col-md-4 mb-0'),
                Column('t1e', css_class='form-group col-md-2 mb-0'),
                Column('t1d', css_class='form-group col-md-2 mb-0'),
                Column('numdeclaration', css_class='form-group col-md-2 mb-0'),
                Column('manifestdgda', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'

            ),
            Row(
                Column('produit', css_class='form-group col-md-4 mb-0'),
                Column('poids', css_class='form-group col-md-4 mb-0'),
                Column('volume', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'

            ),
            Row(
                Column('immatriculation', css_class='form-group col-md-6 mb-0'),
                Column('numbtfh', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'

            ),
        )
