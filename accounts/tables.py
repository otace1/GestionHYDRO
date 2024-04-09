import django_tables2 as tables

from .models import MyUser, AffectationEntrepot, AffectationVille

TEMPLATE = """
<a class="btn btn-success" aria-hidden="true" id="detail-button">Details </a>
<a class="btn btn-success" aria-hidden="true" id="detail-button">Signature </a>
<a href="{%url 'createToken' record.pk%}" class="btn btn-success" aria-hidden="true">Create APP Token</a>
<a href="{%url 'delete_user' record.pk%}" class="btn btn-danger" aria-hidden="true">Effacer</a>
            """

# FILEUPLOAD = """
#     <form id="upload-form" method="post" enctype="multipart/form-data">
#         {% csrf_token %}
#         <input type="file" name="file" id="file" accept="image/png">
#         <!-- Hidden input field to store the row id -->
#         <input type="hidden" name="row_id" id="row_id">
#         <button type="submit">Signature</button>
#     </form>
# """

TEMPLATE1 = """
<a href="{%url 'retireraffectation' record.pk%}"  class="btn btn-danger" aria-hidden="true">Retirer</a>
"""

TEMPLATE2 = """
<a href="{%url 'retireraffectationville' record.pk%}"  class="btn btn-danger" aria-hidden="true">Retirer</a>
"""

TEMPLATE3 = """
<a href="{%url 'sign_it' record.pk%}"  class="btn btn-danger" aria-hidden="true">Ajout Signature</a>
"""


class ListeUtilisateurs(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE, verbose_name='')
    # file_upload = tables.TemplateColumn(FILEUPLOAD, verbose_name='')
    id = tables.Column(verbose_name='USER ID')
    first_name = tables.Column(verbose_name='FIRSTNAME')
    last_name = tables.Column(verbose_name='LASTNAME')
    username = tables.Column(verbose_name='USERNAME')
    # fonction = tables.Column(verbose_name='FONCTION')
    # poste = tables.Column(verbose_name='POSTE   ')
    role = tables.Column(verbose_name='APP LEVEL')
    last_login = tables.Column(verbose_name='DERNIERE CONNEXION')


    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "liste-user"
        }
        row_attrs = {
            "id": lambda record: record.pk
        }
        template_name = "django_tables2/bootstrap4.html"
        model = MyUser
        sequence = ['id', 'first_name', 'last_name', 'username', 'role', 'last_login',]
        exclude = ['password', 'is_admin', 'is_staff', 'entrepot', 'ville','fonction','poste']


class DetailsAffectation(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = AffectationEntrepot
        exclude = ['idaffectation_entrepot']


class DetailsVille(tables.Table):
    action = tables.TemplateColumn(TEMPLATE2, verbose_name='')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = AffectationVille
        exclude = ['idaffectation_ville']


class SignatureTable(tables.Table):
    action = tables.TemplateColumn(TEMPLATE3, verbose_name='')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = MyUser
        sequence = ['first_name', 'last_name', 'fonction', 'last_login']
        exclude = ['id', 'password', 'username', 'is_admin', 'is_staff', 'signature']
