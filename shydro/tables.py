import django_tables2 as tables
from django_tables2.utils import A
from enreg.models import Cargaison,Dechargement


A1 = """
 <form method=post action="{% url 'numdoss' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numdossier">
 </form>
"""


A2 = """
 <form method=post action="{% url 'codecam' record.pk%}">
    {% csrf_token %}
     <input type="text" name="codecargaison">
 </form>

"""

B1 = """
 <form method=post action="{% url 'numdoss' record.pk%}">
    {% csrf_token %}
    <div class="col-sm-5">
     <input type="text" name="numdossier">
     </div>
 </form>
"""


B2 = """
 <form method=post action="{% url 'codecam' record.pk%}">
    {% csrf_token %}
     <input type="text" name="codecargaison">
 </form>

"""

A3 ="""
    
    <a href="{%url 'update' record.pk%}" class="btn btn-success">Envoyer</a>
    
"""


B = """<a href="{%url 'go' record.pk%}" class="btn btn-success">GO</a>
            """

C = """<a href="{%url 'update' record.pk%}" class="btn btn-success">Reconditionner</a>
<a href="{%url 'update' record.pk%}" class="btn btn-danger">Refouler</a>

            """

D = """<a href="{%url 'printact' record.pk%}" class="btn btn-success">Imprimer</a>
            """

E = """<a href="{%url 'reprintact' record.pk%}" class="btn btn-success">Ré-Impression</a>
            """


class CodificationTable(tables.Table):
    numdossiers = tables.TemplateColumn(A1, verbose_name='# Dos')
    codecargaisons = tables.TemplateColumn(A2, verbose_name='# Camion')
    buttons = tables.TemplateColumn(A3, verbose_name='')
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model= Cargaison
        sequence =['dateheurecargaison','entrepot','immatriculation','t1d','t1e']
        exclude = ['idcargaison','declarant', 'tempcargaison', 'densitecargaison', 'idchauffeur', 'nationalite', 'nomchauffeur'
                   , 'qrcode', 'poids', 'transporteur','impression','voie','numact', 'conformite',
                   'provenance','tampon','etat','numdeclaration','numdossier','codecargaison','manifestdgda','fournisseur','numbtfh','valeurfacture','user','volume','volume_decl15','frontiere','printactdate','produit','importateur','l_control']

class ModificationCodification(tables.Table):
    numdossiers = tables.TemplateColumn(B1)
    codecargaisons = tables.TemplateColumn(B2)
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model= Cargaison
        sequence = ['immatriculation','t1d','t1e','numdossier','codecargaison']
        exclude = ['dateheurecargaison','importateur','entrepot','idcargaison','declarant', 'tempcargaison', 'densitecargaison', 'idchauffeur', 'nationalite', 'nomchauffeur'
                   , 'qrcode', 'poids', 'transporteur','impression','voie','numact', 'conformite',
                   'provenance','tampon','l_control','etat','numdeclaration','manifestdgda','fournisseur','numbtfh','valeurfacture','user','volume','volume_decl15','frontiere','printactdate','produit']

class ResultatGoLabo(tables.Table):
    actions = tables.TemplateColumn(B, verbose_name='')
    dateanalyse = tables.Column(verbose_name='Date')
    numdossier = tables.Column(verbose_name='# Dos')
    codecargaison = tables.Column(verbose_name='# Camion')
    conformite = tables.Column(verbose_name='Conformité')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateanalyse', 'importateur', 'entrepot', 'immatriculation', 'produit', 'numdossier','codecargaison', 'conformite']

        exclude = ['idcargaison','declarant', 'tempcargaison', 'densitecargaison', 'idchauffeur','t1d','t1e', 'nationalite', 'nomchauffeur'
                   , 'qrcode', 'poids', 'transporteur','voie', 'frontiere',
                'provenance','impression','l_control', 'volume','numdeclaration','manifestdgda','fournisseur','numbtfh','valeurfacture', 'volume_decl15','etat','dateheurecargaison','user','tampon', 'numact','printactdate']

class Avarie(tables.Table):
    actions = tables.TemplateColumn(C)
    numdossier = tables.Column(verbose_name='# Dos')
    codecargaison = tables.Column(verbose_name='# Camion')
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'entrepot', 'immatriculation', 'produit', 'numdossier','codecargaison', 'etat']
        exclude = ['idcargaison', 'declarant', 'tempcargaison', 'densitecargaison', 'idchauffeur', 't1d', 't1e',
                   'nationalite', 'nomchauffeur'
            , 'qrcode', 'poids', 'transporteur', 'voie', 'frontiere',
                   'provenance', 'impression', 'volume','numdeclaration','manifestdgda','fournisseur','numbtfh','valeurfacture', 'volume_decl15', 'etat', 'dateheurecargaison', 'user',
                   'tampon', 'numact', 'printactdate','l_control']

class Act(tables.Table):
    actions = tables.TemplateColumn(D, verbose_name='')
    importateur = tables.Column(verbose_name='Importateur')
    numdossier = tables.Column(verbose_name='# Dos')
    codecargaison = tables.Column(verbose_name='# Camion')
    numcertificatqualite = tables.Column(verbose_name='# CQ')
    datedechargement = tables.Column(verbose_name='Date')
    gsv = tables.Column(verbose_name='GSV')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['datedechargement','numdossier','codecargaison','importateur','immatriculation','gsv']
        exclude = ['idcargaison','provenance','transporteur','poids','volume','tempcargaison','densitecargaison','t1d', 't1e','idchauffeur', 'nationalite','nomchauffeur', 'dateheurecargaison','qrcode', 'etat','volume_decl15',
                   'numact','conformite','impression','l_control','declarant','numdeclaration','manifestdgda','fournisseur','numbtfh','valeurfacture','numcertificatqualite','frontiere','produit','voie','user','tampon', 'entrepot','printactdate']


class Act2(tables.Table):
    actions = tables.TemplateColumn(E, verbose_name='')
    printactdate = tables.Column(verbose_name="Date")
    importateur = tables.Column(verbose_name='Importateur')
    numdossier = tables.Column(verbose_name='# Dos')
    codecargaison = tables.Column(verbose_name='# Camion')
    numcertificatqualite = tables.Column(verbose_name='N° CQ')
    datedechargement = tables.Column(verbose_name='Date déch.')
    numact = tables.Column(verbose_name='# ACT')
    gsv = tables.Column(verbose_name='GSV')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['printactdate','numact', 'numdossier', 'codecargaison','gsv']
        exclude = ['datedechargement', 'idcargaison', 'provenance', 'transporteur', 'declarant', 'poids', 'volume', 'tempcargaison',
                   'densitecargaison', 't1d', 't1e', 'idchauffeur', 'nationalite', 'nomchauffeur', 'dateheurecargaison',
                   'qrcode', 'etat','importateur', 'volume_decl15',
                   'conformite', 'impression','numdeclaration','manifestdgda','fournisseur','numbtfh','valeurfacture', 'frontiere', 'produit', 'voie', 'user', 'tampon', 'entrepot',
                   'immatriculation','l_control','numcertificatqualite']

