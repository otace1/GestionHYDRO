from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit,Row, Reset, Column, Fieldset, Button
from crispy_forms.bootstrap import Field, InlineField, FormActions,StrictButton
from bootstrap_datepicker_plus import DatePickerInput


etat_physique = [
    ('bon','BON(S)'),
    ('brise','BRISE(S)')
]

conformite_scelle = [
    ('conforme','CONFORME'),
    ('nonconforme','NON CONFORME')
]

class Echantilloner(forms.Form):
    dateechantillonage = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), label="Date de prélèvement :")
    numdossier = forms.CharField(label="Numéro de Dossier :", required=True)
    codecargaison = forms.CharField(label="Code Camion :", required=False)
    numrappech = forms.CharField(label="Numéro rapport d'échantillonage :")
    numplombh = forms.CharField(label="Numéro des Scellés (Haut de la citerne) :")
    numplombb = forms.CharField(label="Numéro des Scellés (Bas de la citerne) :", required=False)
    numplombbr = forms.CharField(label="Numéro des Scellés brisés :", required=False)
    numplombaph = forms.CharField(label="Numéro des Scellés OCC apposes :", required=False)
    etatphysique = forms.CharField(widget=forms.Select(choices=etat_physique),label="Etat physique des plombs :", required=False)
    qte = forms.DecimalField(label="Quantité de produit échantilloner :", required=True)
    conformite = forms.CharField(widget=forms.Select(choices=conformite_scelle),label="Conformité des scellés d'origine :", required=True)

    def __init__(self,*args,**kwargs):
        super(Echantilloner,self).__init__(*args,**kwargs)
        self.helper = FormHelper()
        self.helper.form_class='form-horizontal'
        self.helper.form_id='registration-form'
        self.helper.label_class='col-md-6'
        self.helper.field_class='col-md-6'
        self.helper.layout= Layout(
            Fieldset("",
                Field('dateechantillonage'),
                Field('numdossier'),
                Field('codecargaison'),
                Field('numrappech'),
                Field('numplombh'),
                Field('numplombb'),
                Field('numplombbr'),
                Field('numplombaph'),
                Field('etatphysique'),
                Field('qte'),
                Field('conformite'),
                    ),

            # FormActions(
            #     Submit('valider', 'valider', css_class='btn btn-primary'),
            #     Reset('annuler', 'annuler', css_class='btn btn-danger'),
            #             ),
                                )

class Decharger(forms.Form):
    densite15 = forms.DecimalField(label="Densité du produit a 15 degré :", required=True, min_value=1)
    temperature = forms.DecimalField(label="Température du produit :", required=True, min_value=1)
    gov = forms.DecimalField(label="Gross Observed Volume (GOV) :", required=True, min_value=1)

    def __init__(self,*args,**kwargs):
        super(Decharger,self).__init__(*args,**kwargs)
        self.helper = FormHelper()
        self.helper.form_class='form-horizontal'
        self.helper.form_id='registration-form'
        self.helper.label_class='col-md-4'
        self.helper.field_class='col-md-6'
        self.helper.layout= Layout(
            Fieldset("",
                Field('densite15', placeholder='830.098'),
                Field('temperature',placeholder='20.23'),
                Field('gov', placeholder='32.978'),
                     ),

            # FormActions(
            #     Submit('valider', 'valider', css_class='btn btn-primary'),
            #     Reset('annuler', 'annuler', css_class='btn btn-danger'),
            #             ),
                                 )





