from django import forms
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
    nouvelleDestination = forms.ModelChoiceField(queryset=Entrepot.objects.all())
    def __init__(self, *args, **kwargs):
        super(ChangementDestination, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_errors = True
        self.helper.label_class = 'col-md-12'
        self.helper.field_class = 'col-md-12'
        self.helper.layout = Layout(
            Row(
                Column('nouvelleDestination', css_class='form-group col-md-6 mb-0'),
            ),
            FormActions(
                Submit('valider', 'valider', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),

            ),
        )

