import django_tables2 as tables
from django_tables2.utils import A
from enreg.models import Cargaison,Dechargement


A1 = """
 <form method=post action="{% url 'numreq' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numreq">
 </form>
"""


A2 = """
 <form method=post action="{% url 'codecam' record.pk%}">
    {% csrf_token %}
     <input type="text" name="codecargaison">
 </form>

"""

B1 = """
 <form method=post action="{% url 'numreq' record.pk%}">
    {% csrf_token %}
    <div class="col-sm-5">
     <input type="text" name="numreq">
     </div>
 </form>
"""


B2 = """
 <form method=post action="{% url 'codecam' record.pk%}">
    {% csrf_token %}
     <input type="text" name="codecargaison">
 </form>

"""

A3 = """
    
    <a href="{%url 'update' record.pk%}" class="btn btn-success">AUTORISER</a>
    
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
    numreqi = tables.TemplateColumn(A1, verbose_name='SAISIE REF.REQUISITION')
    numreq = tables.Column(verbose_name='REF.REQUISITION')
    numdos = tables.Column(verbose_name='NUM DE DOSSIER')
    buttons = tables.TemplateColumn(A3, verbose_name='')
    dateheurecargaison = tables.Column(verbose_name='DATE & HEURE')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot = tables.Column(verbose_name='ENTREPOT')
    produit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOLUME')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    declaration = tables.Column(verbose_name='N°DECLARATION')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'entrepot', 'produit', 'volume', 'immatriculation',
                    'declaration', 'numreq',
                    'numreqi']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport', 'volume15', 'volume20', 'tonnagevide', 'tonnageair',
                   'requisitiondackdate', 'numdos', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control', 'before', 'after', 'controlOrganoleptique']


class ModificationCodification(tables.Table):
    numdossiers = tables.TemplateColumn(B1)
    codecargaisons = tables.TemplateColumn(B2)

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['immatriculation', 't1d', 't1e', 'numdossier', 'codecargaison']
        exclude = ['dateheurecargaison', 'importateur', 'entrepot', 'idcargaison', 'declarant', 'tempcargaison',
                   'densitecargaison', 'idchauffeur', 'nationalite', 'nomchauffeur'
            , 'qrcode', 'poids', 'transporteur', 'impression', 'voie', 'numact', 'conformite',
                   'provenance', 'tampon', 'l_control', 'etat', 'numdeclaration', 'manifestdgda', 'fournisseur',
                   'numbtfh', 'valeurfacture', 'user', 'volume', 'volume_decl15', 'frontiere', 'printactdate',
                   'produit', 'before', 'after']

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
        sequence = ['dateanalyse', 'importateur', 'entrepot', 'immatriculation', 'produit', 'numdossier',
                    'codecargaison', 'conformite']

        exclude = ['idcargaison', 'declarant', 'tempcargaison', 'densitecargaison', 'idchauffeur', 't1d', 't1e',
                   'nationalite', 'nomchauffeur'
            , 'qrcode', 'poids', 'transporteur', 'voie', 'frontiere',
                   'provenance', 'impression', 'l_control', 'volume', 'numdeclaration', 'manifestdgda', 'fournisseur',
                   'numbtfh', 'valeurfacture', 'volume_decl15', 'etat', 'dateheurecargaison', 'user', 'tampon',
                   'numact', 'printactdate']


# class Avarie(tables.Table):
#     actions = tables.TemplateColumn(C)
#     numdossier = tables.Column(verbose_name='# Dos')
#     codecargaison = tables.Column(verbose_name='# Camion')
#     class Meta:
#         attrs = {"class": "table table-hover text-nowrap table-striped"}
#         template_name = "django_tables2/bootstrap4.html"
#         model = Cargaison
#         sequence = ['numdossier','importateur', 'entrepot', 'immatriculation', 'produit']
#         exclude = ['dateheurecargaison','etat','codecargaison','idcargaison', 'declarant', 'tempcargaison', 'densitecargaison', 'idchauffeur', 't1d', 't1e',
#                    'nationalite', 'nomchauffeur'
#             , 'qrcode', 'poids', 'transporteur', 'voie', 'frontiere',
#                    'provenance', 'impression', 'volume','numdeclaration','manifestdgda','fournisseur','numbtfh','valeurfacture', 'volume_decl15', 'etat', 'dateheurecargaison', 'user',
#                    'tampon', 'numact', 'printactdate','l_control']

class NonConformeOrganoleptique(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.")
    idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(verbose_name="PRODUIT DECL.")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    natureProduitEntrepot__nomproduit = tables.Column(verbose_name="PRODUIT CONST.", attrs={"td": {"bgcolor": "red"}})
    # volume = tables.Column(verbose_name="VOLUME DECL.")


class NonConformeLaboratoire(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.")
    idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(verbose_name="PRODUIT")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    # volume = tables.Column(verbose_name="VOLUME DECL.")


class EnAttenteEchantillonage(tables.Table):
    numdos = tables.Column(verbose_name="#.DOS")
    declaration = tables.Column(verbose_name="#.DECL.")
    importateur = tables.Column(verbose_name="FOURNISSEUR")
    entrepot = tables.Column(verbose_name="ENTREPOT")
    produit = tables.Column(verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMAT.")
    requisitiondackdate = tables.Column(verbose_name="DATE REQ.", attrs={"td": {"bgcolor": "red"}})


class EnAttenteDechargement(tables.Table):
    idcargaison__idcargaison__idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__idcargaison__idcargaison__declaration = tables.Column(verbose_name="#.DECL.")
    idcargaison__idcargaison__idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__idcargaison__idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__idcargaison__idcargaison__produit = tables.Column(verbose_name="PRODUIT")
    idcargaison__idcargaison__idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    idcargaison__idcargaison__idcargaison__requisitiondackdate = tables.Column(verbose_name="DATE REQ.")
    idcargaison__idcargaison__dateechantillonage = tables.Column(verbose_name="DATE ECHANT.")
    idcargaison__datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO')
    dateanalyse = tables.Column(verbose_name="DATE D'ANALYSE", attrs={"td": {"bgcolor": "red"}})


class EnAttenteResultatLabo(tables.Table):
    idcargaison__idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__idcargaison__declaration = tables.Column(verbose_name="#.DECL.")
    idcargaison__idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__idcargaison__produit = tables.Column(verbose_name="PRODUIT")
    idcargaison__idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    idcargaison__idcargaison__requisitiondackdate = tables.Column(verbose_name="DATE REQ.")
    idcargaison__dateechantillonage = tables.Column(verbose_name="DATE ECHANT.")
    datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO', attrs={"td": {"bgcolor": "red"}})


class RapportActivite(tables.Table):
    numdos = tables.Column(verbose_name="#.DOS")
    declaration = tables.Column(verbose_name="#.DECL.")
    nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    nomville = tables.Column(verbose_name="FRONTIERE")
    entrepot = tables.Column(verbose_name="ENTREPOT")
    produit = tables.Column(verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMAT.")
    dateheurecargaison = tables.Column(verbose_name="DATE D'ENT.", attrs={"td": {"bgcolor": "yellow"}})
    requisitiondackdate = tables.Column(verbose_name="DATE REQ.", attrs={"td": {"bgcolor": "yellow"}})
    dateechantillonage = tables.Column(verbose_name="DATE ECHANT.", attrs={"td": {"bgcolor": "yellow"}})
    datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO', attrs={"td": {"bgcolor": "yellow"}})
    dateanalyse = tables.Column(verbose_name="DATE D'ANALYSE", attrs={"td": {"bgcolor": "yellow"}})
    dateinspection = tables.Column(verbose_name="DATE D'INSPECTION", attrs={"td": {"bgcolor": "yellow"}},
                                   accessor='Inspection.idcargaison.dateinspection')
    volume = tables.Column(verbose_name="VOL.DECL", attrs={"td": {"bgcolor": "red"}})
    volConst = tables.Column(verbose_name="VOL.CONST", attrs={"td": {"bgcolor": "red"}})
    gsvT = tables.Column(verbose_name='GSV', attrs={"td": {"bgcolor": "green"}})


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

