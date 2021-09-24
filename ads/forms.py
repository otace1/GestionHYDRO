from django import forms
from enreg.models import Entrepot, Importateur, Ville, Produit, Cargaison, Paiement, Liquidation
from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, Row, Reset, Column, Fieldset
from crispy_forms.bootstrap import Field, InlineField, FormActions, StrictButton



# Formulaire pour ajout des entrepots
class EntrepotForm(forms.ModelForm):
    class Meta:
        model = Entrepot
        fields = ['nomentrepot', 'adresseentrepot', 'ville']


# Formulaire d'edition des entrepots
class EntrepotEditForm(forms.ModelForm):
    class Meta:
        model = Entrepot
        fields = ['nomentrepot', 'adresseentrepot', 'ville']


# Formulaire pour Ajout d'importateur
class ImportateurForm(forms.ModelForm):
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
    frontiere = forms.ModelChoiceField(queryset=Ville.objects.all(), label="Entité de prise en charge :",
                                       required=False)
    produit = forms.ModelChoiceField(queryset=Produit.objects.all(), label="Nature du produit :", required=False)
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all(), label="Nom de l'importateur :",
                                         required=False)
    entrepot = forms.ModelChoiceField(queryset=Entrepot.objects.all(), label="Entrepot de destination :",
                                      required=False)
    date_d = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), required=False, label="Date de début :")
    date_f = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), required=False, label="Date de fin :")



# Formulaire de recherche statistique
class RechercheEncaissement(forms.Form):
    query = Paiement.objects.raw('SELECT p.bnk_nam, p.id FROM hydro_occ.enreg_paiement p group by p.bnk_nam')
    bank = []
    for d in query:
        bank.append(d.bnk_nam)
    choix = [(data, data) for data in bank]
    choix.insert(0, ('', ''))
    # bank = [i['bnk_nam'] for i in query]

    frontiere = forms.ModelChoiceField(queryset=Ville.objects.all(), label="Entité de prise en charge :",
                                       required=False)
    importateur = forms.ModelChoiceField(queryset=Importateur.objects.all(), label="Nom de l'importateur :",
                                         required=False)
    banque = forms.ChoiceField(choices=choix, label="Banques", required=False)
    date_d = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), required=False, label="Date de début :")
    date_f = forms.DateField(widget=DatePickerInput(format='%Y-%m-%d'), required=False, label="Date de fin :")


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
