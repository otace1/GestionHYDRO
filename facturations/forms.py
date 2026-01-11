from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.bootstrap import Field, FormActions
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Layout, Row, Column, Submit, Reset
from django import forms

from enreg.models import BureauDGDA, LiquidationModel, Banques

paiement_choices = [
    ('total', 'TOTAL'),
    ('partiel', 'PARTIEL')
]


class SaisieBL(forms.Form):
    datebl = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="DATE BL")
    datepay = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="DATE PAIEMENT")
    codebureau = forms.ModelChoiceField(queryset=BureauDGDA.objects.all(), label='CODE BUREAU')
    numerobl = forms.IntegerField(label="N° BL")
    bankName = forms.ModelChoiceField(queryset=Banques.objects.all(), label='BANQUE')
    modele = forms.ModelChoiceField(queryset=LiquidationModel.objects.all(), label='MODÈLE')
    vol_liq = forms.DecimalField(max_digits=32, label='VOL. PAYÉ')
    paiement = forms.ChoiceField(choices=paiement_choices, label="TYPE APPUREMENT", required=False)

    def __init__(self, *args, **kwargs):
        super(SaisieBL, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'post-form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('datebl', css_class='form-group col-md-6 mb-0'),
                Column('datepay', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('codebureau', css_class='form-group col-md-6 mb-0'),
                Column('numerobl', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('modele', css_class='form-group col-md-6 mb-0'),
                Column('bankName', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('vol_liq', css_class='form-group col-md-6 mb-0'),
                Column('paiement', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('ENREGISTRER', 'ENREGISTRER', css_class='btn btn-success px-5 font-weight-bold'),
                Reset('ANNULER', 'ANNULER', css_class='btn btn-outline-secondary px-5'),
            ),
        )



