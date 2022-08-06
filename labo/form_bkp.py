from django import forms
from enreg.models import LaboReception
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column, Fieldset
from crispy_forms.bootstrap import Field, InlineField, FormActions, StrictButton
from bootstrap_datepicker_plus import DatePickerInput


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
    soufre = forms.CharField(max_length=32, label="Souffre Total en %", required=False)
    distillation = forms.CharField(max_length=32, label="Distillation", required=False)
    pointfinal = forms.CharField(max_length=32, label="Point Final", required=False)
    residu = forms.CharField(max_length=32, required=False, label="Résidu en %")
    corrosion = forms.CharField(max_length=32, required=False, label="Corrosion Cu")
    pourcent10 = forms.CharField(max_length=32, label="Distillation 10%", required=False)
    pourcent20 = forms.CharField(max_length=32, label="Distillation 20%", required=False)
    pourcent50 = forms.CharField(max_length=32, label="Distillation 50%", required=False)
    pourcent70 = forms.CharField(max_length=32, label="Distillation 70%", required=False)
    pourcent90 = forms.CharField(max_length=32, label="Distillation 90", required=False)
    tensionvapeur = forms.CharField(max_length=32, label="Tension en vapeur Reid", required=False)
    difftemperature = forms.CharField(max_length=32, label="Diff. Température évaporé", required=False)
    plomb = forms.CharField(max_length=32, required=False, label="Plomb g/l")
    indiceoctane = forms.CharField(max_length=32, required=False, label="Indice OCTANE (RON)")
    massevolumique15 = forms.CharField(max_length=32, label="Masse Volumique à 15°C", required=False)

    def __init__(self, *args, **kwargs):
        super(Mogas, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(

            Field('aspect', 'odeur', 'couleursaybolt', 'soufre', 'residu', 'corrosion', 'pourcent10', 'pourcent20',
                  'distillation', 'pointfinal',
                  'pourcent50', 'pourcent70', 'pourcent90', 'massevolumique15', 'difftemperature', 'tensionvapeur',
                  'plomb', 'indiceoctane'),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )


class Gasoil(forms.Form):
    couleurastm = forms.CharField(max_length=32, required=False, label='Couleur ASTM')
    aciditetotal = forms.CharField(max_length=32, required=False, label='Acidité Total mg KOH/g')
    soufre = forms.CharField(max_length=32, required=False, label='Soufre Total en %')
    massevolumique = forms.CharField(max_length=32, required=False, label='Masse Volumique à 20°C (Kg/l)')
    massevolumique15 = forms.CharField(max_length=32, required=False, label='Masse Volumique 15°C (Kg/l)')
    distillation = forms.CharField(max_length=32, required=False)
    pointinitial = forms.CharField(max_length=32, required=False, label='Point Initial °C')
    distillation10 = forms.CharField(max_length=32, required=False, label='Récup à 10% vol (°C)')
    distillation20 = forms.CharField(max_length=32, required=False, label='Récup à 20% vol (°C)')
    distillation50 = forms.CharField(max_length=32, required=False, label='Récup à 50% vol (°C)')
    distillation90 = forms.CharField(max_length=32, required=False, label='Récup à 90% vol (°C)')
    recuperation362 = forms.CharField(max_length=32, required=False, label='Récup vol à 362 °C')
    pointfinal = forms.CharField(max_length=32, required=False, label='Point Final °C')
    pointeclair = forms.CharField(max_length=32, required=False, label="Point d'éclair °C")
    viscosite = forms.CharField(max_length=32, required=False, label='Viscosité cinématique à 40°C')
    pointecoulement = forms.CharField(max_length=32, required=False, label="Point d'écoulement")
    teneureau = forms.CharField(max_length=32, required=False, label='Teneur en eau % vol')
    sediment = forms.CharField(max_length=32, required=False, label='Sédiments par extraction')
    corrosion = forms.CharField(max_length=32, required=False, label='Corrosion de Cuivre')
    indicecetane = forms.CharField(max_length=32, required=False, label='Indice Cétane')
    densite = forms.CharField(max_length=32, required=False)
    cendre = forms.CharField(max_length=32, required=False, label='Cendres %')

    def __init__(self, *args, **kwargs):
        super(Gasoil, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(

            Field('couleurastm', 'aciditetotal', 'soufre', 'massevolumique', 'massevolumique15',
                  'distillation10', 'distillation20', 'distillation50', 'distillation90', 'pointinitial', 'pointfinal',
                  'pointeclair', 'viscosite', 'pointecoulement', 'teneureau', 'sediment', 'corrosion', 'indicecetane',
                  'recuperation362', 'cendre'),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )


class JetA1(forms.Form):
    aspect = forms.CharField(max_length=32, label='Aspect', required=False)
    couleursaybolt = forms.CharField(max_length=32, label='Couleur SAYBOLT', required=False)
    aciditetotal = forms.CharField(max_length=32, label='Acidité Total mg KOH/g', required=False)
    soufre = forms.CharField(max_length=32, label='Soufre Total en % poids', required=False)
    soufremercaptan = forms.CharField(max_length=32, label='Soufre Mercaptan % m/m', required=False)
    docteurtest = forms.CharField(max_length=32, label='Ou Docteur Test', required=False)
    distillation = forms.CharField(max_length=32, required=False)
    massevolumique15 = forms.CharField(max_length=32, required=False, label='Masse Volumique à 15°C')
    pointinitial = forms.CharField(max_length=32, required=False, label='Point Initial °C')
    vol10 = forms.CharField(max_length=32, required=False, label='10% Vol °C')
    vol90 = forms.CharField(max_length=32, required=False, label='90% Vol °C')
    pointfinal = forms.CharField(max_length=32, required=False, label='Point Final °C')
    residu = forms.CharField(max_length=32, required=False, label='Résidu en % vol')
    perte = forms.CharField(max_length=32, required=False, label='Pertes en % vol')
    viscosite = forms.CharField(max_length=32, required=False, label='Viscosité cinématique')
    pointeclair = forms.CharField(max_length=32, required=False, label="Point d'éclair")
    freezingpoint = forms.CharField(max_length=32, required=False, label='Freezing Point')
    pointfumee = forms.CharField(max_length=32, required=False, label='Point Fumée')
    pointinflammabilite = forms.CharField(max_length=32, required=False, label="Point d'inflammabilité")
    teneureau = forms.CharField(max_length=32, required=False, label='Teneur en eau')
    corrosion = forms.CharField(max_length=32, required=False, label='Corrosion de cuivre')
    conductivite = forms.CharField(max_length=32, required=False, label='Conductivité éléctrique')

    vol20 = forms.CharField(max_length=32, required=False)
    vol30 = forms.CharField(max_length=32, required=False)
    vol40 = forms.CharField(max_length=32, required=False)
    vol50 = forms.CharField(max_length=32, required=False)
    vol60 = forms.CharField(max_length=32, required=False)
    vol70 = forms.CharField(max_length=32, required=False)
    vol80 = forms.CharField(max_length=32, required=False)

    def __init__(self, *args, **kwargs):
        super(JetA1, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(

            Field('aspect', 'couleursaybolt', 'aciditetotal', 'soufre', 'soufremercaptan', 'docteurtest',
                  'distillation',
                  'pointinitial', 'pointfinal', 'pointfumee', 'pointeclair', 'freezingpoint', 'residu', 'perte',
                  'massevolumique15', 'viscosite',
                  'pointinflammabilite', 'teneureau', 'corrosion', 'conductivite', 'vol10', 'vol90'),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )


class PetroleLampant(forms.Form):
    aspect = forms.CharField(max_length=32, label='Aspect', required=False)
    couleursaybolt = forms.CharField(max_length=32, label='Couleur SAYBOLT', required=False)
    aciditetotal = forms.CharField(max_length=32, label='Acidité Total mg KOH/g', required=False)
    soufre = forms.CharField(max_length=32, label='Soufre Total en % poids', required=False)
    soufremercaptan = forms.CharField(max_length=32, label='Soufre Mercaptan % m/m', required=False)
    docteurtest = forms.CharField(max_length=32, label='Ou Docteur Test', required=False)
    distillation = forms.CharField(max_length=32, required=False)
    massevolumique15 = forms.CharField(max_length=32, required=False, label='Masse Volumique à 15°C')
    pointinitial = forms.CharField(max_length=32, required=False, label='Point Initial °C')
    vol10 = forms.CharField(max_length=32, required=False, label='10% Vol °C')
    vol90 = forms.CharField(max_length=32, required=False, label='90% Vol °C')
    pointfinal = forms.CharField(max_length=32, required=False, label='Point Final °C')
    residu = forms.CharField(max_length=32, required=False, label='Résidu en % vol')
    perte = forms.CharField(max_length=32, required=False, label='Pertes en % vol')
    viscosite = forms.CharField(max_length=32, required=False, label='Viscosité cinématique')
    pointeclair = forms.CharField(max_length=32, required=False, label="Point d'éclair")
    freezingpoint = forms.CharField(max_length=32, required=False, label='Freezing Point')
    pointfumee = forms.CharField(max_length=32, required=False, label='Point Fumée')
    pointinflammabilite = forms.CharField(max_length=32, required=False, label="Point d'inflammabilité")
    teneureau = forms.CharField(max_length=32, required=False, label='Teneur en eau')
    corrosion = forms.CharField(max_length=32, required=False, label='Corrosion de cuivre')
    conductivite = forms.CharField(max_length=32, required=False, label='Conductivité éléctrique')

    vol20 = forms.CharField(max_length=32, required=False)
    vol30 = forms.CharField(max_length=32, required=False)
    vol40 = forms.CharField(max_length=32, required=False)
    vol50 = forms.CharField(max_length=32, required=False)
    vol60 = forms.CharField(max_length=32, required=False)
    vol70 = forms.CharField(max_length=32, required=False)
    vol80 = forms.CharField(max_length=32, required=False)

    def __init__(self, *args, **kwargs):
        super(PetroleLampant, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(

            Field('aspect', 'couleursaybolt', 'aciditetotal', 'soufre', 'soufremercaptan', 'docteurtest',
                  'distillation',
                  'pointinitial', 'pointfinal', 'pointfumee', 'pointeclair', 'freezingpoint', 'residu', 'perte',
                  'massevolumique15', 'viscosite',
                  'pointinflammabilite', 'teneureau', 'corrosion', 'conductivite', 'vol10', 'vol90'),

            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),

        )
