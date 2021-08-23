from crispy_forms.bootstrap import Field
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Fieldset
from django import forms
from django_countries.fields import CountryField

from .models import Voie, Importateur, Produit, Ville, Entrepot, Nationalites


class Ajoutcargaison(forms.Form):
    voie = forms.ModelChoiceField(queryset=Voie.objects.all(), label="Type de voie d'entrée :")
    fournisseur = forms.CharField(label='Nom du Fournisseur :', required=False)
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all().order_by('nomimportateur'),
                                         label="Nom de l'importateur :")
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label="Nature du produit :")
    frontiere = forms.ModelChoiceField(queryset=Ville.objects.all(), label="Frontière d'entrée :")
    provenance = CountryField().formfield()
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all().order_by('nomentrepot'),
                                      label="Entrepot de destination :")
    transporteur = forms.CharField(label="Nom du transporteur :")
    declarant = forms.CharField(widget=forms.TextInput(), label="Transitaire/Agence en Douane :")
    poids = forms.DecimalField(min_value=1, label="Poids declaré en Kg :")
    volume = forms.DecimalField(min_value=1, max_value=100, label="Volume déclaré :")
    densitecargaison = forms.DecimalField(label="Densité du produit :", min_value=1, required=False)
    tempcargaison = forms.DecimalField(min_value=0, label="Température du produit :", required=False)
    t1d = forms.CharField(label="Numéro T1D :", required=False)
    t1e = forms.CharField(label="Numéro T1E :", required=False)
    numdeclaration = forms.CharField(label="Numéro de déclaration :", required=False)
    numbtfh = forms.CharField(label="Numéro BT/Fiche Chauffeur :", required=False)
    valeurfacture = forms.DecimalField(min_value=0, label="Valeur facture :", required=False)
    manifestdgda = forms.CharField(label='Manifeste DGDA :', required=False)
    idchauffeur = forms.CharField(label="Numéro ID/Passeport du conducteur :", required=False)
    nationalite = forms.ModelChoiceField(queryset=Nationalites.objects.all(), label="Nationalité du conducteur :")
    nomchauffeur = forms.CharField(label="Nom du conducteur :")
    immatriculation = forms.CharField(label="Immatriculation du camion/remorque/train/navire :")

    def __init__(self, *args, **kwargs):
        # user = kwargs.pop('user')
        super(Ajoutcargaison, self).__init__(*args, **kwargs)
        # qs = Ville.objects.filter(affectationville__username_id=user)
        # self.fields['frontiere'].queryset = qs
        self.helper = FormHelper()
        self.helper.form_id = 'carg_form'
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-8'
        self.helper.layout = Layout(
            Fieldset("Identification de l'importation",
                     Field('voie', css_class='col-md-6', id='voie'),
                     Field('frontiere', css_class='col-md-6'),
                     Field('fournisseur', placeholder='Nom du Fournisseur si applicable'),
                     'importateur',
                     'provenance',
                     'entrepot',
                     Field('transporteur', placeholder='Nom du Transporteur'),
                     Field('declarant', placeholder='Nom du Déclarant'),
                     Field('t1e', placeholder='Saisie du Numéro T1E DGDA - Ex.18772'),
                     Field('t1d', placeholder='Saisie du Numéro T1D DGDA - Ex.29889'),
                     Field('numdeclaration', placeholder='Saisie du Numéro de déclaration si applicable '),
                     ),
            Field('manifestdgda', placeholder='Saisie du numéro manisfeste si applicable'),

            Fieldset('Identification du produit',
                     'produit',
                     Field('valeurfacture', placeholder='Valeur facture en USD si applicable '),
                     Field('poids', placeholder='Le poids est exprimé en Kg'),
                     Field('volume', placeholder='Volume en metre Cube Ex: 30.33', min='20', max='400'),
                     Field('densitecargaison'),
                     # Field('tempcargaison',
                     #       placeholder='Cette valeur est prise à 20°C en accord avec les normes internationales',
                     #       disabled=True),
                     ),
            Fieldset('Identification du Moyen de transport',
                     Field('numbtfh', placeholder="Numéro BT ou Numéro Fiche Chauffeur si applicable"),
                     'idchauffeur',
                     'nationalite',
                     'nomchauffeur',
                     Field('immatriculation',
                           placeholder="Ex. 7889AH05/2877AC08"),
                     ),


        )
