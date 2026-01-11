import django_tables2 as tables

from enreg.models import Cargaison

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
                  TRANSBOR.
                </button>
                <button type="button" onclick="getRowId(this)" id="data" class="btn btn-default" data-toggle="modal" data-target="#modal-fourn">
                  IMPORT.
                </button>
                <button type="button" onclick="getRowId(this)" id="data" class="btn btn-default" data-toggle="modal" data-target="#modal-nat">
                  PRODUIT
                </button>
 <a href="{%url 'pertes' record.pk%}" class="btn btn-danger" onclick="return confirmAction();">SUPPR.</a>
"""

# <button type="button" onclick="getRowId(this)" class="btn btn-default" id="record" data-toggle="modal" data-target="#modal-default">
#                   CHANGEMENT DE DESTINATION
#                 </button>

# rapportButtons = """ <a class="btn btn-warning" onclick="return confirmAction();">Re-INSPECTER</a> """

rapportButtons = """
<div>
        <div class="btn-group">
            <button type="button" class="btn btn-info">Actions</button>
            <button type="button" class="btn btn-info dropdown-toggle dropdown-hover dropdown-icon" data-toggle="dropdown">
              <span class="sr-only">Toggle Dropdown</span>
            </button>
            <div class="dropdown-menu" role="menu">
              <a class="dropdown-item" onclick="return confirmAction();">Re-Inspecter</a>
              <div class="dropdown-divider"></div>
              <a class="dropdown-item" onclick="return printRappEchantillonnage();">Rapport d'Ech.</a>
              <a class="dropdown-item" onclick="return printRappInspection();">Rapport d'Insp.</a>
              <a class="dropdown-item" onclick="return printDossimport();">Dossier Import.</a>
            </div>
        </div>
"""

nonConforme = """
    <a href="{%url 'consignation' record.pk%}" class="btn btn-success" onclick="return confirmAction();">AUTORISATION DE CONSIGNATION</a>
    <a href="" class="btn btn-success" onclick="return confirmAction();">REFOULEMENT</a>
"""


class CodificationTable(tables.Table):
    dateheurecargaison__date = tables.Column(verbose_name='DATE & HEURE')
    importateur = tables.Column(accessor='nom_importateur', verbose_name='FOURNISSEUR')
    entrepot = tables.Column(accessor='nom_entrepot', verbose_name='ENTREPOT')
    produit = tables.Column(accessor='nom_produit', verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOLUME')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    declaration = tables.Column(verbose_name='#.DECL.(T1E)')
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
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.(T1E)")
    idcargaison__importateur = tables.Column(accessor='idcargaison.nom_importateur', verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(accessor='idcargaison.nom_entrepot', verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(accessor='idcargaison.nom_produit', verbose_name="PRODUIT DECL.")
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
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.(T1E)")
    idcargaison__importateur = tables.Column(accessor='idcargaison.nom_importateur', verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(accessor='idcargaison.nom_entrepot', verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(accessor='idcargaison.nom_produit', verbose_name="PRODUIT")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    actions = tables.TemplateColumn(nonConforme,verbose_name='',exclude_from_export=True)
    # volume = tables.Column(verbose_name="VOLUME DECL.")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            # "id": "example1"
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class EnAttenteEchantillonage(tables.Table):
    numdos = tables.Column(verbose_name="#. DOSSIER")
    declaration = tables.Column(verbose_name="#.DECL.(T1E)")
    importateur = tables.Column(accessor='nom_importateur', verbose_name="IMPORTATEUR")
    entrepot = tables.Column(accessor='nom_entrepot', verbose_name="ENTREPOT")
    produit = tables.Column(accessor='nom_produit', verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    requisitiondackdate = tables.Column(verbose_name="DATE REQUISITION", attrs={"td": {"bgcolor": "red"}})


    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            # "id": "example1"
        }
        template_name = "django_tables2/bootstrap5-responsive.html"



class EnAttenteDechargement(tables.Table):
    numdos = tables.Column(verbose_name="#. DOSSIER")
    declaration = tables.Column(verbose_name="#. DECLARATION")
    nomimportateur = tables.Column(accessor='nom_importateur', verbose_name="IMPORTATEUR")
    nomentrepot = tables.Column(accessor='nom_entrepot', verbose_name="ENTREPOT")
    nomproduit = tables.Column(accessor='nom_produit', verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    requisitiondackdate = tables.Column(verbose_name="DATE REQUISITION")
    dateechantillonage = tables.Column(verbose_name="DATE ECHANTILLONNAGE")
    datereceptionlabo = tables.Column(verbose_name='DATE RECEPTION LABO')
    printDate = tables.Column(verbose_name="DATE D'ANALYSE", attrs={"td": {"bgcolor": "red"}})

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            # "id": "example1"
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class EnAttenteReceptionLabo(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#. DOSSIER")
    idcargaison__declaration = tables.Column(verbose_name="#. DECLARATION")
    idcargaison__importateur__nomimportateur = tables.Column(accessor='idcargaison.nom_importateur', verbose_name="IMPORTATEUR")
    idcargaison__entrepot__nomentrepot = tables.Column(accessor='idcargaison.nom_entrepot', verbose_name="ENTREPOT")
    idcargaison__produit__nomproduit = tables.Column(accessor='idcargaison.nom_produit', verbose_name="PRODUIT")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    idcargaison__requisitiondackdate = tables.Column(verbose_name="DATE REQUISITION")
    dateechantillonage__date = tables.Column(verbose_name="DATE ECHANTILLONNAGE")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class EnAttenteInspection(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#. DOSSIER")
    idcargaison__declaration = tables.Column(verbose_name="#. DECLARATION")
    idcargaison__importateur__nomimportateur = tables.Column(accessor='idcargaison.nom_importateur', verbose_name="IMPORTATEUR")
    idcargaison__entrepot__nomentrepot = tables.Column(accessor='idcargaison.nom_entrepot', verbose_name="ENTREPOT")
    idcargaison__produit__nomproduit = tables.Column(accessor='idcargaison.nom_produit', verbose_name="PRODUIT")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    idcargaison__requisitiondackdate = tables.Column(verbose_name="DATE REQUISITION")
    # dateechantillonage__date = tables.Column(verbose_name="DATE ECHANTILLONNAGE")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class EnAttenteResultatLabo(tables.Table):
    idcargaison__idcargaison__numdos = tables.Column(verbose_name="#. DOSSIER")
    idcargaison__idcargaison__declaration = tables.Column(verbose_name="#. DECLARATION")
    idcargaison__idcargaison__importateur = tables.Column(accessor='idcargaison.idcargaison.nom_importateur', verbose_name="IMPORTATEUR")
    idcargaison__idcargaison__entrepot = tables.Column(accessor='idcargaison.idcargaison.nom_entrepot', verbose_name="ENTREPOT")
    idcargaison__idcargaison__produit = tables.Column(accessor='idcargaison.idcargaison.nom_produit', verbose_name="PRODUIT")
    idcargaison__idcargaison__immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    idcargaison__idcargaison__requisitiondackdate = tables.Column(verbose_name="DATE REQUISITION")
    idcargaison__dateechantillonage = tables.Column(verbose_name="DATE ECHANTILLONNAGE")
    datereceptionlabo = tables.Column(verbose_name='DATE RECEPTION LABO', attrs={"td": {"bgcolor": "red"}})

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            # "id": "example1"
        }
        template_name = "django_tables2/bootstrap5-responsive.html"


class RapportActivite(tables.Table):
    numdos = tables.Column(verbose_name="#.DOS")
    declaration = tables.Column(verbose_name="#.DECL.(T1E)")
    nom_importateur = tables.Column(verbose_name="FOURNISSEUR")
    nom_frontiere = tables.Column(verbose_name="FRONTIERE")
    nom_entrepot = tables.Column(verbose_name="ENTREPOT")
    nom_produit = tables.Column(verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMAT.")
    dateheurecargaison = tables.Column(verbose_name="DATE D'ENT.", attrs={"td": {"bgcolor": "yellow"}})
    requisitiondackdate = tables.Column(verbose_name="DATE REQ.", attrs={"td": {"bgcolor": "yellow"}})
    date_echantillon = tables.Column(verbose_name="DATE ECHANT.", attrs={"td": {"bgcolor": "yellow"}})
    date_reception_labo = tables.Column(verbose_name='DATE REC.LABO', attrs={"td": {"bgcolor": "yellow"}})
    date_analyse = tables.Column(verbose_name="DATE D'ANALYSE", attrs={"td": {"bgcolor": "yellow"}})
    date_inspection = tables.Column(verbose_name="DATE D'INSPECTION", attrs={"td": {"bgcolor": "yellow"}})
    # volume = tables.Column(verbose_name="VOL.DECL", attrs={"td": {"bgcolor": "red"}})
    volume = tables.Column(verbose_name="VOL.DECL")
    inspection__dens = tables.Column(verbose_name='DENS.15')
    inspection__temp = tables.Column(verbose_name='TEMP.ATA')
    mta_total = tables.Column(verbose_name='MTA')
    mtv_total = tables.Column(verbose_name='MTV')
    gov_total = tables.Column(verbose_name="GOV")
    gsv_total = tables.Column(verbose_name='GSV')
    actions = tables.TemplateColumn(rapportButtons,verbose_name='',exclude_from_export=True)

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            # "id": "example1"
        }
        row_attrs = {
            "id": lambda record: record['idcargaison']
        }
        template_name = "django_tables2/bootstrap5-responsive.html"



class Regularisation(tables.Table):
    dateheurecargaison = tables.Column(verbose_name='DATE ENTREE')
    nom_frontiere = tables.Column(verbose_name="FRONTIERE")
    nom_importateur = tables.Column(verbose_name='IMPORTATEUR')
    nom_produit = tables.Column(verbose_name='PRODUIT')
    nom_entrepot = tables.Column(verbose_name="ENTREPOT")
    immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    volume = tables.Column(verbose_name="VOL.DECL")
    actions = tables.TemplateColumn(regularisationButtons, verbose_name='',exclude_from_export=True)

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            # "id": "example1"
        }
        row_attrs = {
            "id": lambda record: record.pk
        }
        template_name = "django_tables2/bootstrap5-responsive.html"

