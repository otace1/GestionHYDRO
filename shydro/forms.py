from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit,Row, Reset, Column, Fieldset
from crispy_forms.bootstrap import Field, InlineField, FormActions,StrictButton
from django_countries.fields import CountryField
from enreg.models import Cargaison, Entrepot_echantillon

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