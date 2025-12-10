from crispy_forms.bootstrap import Field, FormActions
# from bootstrap_daterangepicker import widgets, fields
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column, Fieldset
from django import forms

from enreg.models import *


# Formulaire pour ajout des entrepots
class EntrepotForm(forms.ModelForm):
    class Meta:
        model = Entrepot
        fields = ['nomentrepot', 'adresseentrepot', 'ville']



# Formulaire d'edition des entrepots
class EntrepotEditForm(forms.ModelForm):
    nomentrepot = forms.CharField()
    adresseentrepot = forms.CharField()

    class Meta:
        model = Entrepot
        fields = ['nomentrepot', 'adresseentrepot', 'ville']

    def __init__(self, *args, **kwargs):
        super(EntrepotEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-6'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Row("",
                Column('nomentrepot', css_class='form-group col-md-6'),
                css_class='form-row'
                ),
            Row("",
                Column('adresseentrepot', css_class='form-group col-md-6'),
                css_class='form-row'
                ),
            Row("",
                Column('ville', css_class='form-group col-md-6'),
                css_class='form-row'
                ),

            FormActions(
                Submit('soumettre', 'soumettre', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )


# Formulaire pour Ajout d'importateur
class ImportateurForm(forms.ModelForm):
    nomimportateur = forms.CharField()
    adresseimportateur = forms.CharField()

    class Meta:
        model = Importateur
        fields = ['idimportateur', 'nomimportateur', 'adresseimportateur']


# Formulaire edition importateur
class ImportateurEditForm(forms.ModelForm):
    class Meta:
        model = Importateur
        fields = ['idimportateur', 'nomimportateur', 'adresseimportateur']


# Formulaire ajout ville
class VilleForm(forms.ModelForm):
    class Meta:
        model = Ville
        fields = ['idville', 'nomville', 'province']


# Formulaire edition ville
class VilleEditForm(forms.ModelForm):
    class Meta:
        model = Ville
        fields = ['idville', 'nomville', 'province']


# Formulaire ajout produit
class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['idproduit', 'nomproduit']


# Formulaire edition produit
class ProduitEditForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['idproduit', 'nomproduit']


# Formulaire de recherche statistique
class RechercheStat(forms.Form):
    ville = forms.ModelChoiceField(queryset=Ville.objects.all(), label="ENTITE:", required=False)
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label="PRODUIT:", required=False)
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all(), label="IMPORTATEUR:", required=False)
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all(), label="ENTREPOT:", required=False)
    date_d = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='DATE DEBUT', required=False)
    date_f = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='DATE FIN', required=False)

    def __init__(self, *args, **kwargs):
        # Optionally accept a user to filter available choices
        user = kwargs.pop('user', None)
        super(RechercheStat, self).__init__(*args, **kwargs)

        # Restrict Ville choices to those where the user is affected, if a user is provided
        try:
            if user is not None and getattr(user, 'id', None):
                self.fields['ville'].queryset = Ville.objects.filter(
                    affectationville__username_id=user.id
                ).distinct()
        except Exception:
            # Fail-safe: keep default queryset if anything goes wrong
            pass
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'registration-form'
        self.helper.label_class = 'col-md-6'
        self.helper.field_class = 'col-md-6'
        self.helper.form_show_buttons = False  # 👈 Hide default form buttons
        self.helper.layout = Layout(
            Row(Column('ville', css_class='form-group col-md-12 mb-0')),
            Row(Column('produit', css_class='form-group col-md-12 mb-0')),
            Row(Column('importateur', css_class='form-group col-md-12 mb-0')),
            Row(Column('entrepot', css_class='form-group col-md-12 mb-0')),
            Row(Column('date_d', css_class='form-group col-md-12 mb-0')),
            Row(Column('date_f', css_class='form-group col-md-12 mb-0')),
        )



# Formulaire de recherche statistique
class RechercheEncaissement(forms.Form):
    pass
    # query = Paiement.objects.raw('SELECT p.bnk_nam, p.id FROM hydro_occ.enreg_paiement p group by p.bnk_nam')
    # bank = []
    # for d in query:
    #     bank.append(d.bnk_nam)
    # choix = [(data, data) for data in bank]
    # choix.insert(0, ('', ''))
    # # bank = [i['bnk_nam'] for i in query]
    #
    # frontiere = forms.ModelChoiceField(queryset=Ville.objects.all(), label="Entité de prise en charge :",
    #                                    required=False)
    # importateur = forms.ModelChoiceField(queryset=Importateur.objects.all(), label="Nom de l'importateur :",
    #                                      required=False)
    # banque = forms.ChoiceField(choices=choix, label="Banques", required=False)
    # date_d = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), required=False, label="Date de début :")
    # date_f = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), required=False, label="Date de fin :")


# Formulaire importation
class Import_Importateur(forms.Form):
    fichier = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(Import_Importateur, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.form_show_labels = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-8'
        self.helper.layout = Layout(
            Fieldset("Choix du fichier de données à uploader",
                     Field('fichier')),
            FormActions(
                Submit('uploader', 'uploader', css_class='btn btn-primary'),
                Reset('annuler', 'annuler', css_class='btn btn-danger'),
            ),
        )
