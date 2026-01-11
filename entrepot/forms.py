from crispy_forms.bootstrap import Field, FormActions
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column
from django import forms

from enreg.models import *

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
    ('', '--- Choisir une méthode ---'),
    ('Running Sampling (Prélèvement continu)', 'Running Sampling (Prélèvement continu)'),
    ('All-level Sampling (Prélèvement à tous les niveaux)', 'All-level Sampling (Prélèvement à tous les niveaux)'),
    ('Upper-Middle-Lower Sampling (Prélèvement Supérieur-Moyen-Inférieur)', 'Upper-Middle-Lower Sampling (Prélèvement Supérieur-Moyen-Inférieur)'),
    ('Spot Sampling (Prélèvement ponctuel)', 'Spot Sampling (Prélèvement ponctuel)'),
    ('Bottom Sampling (Prélèvement en fond de réservoir)', 'Bottom Sampling (Prélèvement en fond de réservoir)'),
    ('Tap Sampling (Prélèvement au robinet)', 'Tap Sampling (Prélèvement au robinet)'),
    ('Core Sampling (Prélèvement à la sonde)', 'Core Sampling (Prélèvement à la sonde)'),
    ('Other (Autre)', 'Other (Autre)'),
]

unites_mesure_innagein = [
    ('', ''),
    ('cm', 'CM'),
    ('m', 'M'),
]

unites_mesure_volumein = [
    ('', ''),
    ('Cu.Mtrs', 'Cu.Mtrs'),
]

unites_mesure_tempin = [
    ('', ''),
    ('C°', 'C°'),
    # ('F°', 'F°'),
]

unites_mesure_weightin = [
    ('', ''),
    ('m/t', ' M/T'),
]


class NatureProduit(forms.Form):
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label='NATURE PRODUIT')

    def __init__(self, *args, **kwargs):
        super(NatureProduit, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column('produit', css_class='form-group col-md-4 mb-0'),
            ),
            FormActions(
                Submit('VALIDER', 'VALIDER', css_class='btn btn-success'),
                Reset('CLEAR', 'CLEAR', css_class='btn btn-danger'),
            ),
        )


conformite_sampling = [
    ('', '--- Choisir un aspect ---'),
    ('CONFORME (Bon aspect)', 'CONFORME (Bon aspect)'),
    ('NON CONFORME (Présence d\'impuretés/eau)', 'NON CONFORME (Présence d\'impuretés/eau)'),
]


class Echantilloner(forms.Form):
    matricule = forms.CharField(
        label="MATRICULE DE L'ÉCHANTILLONNEUR",
        widget=forms.TextInput(attrs={'placeholder': 'Entrez le matricule'})
    )
    methodeutilisee = forms.ChoiceField(
        choices=methodes,
        label="MÉTHODE UTILISÉE",
        required=True
    )
    qte = forms.FloatField(
        label="QUANTITÉ PRÉLEVÉE (L)",
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': 'Ex: 1.5', 'step': '0.1'})
    )
    conformite = forms.ChoiceField(
        choices=conformite_sampling,
        label="ASPECT ORGANOLEPTIQUE",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(Echantilloner, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('matricule', css_class='form-group col-md-12 mb-3'),
            ),
            Row(
                Column('methodeutilisee', css_class='form-group col-md-8 mb-3'),
                Column('qte', css_class='form-group col-md-4 mb-3'),
            ),
            Row(
                Column('conformite', css_class='form-group col-md-12 mb-3'),
            ),
        )

