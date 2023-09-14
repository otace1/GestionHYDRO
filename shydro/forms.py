from django import forms
from django.contrib.auth.decorators import login_required

from enreg.models import *
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column, Fieldset
from crispy_forms.bootstrap import Field, InlineField, FormActions, StrictButton, Div
from django_countries.fields import CountryField
from enreg.models import Cargaison, Entrepot_echantillon
from bootstrap_datepicker_plus.widgets import DatePickerInput

class CodificationHydro(forms.Form):
    numdossier = forms.CharField(label="Numero du dossier :", required=True)
    codecargaison = forms.CharField(label="Code de la cargaison :", required=True)

    def __init__(self,*args,**kwargs):
        super(CodificationHydro,self).__init__(*args,**kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-8'
        self.helper.layout = Layout(
                    Fieldset('Information administrative de codification',
                        Field('numdossier'),
                        Field('codecargaison'),
                                ),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset ('annuler','annuler',css_class='btn btn-danger'),

            ),

 )

class SearchByDate(forms.Form):
    start_date = forms.DateField(widget=DatePickerInput, required=False, label='DATE DEBUT')
    end_date = forms.DateField(widget=DatePickerInput, required=False, label='DATE FIN')

    def __init__(self, *args, **kwargs):
        super(SearchByDate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_errors = True
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Div(
                Field('start_date', css_class='form-group col-sm-2'),
                Field('end_date', css_class='form-group col-sm-2'),
            ),
            FormActions(
                Submit('Search', 'Search', css_class='btn-success'),
            )
        )


class ChangementDestination(forms.Form):
    nouvelleDestination = forms.ModelChoiceField(queryset=Entrepot.objects.all().order_by('nomentrepot'), label='Selectionner la nouvelle destination')
    def __init__(self, *args, **kwargs):
        super(ChangementDestination, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_id = 'destination-form'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_errors = True
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'

        self.helper.layout = Layout(
            Field(),
            Row(
                Column('nouvelleDestination', css_class='form-group col-md-12 mb-0'),
            ),
            FormActions(
                Submit('VALIDER', 'VALIDER', css_class='btn btn-success'),
                Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
            ),
        )


class Transbordement(forms.Form):
    nouvelleImmatriculation = forms.CharField(label='Immatriculation')
    nouveauVolume = forms.FloatField(label='Volume')
    def __init__(self, *args, **kwargs):
        super(Transbordement, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_id = 'transbordement-form'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_errors = True
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'

        self.helper.layout = Layout(
            Row(
                Column('nouvelleImmatriculation', css_class='form-group col-md-8 mb-0'),
                Column('nouveauVolume', css_class='form-group col-md-4 mb-0'),
            ),
            FormActions(
                Submit('VALIDER', 'VALIDER', css_class='btn btn-outline-success'),
                Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
            ),
        )



class Filters(forms.Form):
    fournisseur = forms.ModelChoiceField(queryset=Importateur.objects.all().order_by('nomimportateur'), label='FOURNISSEUR',required=False)
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.none(), label='ENTREPOT',required=False)
    dateDebut = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='DATE DEBUT',required=False)
    dateFin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='DATE FIN',required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user',None)  # Get the logged-in user from kwargs
        super(Filters, self).__init__(*args, **kwargs)

        self.fields['entrepot'].queryset = Entrepot.objects.filter(ville__affectationville__username=user).order_by('nomentrepot')

        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_id = 'filtres-form'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_errors = True
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'

        self.helper.layout = Layout(
            Row(
                Column('fournisseur', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('entrepot', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('dateDebut', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('dateFin', css_class='form-group col-md-12 mb-0'),
            ),
            FormActions(
                Submit('VALIDER', 'VALIDER', css_class='btn btn-primary'),
                Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
            ),
        )



class ChangementNatureProduit(forms.Form):
    nouvelleNatureProduit = forms.ModelChoiceField(queryset=Produit.objects.all().order_by('nomproduit'), label='NOUVELLE NATURE')

    def __init__(self, *args, **kwargs):
        super(ChangementNatureProduit, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_id = 'nature-form'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_errors = True
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'

        self.helper.layout = Layout(
            Row(
                Column('nouvelleNatureProduit', css_class='form-group col-md-12 mb-0'),
            ),
            FormActions(
                Submit('VALIDER', 'VALIDER', css_class='btn btn-outline-primary'),
                Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
            ),
        )


class RegularisationNouvelleEntree(forms.ModelForm):
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

    class Meta:
        model = Cargaison
        fields = ['voie','frontiere','typeunitetransport','provenance','importateur',
                 'produit','entrepot','immatriculation','transitaire','declaration','volume',
                 'volume15','volume20','tonnagevide','tonnageair']

    def __init__(self, *args, **kwargs):
        super(RegularisationNouvelleEntree, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'nouvelle-cargaison'
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
            FormActions(
                Submit('VALIDER', 'VALIDER', css_class='btn btn-outline-warning'),
                Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
            ),
        )


# Formulaire pour Ajout d'importateur
class ImportateurRegularisationForm(forms.Form):
    nomimportateur = forms.CharField(label='NOM IMPORTATEUR')
    adresseimportateur = forms.CharField(label='ADRESSE', required=False)
    nifimportateur = forms.CharField(label='NIF', required=False)
    email = forms.EmailField(label='EMAIL',widget=forms.EmailInput, required=False)

    def __init__(self, *args, **kwargs):
        super(ImportateurRegularisationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-12'
        self.helper.field_class = 'col-12'
        self.helper.layout = Layout(
                    Row(
                        Column('nomimportateur', css_class='form-group col-12'),
                        css_class='form-row'
                        ),
                    Row(
                        Column('nifimportateur', css_class='form-group col-3'),
                        Column('adresseimportateur', css_class='form-group col-9'),
                        css_class='form-row'
                        ),
                    Row(
                        Column('email', css_class='form-group col-12'),
                        css_class='form-row'
                        ),
            FormActions(
                Submit('ENREGISTRER', 'ENREGISTRER', css_class='btn btn-primary'),
                Reset('ANNULER', 'ANNULER', css_class='btn btn-danger'),
            ),
        )


# Formulaire pour ajout des entrepots
class EntrepotRegularisationForm(forms.Form):
    nomentrepot = forms.CharField(label='NOM ENTREPOT')
    adresseentrepot = forms.CharField(label='ADRESSE ENTREPOT', required=False)
    ville = forms.ModelChoiceField(queryset=Ville.objects.all().order_by('-nomville'),label='VILLE')

    def __init__(self, *args, **kwargs):
        super(EntrepotRegularisationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column('nomentrepot', css_class='form-group col-12'),
                css_class='form-row'
                ),
            Row(
                Column('ville', css_class='form-group col-4'),
                Column('adresseentrepot', css_class='form-group col-8'),
                css_class='form-row'
                ),
            FormActions(
                Submit('ENREGISTRER', 'ENREGISTRER', css_class='btn btn-outlined-warning'),
                Reset('ANNULER', 'ANNULER', css_class='btn btn-danger'),
            ),
        )



class ChangementImportateur(forms.Form):
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all().order_by('nomimportateur'), label='FOURNISSEUR')

    def __init__(self, *args, **kwargs):
        super(ChangementImportateur, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_id = 'importateur-form'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_errors = True
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'

        self.helper.layout = Layout(
            Row(
                Column('importateur', css_class='form-group col-md-12 mb-0'),
            ),
            FormActions(
                Submit('submit', 'VALIDER', css_class='btn btn-outline-danger'),
                Reset('reset', 'CLEAR', css_class='btn btn-danger'),
            ),
        )
