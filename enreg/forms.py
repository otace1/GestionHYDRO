from crispy_forms.layout import Layout, Row, Column
from crispy_forms.helper import FormHelper
from django import forms
from django_countries.fields import CountryField
from enreg.models import *


class AjoutCargaison(forms.ModelForm):
    class Meta:
        model = Cargaison
        fields = ('voie', 'frontiere', 'typeunitetransport', 'immatriculation', 'provenance', 'produit', 'entrepot',
                  'importateur', 'entrepot', 'produit', 'volume', 'volume15', 'volume20', 'tonnagevide', 'tonnageair')

        def __init__(self, *args, **kwargs):
            super(AjoutCargaison, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.layout = Layout(
                Row(
                    Column('voie', css_class='form-group col-md-4 mb-0'),
                    Column('frontiere', css_class='form-group col-md-4 mb-0'),
                    Column('typeunitetransport', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('immatriculation', css_class='form-group col-md-4 mb-0'),
                    Column('provenance', label='PROVENANCE', css_class='form-group col-md-4 mb-0'),
                    Column('importateur', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('entrepot', css_class='form-group col-md-6 mb-0'),
                    Column('produit', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('volume', css_class='form-group col-md-4 mb-0'),
                    Column('volume15', css_class='form-group col-md-4 mb-0'),
                    Column('volume20', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'

                ),
                Row(
                    Column('tonnagevide', css_class='form-group col-md-6 mb-0'),
                    Column('tonnageair', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'

                ),
            )


class Ajoutcargaison(forms.Form):
    voie = forms.ModelChoiceField(queryset=Voie.objects.all(), label="TYPE VOIE D'ENTREE")
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all().order_by('nomimportateur'),
                                         label="FOURNISSEUR", required=True)
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label="NATURE DU PRODUIT")
    frontiere = forms.ModelChoiceField(queryset=Ville.objects.all().order_by('nomville'), label="FRONTIERE D'ENTREE")
    provenance = CountryField().formfield()
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all().order_by('nomentrepot'),
                                      label="ENTREPOT DE DESTINATION")
    declarant = forms.CharField(widget=forms.TextInput(), label="TRANSITAIRE")
    poids = forms.DecimalField(min_value=1, label="MASSE EN TONNE METRIQUE (MTA)")
    volume = forms.FloatField(label="VOLUME AMBIANT", required=True)
    t1d = forms.CharField(label="T1D", required=False)
    t1e = forms.CharField(label="T1E", required=False)
    numdeclaration = forms.CharField(label="# DECLARATION", required=False)
    numbtfh = forms.CharField(label="NUMERO BT/LT/FICHE CHAUFFEUR", required=False)
    manifestdgda = forms.CharField(label='# MANIFESTE', required=False)
    immatriculation = forms.CharField(label="IMMATRICULATION")

    # Nouveau ajout sur le formulaire d'enregistrement a l'entree
    typeunitetransport = forms.ModelChoiceField(queryset=TypeUniteTransport.objects.all().order_by('unitetransport'),
                                                label="TYPE D'UNITE DE TRANPORT", required=False)
    volume15 = forms.FloatField(label="VOLUME A 15°C", required=False)
    volume20 = forms.FloatField(label="VOLUME A 20°C", required=False)
    tonnagevide = forms.FloatField(label="TONNAGE VIDE", required=False)
    tonnageair = forms.FloatField(label="TONNAGE AIR", required=False)

    def __init__(self, *args, **kwargs):
        super(Ajoutcargaison, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('voie', css_class='form-group col-md-4 mb-0'),
                Column('frontiere', css_class='form-group col-md-4 mb-0'),
                Column('typeunitetransport', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('immatriculation', css_class='form-group col-md-4 mb-0'),
                Column('provenance', label='PROVENANCE', css_class='form-group col-md-4 mb-0'),
                Column('importateur', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('entrepot', css_class='form-group col-md-6 mb-0'),
                Column('produit', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('volume', css_class='form-group col-md-4 mb-0'),
                Column('volume15', css_class='form-group col-md-4 mb-0'),
                Column('volume20', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'

            ),
            Row(
                Column('tonnagevide', css_class='form-group col-md-6 mb-0'),
                Column('tonnageair', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'

            ),
        )
