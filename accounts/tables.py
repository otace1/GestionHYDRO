import django_tables2 as tables

from .models import MyUser, AffectationEntrepot

TEMPLATE = """
<a href="{%url 'edit' record.pk%}" class="btn btn-success" aria-hidden="true">Details</a>
<a href="{%url 'delete_user' record.pk%}" class="btn btn-danger" aria-hidden="true">Effacer</a>
            """
TEMPLATE1 = """
<a href="{%url 'retireraffectation' record.pk%}"  class="btn btn-danger" aria-hidden="true">Retirer</a>
"""

class ListeUtilisateurs(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE, verbose_name='')
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = MyUser
        sequence = ['id', 'first_name', 'last_name', 'username', 'role', 'last_login']
        exclude = ['password', 'is_admin', 'is_staff', 'entrepot', 'ville']

class DetailsAffectation(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    class Meta:
        attrs = {"class":"table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = AffectationEntrepot
        exclude = ['idaffectation_entrepot']