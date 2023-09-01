from django import forms
from enreg.models import LaboReception, Produit
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column, Fieldset
from crispy_forms.bootstrap import Field, InlineField, FormActions, StrictButton
from bootstrap_datepicker_plus.widgets import DatePickerInput


class NatureProduitLaboratoire(forms.Form):
    natureProduit = forms.ModelChoiceField(queryset=Produit.objects.all(), label='NATURE DU PRODUIT :')

    def __init__(self, *args, **kwargs):
        super(NatureProduitLaboratoire, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Field('natureProduit'),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )


class ReceptionEchantillon(forms.Form):
    codelabo = forms.IntegerField(label="Code du Labo :")
    # numerore= forms.CharField(label="Numero RE :")
    datereception = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de réception :")
    dateprelevement = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de prélèvement :")


class ModificationEchantillon(forms.Form):
    codelabo = forms.CharField(label="Code du Labo :")
    # numerore= forms.CharField(label="Numero RE :")
    datereception = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de réception :")
    dateprelevement = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de prélèvement :")


class RapportLabo(forms.Form):
    # codelabo = forms.CharField(label="Code du Labo :")
    # numerore= forms.CharField(label="Numero RE :")
    datedebut = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de début :")
    datefin = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de fin :")


class Mogas(forms.Form):
    aspect = forms.CharField(max_length=32, label="Aspect", required=False)
    odeur = forms.CharField(max_length=32, label="Odeur", required=False)
    couleursaybolt = forms.CharField(max_length=32, label="Couleur", required=False)
    soufre = forms.DecimalField(label="Souffre Total en %", required=False)
    distillation = forms.DecimalField(label="Distillation", required=False)
    pointfinal = forms.DecimalField(label="Point Final", required=False)
    residu = forms.DecimalField(required=False, label="Résidu en %")
    corrosion = forms.CharField(max_length=32, required=False, label="Corrosion Cu")
    pourcent10 = forms.DecimalField(label="Distillation 10%", required=False)
    pourcent20 = forms.DecimalField(label="Distillation 20%", required=False)
    pourcent50 = forms.DecimalField(label="Distillation 50%", required=False)
    pourcent70 = forms.DecimalField(label="Distillation 70%", required=False)
    pourcent90 = forms.DecimalField(label="Distillation 90", required=False)
    tensionvapeur = forms.DecimalField(label="Tension en vapeur Reid", required=False)
    difftemperature = forms.DecimalField(label="Diff. Température évaporé", required=False)
    plomb = forms.DecimalField(required=False, label="Plomb g/l")
    indiceoctane = forms.DecimalField(required=False, label="Indice OCTANE (RON)")
    massevolumique15 = forms.DecimalField(label="Masse Volumique à 15°C", required=False)

    def __init__(self, *args, **kwargs):
        super(Mogas, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row(
                Column('aspect',css_class='form-group col-md-4 mb-0'),
                Column('odeur',css_class='form-group col-md-4 mb-0'),
                Column('couleursaybolt',css_class='form-group col-md-4 mb-0'),
                Column('soufre',css_class='form-group col-md-4 mb-0'),
                Column('residu',css_class='form-group col-md-4 mb-0'),
                Column('corrosion',css_class='form-group col-md-4 mb-0'),
                Column('pourcent10',css_class='form-group col-md-4 mb-0'),
                Column('pourcent20',css_class='form-group col-md-4 mb-0'),
                Column('distillation',css_class='form-group col-md-4 mb-0'),
                Column('pointfinal',css_class='form-group col-md-4 mb-0'),
                Column('pourcent50',css_class='form-group col-md-4 mb-0'),
                Column('pourcent70',css_class='form-group col-md-4 mb-0'),
                Column('pourcent90',css_class='form-group col-md-4 mb-0'),
                Column('massevolumique15',css_class='form-group col-md-4 mb-0'),
                Column('difftemperature',css_class='form-group col-md-4 mb-0'),
                Column('tensionvapeur',css_class='form-group col-md-4 mb-0'),
                Column('plomb',css_class='form-group col-md-4 mb-0'),
                Column('indiceoctane',css_class='form-group col-md-4 mb-0'),
            ),

            # Field('aspect', 'odeur', 'couleursaybolt', 'soufre', 'residu', 'corrosion', 'pourcent10', 'pourcent20',
            #       'distillation', 'pointfinal',
            #       'pourcent50', 'pourcent70', 'pourcent90', 'massevolumique15', 'difftemperature', 'tensionvapeur',
            #       'plomb', 'indiceoctane'),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )


class Gasoil(forms.Form):
    couleurastm = forms.CharField(max_length=32, required=False, label='Couleur ASTM')
    aciditetotal = forms.FloatField(required=False, label='Acidité Total mg KOH/g')
    soufre = forms.FloatField(required=False, label='Soufre Total en %')
    massevolumique = forms.FloatField(required=False, label='Masse Volumique à 20°C (Kg/l)')
    massevolumique15 = forms.FloatField(required=False, label='Masse Volumique 15°C (Kg/l)')
    distillation = forms.FloatField(required=False)
    pointinitial = forms.FloatField(required=False, label='Point Initial °C')
    distillation10 = forms.FloatField(required=False, label='Récup à 10% vol (°C)')
    distillation20 = forms.FloatField(required=False, label='Récup à 20% vol (°C)')
    distillation50 = forms.FloatField(required=False, label='Récup à 50% vol (°C)')
    distillation90 = forms.FloatField(required=False, label='Récup à 90% vol (°C)')
    recuperation362 = forms.FloatField(required=False, label='Récup vol à 362 °C')
    pointfinal = forms.FloatField(required=False, label='Point Final °C')
    pointeclair = forms.FloatField(required=False, label="Point d'éclair °C")
    viscosite = forms.FloatField(required=False, label='Viscosité cinématique à 40°C')
    pointecoulement = forms.FloatField(required=False, label="Point d'écoulement")
    teneureau = forms.FloatField(required=False, label='Teneur en eau % vol')
    sediment = forms.FloatField(required=False, label='Sédiments par extraction')
    corrosion = forms.CharField(max_length=32, required=False, label='Corrosion de Cuivre')
    indicecetane = forms.FloatField(required=False, label='Indice Cétane')
    densite = forms.FloatField(required=False)
    cendre = forms.FloatField(required=False, label='Cendres %')

    def __init__(self, *args, **kwargs):
        super(Gasoil, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row(
                Column('couleurastm',css_class='form-group col-md-4 mb-0'),
                Column('aciditetotal',css_class='form-group col-md-4 mb-0'),
                Column('soufre',css_class='form-group col-md-4 mb-0'),
                Column('massevolumique',css_class='form-group col-md-4 mb-0'),
                Column('massevolumique15',css_class='form-group col-md-4 mb-0'),
                Column('distillation10',css_class='form-group col-md-4 mb-0'),
                Column('distillation20',css_class='form-group col-md-4 mb-0'),
                Column('distillation50',css_class='form-group col-md-4 mb-0'),
                Column('distillation90',css_class='form-group col-md-4 mb-0'),
                Column('pointinitial',css_class='form-group col-md-4 mb-0'),
                Column('pointfinal',css_class='form-group col-md-4 mb-0'),
                Column('pointeclair',css_class='form-group col-md-4 mb-0'),
                Column('pointeclair',css_class='form-group col-md-4 mb-0'),
                Column('viscosite',css_class='form-group col-md-4 mb-0'),
                Column('pointecoulement',css_class='form-group col-md-4 mb-0'),
                Column('teneureau',css_class='form-group col-md-4 mb-0'),
                Column('sediment',css_class='form-group col-md-4 mb-0'),
                Column('corrosion',css_class='form-group col-md-4 mb-0'),
                Column('indicecetane',css_class='form-group col-md-4 mb-0'),
                Column('recuperation362',css_class='form-group col-md-4 mb-0'),
                Column('cendre',css_class='form-group col-md-4 mb-0'),
            ),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )


class JetA1(forms.Form):
    aspect = forms.CharField(max_length=32, label='Aspect', required=False)
    couleursaybolt = forms.CharField(max_length=32, label='Couleur SAYBOLT', required=False)
    aciditetotal = forms.CharField(max_length=32, label='Acidité Total mg KOH/g', required=False)
    soufre = forms.DecimalField(label='Soufre Total en % poids', required=False)
    soufremercaptan = forms.DecimalField(label='Soufre Mercaptan % m/m', required=False)
    docteurtest = forms.DecimalField(label='Ou Docteur Test', required=False)
    distillation = forms.DecimalField(required=False)
    massevolumique15 = forms.DecimalField(required=False, label='Masse Volumique à 15°C')
    pointinitial = forms.DecimalField(required=False, label='Point Initial °C')
    vol10 = forms.DecimalField(required=False, label='10% Vol °C')
    vol90 = forms.DecimalField(required=False, label='90% Vol °C')
    pointfinal = forms.DecimalField(required=False, label='Point Final °C')
    residu = forms.DecimalField(required=False, label='Résidu en % vol')
    perte = forms.DecimalField(required=False, label='Pertes en % vol')
    viscosite = forms.DecimalField(required=False, label='Viscosité cinématique')
    pointeclair = forms.DecimalField(required=False, label="Point d'éclair")
    freezingpoint = forms.DecimalField(required=False, label='Freezing Point')
    pointfumee = forms.DecimalField(required=False, label='Point Fumée')
    pointinflammabilite = forms.DecimalField(required=False, label="Point d'inflammabilité")
    teneureau = forms.DecimalField(required=False, label='Teneur en eau')
    corrosion = forms.CharField(required=False, label='Corrosion de cuivre')
    conductivite = forms.DecimalField(required=False, label='Conductivité éléctrique')

    vol20 = forms.DecimalField(required=False)
    vol30 = forms.DecimalField(required=False)
    vol40 = forms.DecimalField(required=False)
    vol50 = forms.DecimalField(required=False)
    vol60 = forms.DecimalField(required=False)
    vol70 = forms.DecimalField(required=False)
    vol80 = forms.DecimalField(required=False)

    def __init__(self, *args, **kwargs):
        super(JetA1, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row(
                Column('aspect',css_class='form-group col-md-4 mb-0'),
                Column('couleursaybolt',css_class='form-group col-md-4 mb-0'),
                Column('aciditetotal',css_class='form-group col-md-4 mb-0'),
                Column('soufre',css_class='form-group col-md-4 mb-0'),
                Column('soufremercaptan',css_class='form-group col-md-4 mb-0'),
                Column('docteurtest',css_class='form-group col-md-4 mb-0'),
                Column('distillation',css_class='form-group col-md-4 mb-0'),
                Column('pointinitial',css_class='form-group col-md-4 mb-0'),
                Column('pointfinal',css_class='form-group col-md-4 mb-0'),
                Column('pointfumee',css_class='form-group col-md-4 mb-0'),
                Column('pointeclair',css_class='form-group col-md-4 mb-0'),
                Column('freezingpoint',css_class='form-group col-md-4 mb-0'),
                Column('residu',css_class='form-group col-md-4 mb-0'),
                Column('perte',css_class='form-group col-md-4 mb-0'),
                Column('massevolumique15',css_class='form-group col-md-4 mb-0'),
                Column('viscosite',css_class='form-group col-md-4 mb-0'),
                Column('pointinflammabilite',css_class='form-group col-md-4 mb-0'),
                Column('teneureau',css_class='form-group col-md-4 mb-0'),
                Column('corrosion',css_class='form-group col-md-4 mb-0'),
                Column('vol10',css_class='form-group col-md-4 mb-0'),
                Column('vol90',css_class='form-group col-md-4 mb-0'),
            ),

            # Field('aspect', 'couleursaybolt', 'aciditetotal', 'soufre', 'soufremercaptan', 'docteurtest',
            #       'distillation',
            #       'pointinitial', 'pointfinal', 'pointfumee', 'pointeclair', 'freezingpoint', 'residu', 'perte',
            #       'massevolumique15', 'viscosite',
            #       'pointinflammabilite', 'teneureau', 'corrosion', 'conductivite', 'vol10', 'vol90'),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )


class PetroleLampant(forms.Form):
    aspect = forms.CharField(max_length=32, label='Aspect', required=False)
    couleursaybolt = forms.CharField(max_length=32, label='Couleur SAYBOLT', required=False)
    aciditetotal = forms.DecimalField(label='Acidité Total mg KOH/g', required=False)
    soufre = forms.DecimalField(label='Soufre Total en % poids', required=False)
    soufremercaptan = forms.DecimalField(label='Soufre Mercaptan % m/m', required=False)
    docteurtest = forms.DecimalField(label='Ou Docteur Test', required=False)
    distillation = forms.DecimalField(required=False)
    massevolumique15 = forms.DecimalField(required=False, label='Masse Volumique à 15°C')
    pointinitial = forms.DecimalField(required=False, label='Point Initial °C')
    vol10 = forms.DecimalField(required=False, label='10% Vol °C')
    vol90 = forms.DecimalField(required=False, label='90% Vol °C')
    pointfinal = forms.DecimalField(required=False, label='Point Final °C')
    residu = forms.DecimalField(required=False, label='Résidu en % vol')
    perte = forms.DecimalField(required=False, label='Pertes en % vol')
    viscosite = forms.DecimalField(required=False, label='Viscosité cinématique')
    pointeclair = forms.DecimalField(required=False, label="Point d'éclair")
    freezingpoint = forms.DecimalField(required=False, label='Freezing Point')
    pointfumee = forms.DecimalField(required=False, label='Point Fumée')
    pointinflammabilite = forms.DecimalField(required=False, label="Point d'inflammabilité")
    teneureau = forms.DecimalField(required=False, label='Teneur en eau')
    corrosion = forms.CharField(required=False, label='Corrosion de cuivre')
    conductivite = forms.DecimalField(required=False, label='Conductivité éléctrique')

    vol20 = forms.DecimalField(required=False)
    vol30 = forms.DecimalField(required=False)
    vol40 = forms.DecimalField(required=False)
    vol50 = forms.DecimalField(required=False)
    vol60 = forms.DecimalField(required=False)
    vol70 = forms.DecimalField(required=False)
    vol80 = forms.DecimalField(required=False)

    def __init__(self, *args, **kwargs):
        super(PetroleLampant, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row(
                Column('aspect',css_class='form-group col-md-4 mb-0'),
                Column('couleursaybolt',css_class='form-group col-md-4 mb-0'),
                Column('aciditetotal',css_class='form-group col-md-4 mb-0'),
                Column('soufre',css_class='form-group col-md-4 mb-0'),
                Column('soufremercaptan',css_class='form-group col-md-4 mb-0'),
                Column('docteurtest',css_class='form-group col-md-4 mb-0'),
                Column('distillation',css_class='form-group col-md-4 mb-0'),
                Column('pointinitial',css_class='form-group col-md-4 mb-0'),
                Column('pointfinal',css_class='form-group col-md-4 mb-0'),
                Column('pointfumee',css_class='form-group col-md-4 mb-0'),
                Column('pointeclair',css_class='form-group col-md-4 mb-0'),
                Column('freezingpoint',css_class='form-group col-md-4 mb-0'),
                Column('residu',css_class='form-group col-md-4 mb-0'),
                Column('perte',css_class='form-group col-md-4 mb-0'),
                Column('massevolumique15',css_class='form-group col-md-4 mb-0'),
                Column('viscosite',css_class='form-group col-md-4 mb-0'),
                Column('pointinflammabilite',css_class='form-group col-md-4 mb-0'),
                Column('teneureau',css_class='form-group col-md-4 mb-0'),
                Column('corrosion',css_class='form-group col-md-4 mb-0'),
                Column('conductivite',css_class='form-group col-md-4 mb-0'),
                Column('vol10',css_class='form-group col-md-4 mb-0'),
                Column('vol90',css_class='form-group col-md-4 mb-0'),
            ),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )


# Formulaire de recherche statistique
class FiltresDate(forms.Form):
    date_d = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='DATE DEBUT',required=False)
    date_f = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='DATE FIN',required=False)

    def __init__(self, *args, **kwargs):
        super(FiltresDate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-6'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row(
                Column('date_d',css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('date_f',css_class='form-group col-md-12 mb-0'),
            ),

            FormActions(
                Reset('ANNULER', 'ANNULER', css_class='btn btn-danger'),
                Submit('VALIDER', 'VALIDER', css_class='btn btn-primary'),
            ),
        )



# Formulaire de recherche statistique
class CorrectionProduit(forms.Form):
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label='NATURE PRODUIT')
    def __init__(self, *args, **kwargs):
        super(CorrectionProduit, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'correctionForm'
        self.helper.label_class = 'col-md-6'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row(
                Column('produit',css_class='form-group col-md-12 mb-0'),
            ),
        )