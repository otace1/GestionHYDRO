from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Field
from django import forms
from django.utils.translation import gettext_lazy as _

from enreg.models import *


class Ajoutcargaison(forms.Form):
    voie = forms.ModelChoiceField(
        queryset=Voie.objects.all(), 
        label=_("Type Voie d'Entrée"),
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )
    frontiere = forms.ModelChoiceField(
        queryset=Ville.objects.all().order_by('nomville'), 
        label=_("Frontière d'Entrée"),
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )
    typeunitetransport = forms.ModelChoiceField(
        queryset=TypeUniteTransport.objects.all().order_by('unitetransport'),
        label=_("Type d'Unité de Transport"), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )
    provenance = CountryField().formfield(
        label=_("Provenance"),
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )
    importateur = forms.ModelChoiceField(
        queryset=Importateur.objects.all().order_by('nomimportateur'),
        label=_("Fournisseur / Importateur"), 
        required=True,
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all(), 
        label=_("Nature du Produit"),
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )
    entrepot = forms.ModelChoiceField(
        queryset=Entrepot.objects.all().order_by('nomentrepot'),
        label=_("Entrepôt de Destination"),
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )
    immatriculation = forms.CharField(
        label=_("Immatriculation"),
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 1234AB/01', 'class': 'form-control'})
    )
    transitaire = forms.CharField(
        label=_("Transitaire"),
        widget=forms.TextInput(attrs={'placeholder': 'Nom du transitaire', 'class': 'form-control'})
    )
    declaration = forms.CharField(
        label=_("N°. Déclaration / T1"), 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Numéro de déclaration', 'class': 'form-control'})
    )
    volume = forms.FloatField(
        label=_("Volume Ambiant (m³)"),
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-control'})
    )
    volume15 = forms.FloatField(
        label=_("Volume à 15°C (m³)"),
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-control'})
    )
    volume20 = forms.FloatField(
        label=_("Volume à 20°C (m³)"),
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-control'})
    )
    tonnagevide = forms.FloatField(
        label=_("Tonnage Vide (t)"),
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-control'})
    )
    tonnageair = forms.FloatField(
        label=_("Tonnage Air (t)"),
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super(Ajoutcargaison, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            HTML('<div class="form-section-title mb-3"><i class="fas fa-shipping-fast text-primary mr-2"></i>' + "TRANSPORT & PROVENANCE" + '</div>'),
            Row(
                Column(Field('voie', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                Column(Field('frontiere', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                Column(Field('typeunitetransport', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column(Field('provenance', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                Column(Field('immatriculation', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                Column(Field('transitaire', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                css_class='form-row'
            ),
            
            HTML('<div class="form-section-title mb-3 mt-3"><i class="fas fa-file-invoice-dollar text-primary mr-2"></i>' + "DÉTAILS COMMERCIAUX" + '</div>'),
            Row(
                Column(Field('importateur', css_class='form-control'), css_class='form-group col-md-6 col-12 mb-3'),
                Column(Field('entrepot', css_class='form-control'), css_class='form-group col-md-6 col-12 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column(Field('produit', css_class='form-control'), css_class='form-group col-md-6 col-12 mb-3'),
                Column(Field('declaration', css_class='form-control'), css_class='form-group col-md-6 col-12 mb-3'),
                css_class='form-row'
            ),
            
            HTML('<div class="form-section-title mb-3 mt-3"><i class="fas fa-weight text-primary mr-2"></i>' + "MESURES & QUANTITÉS" + '</div>'),
            Row(
                Column(Field('volume', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                Column(Field('volume15', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                Column(Field('volume20', css_class='form-control'), css_class='form-group col-md-4 col-12 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column(Field('tonnagevide', css_class='form-control'), css_class='form-group col-md-6 col-12 mb-3'),
                Column(Field('tonnageair', css_class='form-control'), css_class='form-group col-md-6 col-12 mb-3'),
                css_class='form-row'
            ),
        )