class Decharger(forms.Form):
    densite = forms.FloatField(label="Densité", required=True)
    types = forms.CharField(widget=forms.Select(choices=types), label="Type de mesure", required=True)
    indexinit = forms.FloatField(label="Index Initial", required=False)
    indexfin = forms.FloatField(label="Index Final", required=False)
    temperature = forms.FloatField(label="Température (°C)", required=True, min_value=1)
    gov = forms.FloatField(label="GOV (m³)", required=False, min_value=0)

    def __init__(self, *args, **kwargs):
        super(Decharger, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('types', css_class='form-group col-md-12 mb-3'),
            ),
            Row(
                Column('indexinit', css_class='form-group col-md-6 mb-3'),
                Column('indexfin', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('densite', css_class='form-group col-md-4 mb-3'),
                Column('temperature', css_class='form-group col-md-4 mb-3'),
                Column('gov', css_class='form-group col-md-4 mb-3'),
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
                Column('meter', css_class='form-group col-md-6 mb-0'),
                Column('tanker', css_class='form-group col-md-6 mb-0'),
                Column('shore', css_class='form-group col-md-6 mb-0'),
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

#Avec presence compteur
class TankerInspection(forms.Form):
    # produit = forms.ModelChoiceField(Produit.objects.all(), label="PRODUIT")
    # meterbefore = forms.FloatField(required=False, label="INDEX INITIAL DU COMPTEUR")
    dens = forms.FloatField(required=True, label="DENSITE (Ex. 820.907)")
    temp = forms.FloatField(required=True, label="TEMPERATURE")
    innagein = forms.CharField(widget=forms.Select(choices=unites_mesure_innagein), label="INNAGE IN", required=False)
    volumein = forms.CharField(widget=forms.Select(choices=unites_mesure_volumein), label="VOLUME IN", required=True)
    tempin = forms.CharField(widget=forms.Select(choices=unites_mesure_tempin), label="TEMP IN", required=True)
    weightin = forms.CharField(widget=forms.Select(choices=unites_mesure_weightin), label="WEIGHT IN", required=True)

    def __init__(self, *args, **kwargs):
        super(TankerInspection, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Row(
            #     # Column('produit', css_class='form-group col-md-6 mb-0'),
            #     Column('meterbefore', css_class='form-group col-md-6 mb-0'),
            #     css_class='form-row'
            # ),
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
            'sealNumber',
            'sealstate',
            'innage',
            'gov',
            'tempcomp',
        )

    def __init__(self, *args, **kwargs):
        super(CompartimentInspection, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row("",
                Column('compart', css_class='form-group col-md-6 mb-0'),
                Column('sealNumber', css_class='form-group col-md-6 mb-0'),
                ),
            Row("",
                Column('sealstate', css_class='form-group col-md-3 mb-0'),
                Column('innage', css_class='form-group col-md-3 mb-0'),
                Column('gov', css_class='form-group col-md-3 mb-0'),
                Column('tempcomp', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
                ),
        )


class MeterAfter(forms.Form):
    meterbefore = forms.FloatField(required=False, label="INDEX INITIAL DU COMPTEUR")
    meterafter = forms.FloatField(required=False, label="INDEX FINAL DU COMPTEUR")

    def __init__(self, *args, **kwargs):
        super(MeterAfter, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'meter-after'
        self.helper.layout = Layout(
            Row(
                Column('meterbefore', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
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


#Kalemie case integration
class Special_inspection_form(forms.Form):
    dens = forms.FloatField(required=True, label="DENSITE (Ex. 820.907)")
    index_deb = forms.IntegerField(required=False, label="INDEX DEB (Ex. 820)")
    index_fin = forms.IntegerField(required=False, label="INDEX FIN (Ex. 820)")
    temp = forms.FloatField(required=True, label="TEMPERATURE")
    gov = forms.FloatField(required=True, label="GOV")

    def __init__(self, *args, **kwargs):
        super(Special_inspection_form, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'special-inspection-form'
        self.helper.layout = Layout(

     Row(
         Column('dens', css_class='form-group col-md-6 mb-0'),
                Column('temp', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
         Column('index_deb', css_class='form-group col-md-6 mb-0'),
                Column('index_fin', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
         Column('gov', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('suivant', 'Enregistrer', css_class='btn btn-outline-primary'),
                Reset('annuler', 'Annuler', css_class='btn btn-outline-danger'),
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

