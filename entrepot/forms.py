from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column, Fieldset, Button
from crispy_forms.bootstrap import Field, InlineField, FormActions, StrictButton
from bootstrap_datepicker_plus.widgets import DatePickerInput

etat_physique = [
    ('---', '---'),
    ('bon', 'BON(S)'),
    ('brise', 'BRISE(S)')
]

conformite_scelle = [
    ('---', '---'),
    ('conforme', 'CONFORME'),
    ('nonconforme', 'NON CONFORME')
]

types = [
    ('', ''),
    ('innage', 'INNAGE'),
    ('ullage', 'ULLAGE'),
]


class Echantilloner(forms.Form):
    dateechantillonage = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de prélèvement :")
    # numdossier = forms.CharField(label="Numéro de Dossier :", required=True)
    # codecargaison = forms.CharField(label="Code Camion :", required=False)
    # numrappech = forms.CharField(label="Numéro rapport d'échantillonage :")
    numplombh = forms.CharField(label="NUMERO DES PLOMBS (HAUT)", required=False)
    numplombb = forms.CharField(label="NUMERO DES PLOMBS (BAS)", required=False)
    numplombbr = forms.CharField(label="NUMERO DES PLOMBS BRISES", required=False)
    numplombaph = forms.CharField(label="NUMERO DES PLOMBS APPOSES", required=False)
    etatphysique = forms.CharField(widget=forms.Select(choices=etat_physique), label="ETAT DES PLOMBS", required=True)
    qte = forms.DecimalField(label="QUANTITE DE PRODUIT EN L.", required=True)
    conformite = forms.CharField(widget=forms.Select(choices=conformite_scelle),
                                 label="Conformité des scellés d'origine :", required=True)

    def __init__(self, *args, **kwargs):
        super(Echantilloner, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column('etatphysique', css_class='form-group col-md-2 mb-0'),
                Column('qte', css_class='form-group col-md-2 mb-0'),
                Column('numplombh', css_class='form-group col-md-12 mb-0'),
                Column('numplombb', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('numplombbr', css_class='form-group col-md-6 mb-0'),
                Column('numplombaph', css_class='form-group col-md-6 mb-0'),
            ),

            FormActions(
                Submit('VALIDER', 'VALIDER', css_class='btn btn-success'),
                Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
            ),
        )

class Decharger(forms.Form):
    densite = forms.FloatField(label="Densité:", required=True)
    types = forms.CharField(widget=forms.Select(choices=types), label="Types :", required=True)
    indexinit = forms.FloatField(label="Index Compteur Initial (si applicable):", required=False)
    indexfin = forms.FloatField(label="Index Compteur Fin (si applicable):", required=False)
    temperature = forms.FloatField(label="Température °C:", required=True, min_value=1)
    gov = forms.FloatField(label="GOV jaugé en Mètre cube:", required=False, min_value=1)

    def __init__(self, *args, **kwargs):
        super(Decharger, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row("",
                Column('types', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
                ),
            Row(
                Column('indexinit', css_class='form-group col-md-6 mb-0'),
                Column('indexfin', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Field('gov', placeholder=""),
            Row(
                Column('densite', css_class='form-group col-md-6 mb-0'),
                Column('temperature', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )
