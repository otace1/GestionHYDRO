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


regularisationButtons = """
                <button type="button" onclick="getRowId(this)" id="data" class="btn btn-default" data-toggle="modal" data-target="#modal-dest">
                  RE-ROUTAGE
                </button>
                <button type="button" onclick="getRowId(this)" id="data" class="btn btn-default" data-toggle="modal" data-target="#modal-trans">
                  TRANSBORDEMENT
                </button>
                <button type="button" onclick="getRowId(this)" id="data" class="btn btn-default" data-toggle="modal" data-target="#modal-fourn">
                  FOURNISSEUR
                </button>
                <button type="button" onclick="getRowId(this)" id="data" class="btn btn-default" data-toggle="modal" data-target="#modal-nat">
                  NATURE PRODUIT
                </button>
 <a href="{%url 'pertes' record.pk%}" class="btn btn-danger" onclick="return confirmAction();">PERTE</a>
"""

# <button type="button" onclick="getRowId(this)" class="btn btn-default" id="record" data-toggle="modal" data-target="#modal-default">
#                   CHANGEMENT DE DESTINATION
#                 </button>

rapportButtons = """
    <a href="{%url 'rapportRe' record.pk%}" class="btn btn-success" onclick="return confirmAction();">RAPP.ECH</a>
    <a href="{%url 'rapportIs' record.pk%}" class="btn btn-warning" onclick="return confirmAction();">RAPP.INSP</a>
"""

nonConforme = """
    <a href="{%url 'consignation' record.pk%}" class="btn btn-success" onclick="return confirmAction();">AUTORISATION DE CONSIGNATION</a>
    <a href="" class="btn btn-success" onclick="return confirmAction();">REFOULEMENT</a>
"""


class CodificationTable(tables.Table):
    dateheurecargaison = tables.Column(verbose_name='DATE & HEURE')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot = tables.Column(verbose_name='ENTREPOT')
    produit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOLUME')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    declaration = tables.Column(verbose_name='#.DECL.(T1D)')
    # numdos = tables.Column(verbose_name='NUM DE DOSSIER')
    numreq = tables.Column(verbose_name='REF.REQUISITION')
    numreqi = tables.TemplateColumn(A1, verbose_name='SAISIE REF.REQUISITION')
    buttons = tables.TemplateColumn(A3, verbose_name='')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # template_name = "django_tables2/bootstrap4-responsive.html"


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


class NonConformeOrganoleptique(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.(T1D)")
    idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(verbose_name="PRODUIT DECL.")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    natureProduitEntrepot__nomproduit = tables.Column(verbose_name="PRODUIT CONST.", attrs={"td": {"bgcolor": "red"}})
    # volume = tables.Column(verbose_name="VOLUME DECL.")

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"




class NonConformeLaboratoire(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.(T1D)")
    idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(verbose_name="PRODUIT")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    actions = tables.TemplateColumn(nonConforme,verbose_name='')
    # volume = tables.Column(verbose_name="VOLUME DECL.")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # template_name = "django_tables2/bootstrap4.html"




class EnAttenteEchantillonage(tables.Table):
    numdos = tables.Column(verbose_name="#.DOS")
    declaration = tables.Column(verbose_name="#.DECL.(T1D)")
    importateur = tables.Column(verbose_name="FOURNISSEUR")
    entrepot = tables.Column(verbose_name="ENTREPOT")
    produit = tables.Column(verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMAT.")
    requisitiondackdate = tables.Column(verbose_name="DATE REQ.", attrs={"td": {"bgcolor": "red"}})


    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # template_name = "django_tables2/bootstrap4.html"



class EnAttenteDechargement(tables.Table):
    numdos = tables.Column(verbose_name="#.DOS")
    declaration = tables.Column(verbose_name="#.DECL.(T1D)")
    nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    nomentrepot = tables.Column(verbose_name="ENTREPOT")
    nomproduit = tables.Column(verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMAT.")
    requisitiondackdate = tables.Column(verbose_name="DATE REQ.")
    dateechantillonage = tables.Column(verbose_name="DATE ECHANT.")
    datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO')
    printDate = tables.Column(verbose_name="DATE D'ANALYSE", attrs={"td": {"bgcolor": "red"}})

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # template_name = "django_tables2/bootstrap4.html"


class EnAttenteResultatLabo(tables.Table):
    idcargaison__idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__idcargaison__declaration = tables.Column(verbose_name="#.DECL.(T1D)")
    idcargaison__idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__idcargaison__produit = tables.Column(verbose_name="PRODUIT")
    idcargaison__idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    idcargaison__idcargaison__requisitiondackdate = tables.Column(verbose_name="DATE REQ.")
    idcargaison__dateechantillonage = tables.Column(verbose_name="DATE ECHANT.")
    datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO', attrs={"td": {"bgcolor": "red"}})

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # template_name = "django_tables2/bootstrap4.html"




class RapportActivite(tables.Table):
    numdos = tables.Column(verbose_name="#.DOS")
    declaration = tables.Column(verbose_name="#.DECL.(T1D)")
    importateur = tables.Column(verbose_name="FOURNISSEUR")
    frontiere = tables.Column(verbose_name="FRONTIERE")
    entrepot = tables.Column(verbose_name="ENTREPOT")
    produit = tables.Column(verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMAT.")
    dateheurecargaison = tables.Column(verbose_name="DATE D'ENT.", attrs={"td": {"bgcolor": "yellow"}})
    requisitiondackdate = tables.Column(verbose_name="DATE REQ.", attrs={"td": {"bgcolor": "yellow"}})
    dateechantillonage = tables.Column(verbose_name="DATE ECHANT.", attrs={"td": {"bgcolor": "yellow"}})
    datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO', attrs={"td": {"bgcolor": "yellow"}})
    printDate = tables.Column(verbose_name="DATE D'ANALYSE", attrs={"td": {"bgcolor": "yellow"}})
    dateinspection = tables.Column(verbose_name="DATE D'INSPECTION", attrs={"td": {"bgcolor": "yellow"}})
    volume = tables.Column(verbose_name="VOL.DECL", attrs={"td": {"bgcolor": "red"}})
    volConst = tables.Column(verbose_name="VOL.CONST", attrs={"td": {"bgcolor": "red"}})
    gsvT = tables.Column(verbose_name='GSV', attrs={"td": {"bgcolor": "green"}})
    actions = tables.TemplateColumn(rapportButtons,verbose_name='')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # template_name = "django_tables2/bootstrap4.html"


class Regularisation(tables.Table):
    dateheurecargaison = tables.Column(verbose_name='DATE ENTR.')
    frontiere = tables.Column(verbose_name='FRONTIERE ENTR.')
    importateur = tables.Column(verbose_name='FOURNISSEUR.')
    produit = tables.Column(verbose_name='PRODUIT.')
    entrepot = tables.Column(verbose_name="ENTREPOT")
    immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    volume = tables.Column(verbose_name="VOL.DECL", attrs={"td": {"bgcolor": "green"}})
    actions = tables.TemplateColumn(regularisationButtons, verbose_name='')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        row_attrs = {
            "id": lambda record: record.pk
        }
        # template_name = "django_tables2/bootstrap4.html"

