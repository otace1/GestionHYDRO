from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django import forms

from enreg.models import *


# class AjoutCargaison(forms.ModelForm):
#     class Meta:
#         model = Cargaison
#         fields = ('voie', 'frontiere', 'typeunitetransport', 'immatriculation', 'provenance', 'produit', 'declaration',
#                   'entrepot','transitaire',
#                   'importateur', 'entrepot', 'produit', 'volume', 'volume15', 'volume20', 'tonnagevide', 'tonnageair')
#
#         def __init__(self, *args, **kwargs):
#             super(AjoutCargaison, self).__init__(*args, **kwargs)
#             self.helper = FormHelper()
#             self.helper.layout = Layout(
#                 Row(
#                     Column('voie', css_class='form-group col-md-4 mb-0'),
#                     Column('frontiere', css_class='form-group col-md-4 mb-0'),
#                     Column('typeunitetransport', css_class='form-group col-md-4 mb-0'),
#                     css_class='form-row'
#                 ),
#                 Row(
#                     Column('immatriculation', css_class='form-group col-md-3 mb-0'),
#                     Column('transitaire', css_class='form-group col-md-3 mb-0'),
#                     Column('provenance', label='PROVENANCE', css_class='form-group col-md-3 mb-0'),
#                     Column('importateur', css_class='form-group col-md-3 mb-0'),
#                     css_class='form-row'
#                 ),
#                 Row(
#                     Column('declaration', css_class='form-group col-md-4 mb-0'),
#                     Column('entrepot', css_class='form-group col-md-4 mb-0'),
#                     Column('produit', css_class='form-group col-md-4 mb-0'),
#                     css_class='form-row'
#                 ),
#                 Row(
#                     Column('volume', css_class='form-group col-md-4 mb-0'),
#                     Column('volume15', css_class='form-group col-md-4 mb-0'),
#                     Column('volume20', css_class='form-group col-md-4 mb-0'),
#                     css_class='form-row'
#
#                 ),
#                 Row(
#                     Column('tonnagevide', css_class='form-group col-md-6 mb-0'),
#                     Column('tonnageair', css_class='form-group col-md-6 mb-0'),
#                     css_class='form-row'
#
#                 ),
#             )


class Ajoutcargaison(forms.Form):
    voie = forms.ModelChoiceField(queryset=Voie.objects.all(), label="TYPE VOIE D'ENTREE")
    frontiere = forms.ModelChoiceField(queryset=Ville.objects.all().order_by('nomville'), label="FRONTIERE D'ENTREE")
    typeunitetransport = forms.ModelChoiceField(queryset=TypeUniteTransport.objects.all().order_by('unitetransport'),
                                                label="TYPE D'UNITE DE TRANPORT", required=False)
    provenance = CountryField().formfield()
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all().order_by('nomimportateur'),
                                         label="FOURNISSEUR", required=True)
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label="NATURE DU PRODUIT")
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all().order_by('nomentrepot'),
                                      label="ENTREPOT DE DESTINATION")
    immatriculation = forms.CharField(label="IMMATRICULATION")
    transitaire = forms.CharField(label='TRANSITAIRE')
    declaration = forms.CharField(label="N°.DECLARATION/T1", required=False)
    volume = forms.FloatField(label="VOLUME AMBIANT", required=True)
    # Nouveau ajout sur le formulaire d'enregistrement a l'entree
    volume15 = forms.FloatField(label="VOLUME A 15°C", required=False)
    volume20 = forms.FloatField(label="VOLUME A 20°C", required=False)
    tonnagevide = forms.FloatField(label="TONNAGE VIDE", required=False)
    tonnageair = forms.FloatField(label="TONNAGE AIR", required=False)
    files = forms.FileField(label='FILES', widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}), required=False)

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
                Column('immatriculation', css_class='form-group col-md-3 mb-0'),
                Column('transitaire', css_class='form-group col-md-3 mb-0'),
                Column('provenance', label='PROVENANCE', css_class='form-group col-md-3 mb-0'),
                Column('importateur', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('declaration', css_class='form-group col-md-4 mb-0'),
                Column('entrepot', css_class='form-group col-md-4 mb-0'),
                Column('produit', css_class='form-group col-md-4 mb-0'),
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
            Row(
                Column('files', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
        )


