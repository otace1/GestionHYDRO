from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit,Row, Reset, Column, Fieldset, Button
from crispy_forms.bootstrap import Field, InlineField, FormActions,StrictButton
from bootstrap_datepicker_plus import DatePickerInput
from enreg.models import BureauDGDA


paiement = [
    ('total','TOTAL'),
    ('partiel','PARTIEL')
]


class SaisieBL(forms.Form):
    datebl = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de liquidattion :")
    numerobl = forms.CharField(label="Numéro de BL :", widget=forms.TextInput(attrs={'data-mask': "*-****"}))
    codebureau = forms.ModelChoiceField(queryset=BureauDGDA.objects.all(),label='Code Bureau DGDA')
    vol_liq = forms.DecimalField(max_digits=32, label='Volume liquidé :')
    paiement = forms.CharField(widget=forms.Select(choices=paiement),label="type de paiement :", required=False)

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
                Field('numerobl'),
                Field('codebureau'),
                Field('vol_liq'),
                Field('paiement'),
                    ),

            # FormActions(
            #     Submit('valider', 'valider', css_class='btn btn-primary'),
            #     Reset('annuler', 'annuler', css_class='btn btn-danger'),
            #             ),
                                )



