from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column, Fieldset, Button, Div
from crispy_forms.bootstrap import Field, InlineField, FormActions, StrictButton, TabHolder, Tab, ContainerHolder, \
    Container, InlineCheckboxes
from enreg.models import *
from django.forms.models import inlineformset_factory

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

methodes = [
    ('', ''),
    ('running sampling', 'RUNNING SAMPLING'),
    ('allo level sampling', 'ALLO LEVEL SAMPLING'),
    ('other', 'OTHER'),
]


class Echantilloner(forms.Form):
    matricule = forms.CharField(label="MATRICULE ECHANTILLONEUR")
    methodeutilisee = forms.CharField(widget=forms.Select(choices=methodes), label="METHODE UTILISEE", required=True)
    qte = forms.FloatField(label="QUANTITE PRELEVEE", required=True)

    def __init__(self, *args, **kwargs):
        super(Echantilloner, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column('matricule', css_class='form-group col-md-4 mb-0'),
                Column('methodeutilisee', css_class='form-group col-md-4 mb-0'),
                Column('qte', css_class='form-group col-md-4 mb-0'),
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


class PreInspectionForm1(forms.Form):
    meter = forms.BooleanField(required=False, label='METER')
    tanker = forms.BooleanField(required=False, label='TANKER')
    shore = forms.BooleanField(required=False, label='SHORE')

    def __init__(self, *args, **kwargs):
        super(PreInspectionForm1, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row("",
                Column('meter', css_class='form-group col-md-4 mb-0'),
                Column('tanker', css_class='form-group col-md-4 mb-0'),
                Column('shore', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
                ),
            FormActions(
                Submit('suivant', 'Suivant', css_class='btn btn-primary'),
                Reset('annuler', 'Annuler', css_class='btn btn-danger'),
            ),
        )


class SealInspection(forms.ModelForm):
    class Meta:
        model = InspectionSeal
        fields = (
            'manifoldnumber',
            'sealstate',
        )


class TankerInspection(forms.Form):
    produit = forms.ModelChoiceField(Produit.objects.all(), label="PRODUIT")
    meterbefore = forms.FloatField(required=False, label="INDEX INITIAL COMPTEUR")
    dens = forms.FloatField(required=False, label="DENSITE")
    temp = forms.FloatField(required=False, label="AT")
    innagein = forms.FloatField(required=False, label="INNAGE IN")
    volumein = forms.FloatField(required=False, label="VOLUME IN")
    tempin = forms.FloatField(required=False, label="TEMP IN")
    weightin = forms.FloatField(required=False, label="WEIGHT IN")

    def __init__(self, *args, **kwargs):
        super(TankerInspection, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('produit', css_class='form-group col-md-6 mb-0'),
                Column('meterbefore', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('dens', css_class='form-group col-md-6 mb-0'),
                Column('temp', label='PROVENANCE', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('innagein', css_class='form-group col-md-3 mb-0'),
                Column('volumein', css_class='form-group col-md-3 mb-0'),
                Column('tempin', css_class='form-group col-md-3 mb-0'),
                Column('weightin', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('suivant', 'Suivant', css_class='btn btn-primary'),
                Reset('annuler', 'Annuler', css_class='btn btn-danger'),
            ),
        )


class CompartimentInspection(forms.ModelForm):
    class Meta:
        model = Compartiment
        fields = (
            'compart',
            'sealstate',
            'innage',
            'gov',
            'tempcomp',
        )


class MeterAfter(forms.Form):
    meterafter = forms.FloatField(label="INDEX COMPTEUR")

    def __init__(self, *args, **kwargs):
        super(MeterAfter, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('meterafter', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('suivant', 'Suivant', css_class='btn btn-primary'),
                Reset('annuler', 'Annuler', css_class='btn btn-danger'),
            ),
        )


class ShoreInspection(forms.Form):
    produit = forms.ModelChoiceField(Produit.objects.all(), label="PRODUIT")
    innagein = forms.FloatField(required=False, label="INNAGE IN")
    volumein = forms.FloatField(required=False, label="VOLUME IN")
    tempin = forms.FloatField(required=False, label="TEMP IN")
    weightin = forms.FloatField(required=False, label="WEIGHT IN")

    def __init__(self, *args, **kwargs):
        super(ShoreInspection, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('produit', css_class='form-group col-md-6 mb-0'),
                Column('innagein', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('volumein', css_class='form-group col-md-4 mb-0'),
                Column('tempin', css_class='form-group col-md-4 mb-0'),
                Column('weightin', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('suivant', 'Suivant', css_class='btn btn-primary'),
                Reset('annuler', 'Annuler', css_class='btn btn-danger'),
            ),
        )


class ShoreInspectionBefore(forms.ModelForm):
    class Meta:
        model = ShoreTank
        fields = (
            'tankdenombefore',
            'prodinnagebefore',
            'fwdeepbefore',
            'govbefore',
            'tempbefore',
            'densitybefore',
        )

    def __init__(self, *args, **kwargs):
        super(ShoreInspectionBefore, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row("",
                Column('tankdenombefore', css_class='form-group col-md-6 mb-0'),
                Column('prodinnagebefore', css_class='form-group col-md-6 mb-0'),
                ),
            Row("",
                Column('fwdeepbefore', css_class='form-group col-md-3 mb-0'),
                Column('govbefore', css_class='form-group col-md-3 mb-0'),
                Column('tempbefore', css_class='form-group col-md-3 mb-0'),
                Column('densitybefore', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
                ),
            FormActions(
                Submit('suivant', 'Suivant', css_class='btn btn-primary'),
                Reset('annuler', 'Annuler', css_class='btn btn-danger'),
            ),
        )


class ShoreInspectionAfter(forms.ModelForm):
    class Meta:
        model = ShoreTank
        fields = (
            'tankdenomafter',
            'prodinnageafter',
            'fwdeepafter',
            'govafter',
            'tempafter',
            'densityafter',
        )

    def __init__(self, *args, **kwargs):
        super(ShoreInspectionAfter, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row("",
                Column('tankdenomafter', css_class='form-group col-md-6 mb-0'),
                Column('prodinnageafter', css_class='form-group col-md-6 mb-0'),
                ),
            Row("",
                Column('fwdeepafter', css_class='form-group col-md-3 mb-0'),
                Column('govafter', css_class='form-group col-md-3 mb-0'),
                Column('tempafter', css_class='form-group col-md-3 mb-0'),
                Column('densityafter', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
                ),
            FormActions(
                Submit('suivant', 'Suivant', css_class='btn btn-primary'),
                Reset('annuler', 'Annuler', css_class='btn btn-danger'),
            ),
        )

# class ShoreInspectionBefore(forms.ModelForm):
#     class Meta:
#         model = Shore
#         fields = (
#             'tankdenombefore',
#             'prodinnagebefore',
#             'fwdeepbefore',
#             'govbefore',
#             'tempbefore',
#             'fwvolbefore',
#         )
#         exclude = (
#             'tankdenomafter',
#             'prodinnageafter',
#             'fwdeepafter',
#             'govafter',
#             'tempafter',
#             'fwvolafter',
#         )
#
#
# class ShoreInspectionAfter(forms.ModelForm):
#     class Meta:
#         model = Shore
#         fields = (
#             'tankdenomafter',
#             'prodinnageafter',
#             'fwdeepafter',
#             'govafter',
#             'tempafter',
#             'fwvolafter',
#         )
#         exclude = (
#             'tankdenombefore',
#             'prodinnagebefore',
#             'fwdeepbefore',
#             'govbefore',
#             'tempbefore',
#             'fwvolbefore',
#         )
