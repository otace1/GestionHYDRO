from bootstrap_datepicker_plus.widgets import DatePickerInput
from crispy_forms.bootstrap import Field
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Fieldset
from django import forms

from enreg.models import BureauDGDA, LiquidationModel, Banques

paiement = [
    ('total', 'TOTAL'),
    ('partiel', 'PARTIEL')
]


class SaisieBL(forms.Form):
    datebl = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="DATE BL:")
    datepay = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="DATE PAIEMENT:")
    codebureau = forms.ModelChoiceField(queryset=BureauDGDA.objects.all(), label='CODE BUREAU')
    numerobl = forms.IntegerField(label="NUMERO BL :")
    quittance = forms.CharField(max_length=64, label='NUM QUITTANCE')
    bankName = forms.ModelChoiceField(queryset=Banques.objects.all(), label='BANQUE')
    modele = forms.ModelChoiceField(queryset=LiquidationModel.objects.all(), label='MODELE')
    vol_liq = forms.DecimalField(max_digits=32, label='VOL.PAYE:')
    paiement = forms.CharField(widget=forms.Select(choices=paiement),label="APPUREMENT:", required=False)

    def __init__(self,*args,**kwargs):
        super(SaisieBL,self).__init__(*args,**kwargs)
        self.helper = FormHelper()
        self.helper.form_class='form-horizontal'
        self.helper.form_id='registration-form'
        self.helper.label_class='col-md-6'
        self.helper.field_class='col-md-6'
        self.helper.layout= Layout(
            Fieldset("",
                Field('datebl'),
                Field('datepay'),
                Field('codebureau'),
                Field('numerobl'),
                Field('modele'),
                Field('vol_liq'),
                Field('bankName'),
                Field('paiement'),
                    ),

            # FormActions(
            #     Submit('valider', 'valider', css_class='btn btn-primary'),
            #     Reset('annuler', 'annuler', css_class='btn btn-danger'),
            #             ),
                                )



