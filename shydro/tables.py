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
    importateur__nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot__nomentrepot = tables.Column(verbose_name='ENTREPOT')
    produit__nomproduit = tables.Column(verbose_name='PRODUIT')
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
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.(T1E)")
    idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(verbose_name="PRODUIT")
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
    importateur = tables.Column(verbose_name="IMPORTATEUR")
    entrepot = tables.Column(verbose_name="ENTREPOT")
    produit = tables.Column(verbose_name="PRODUIT")
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
    nomimportateur = tables.Column(verbose_name="IMPORTATEUR")
    nomentrepot = tables.Column(verbose_name="ENTREPOT")
    nomproduit = tables.Column(verbose_name="PRODUIT")
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
    idcargaison__importateur__nomimportateur = tables.Column(verbose_name="IMPORTATEUR")
    idcargaison__entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit__nomproduit = tables.Column(verbose_name="PRODUIT")
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
    idcargaison__importateur__nomimportateur = tables.Column(verbose_name="IMPORTATEUR")
    idcargaison__entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit__nomproduit = tables.Column(verbose_name="PRODUIT")
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
    idcargaison__idcargaison__importateur = tables.Column(verbose_name="IMPORTATEUR")
    idcargaison__idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__idcargaison__produit = tables.Column(verbose_name="PRODUIT")
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
    importateur__nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    frontiere__nomville = tables.Column(verbose_name="FRONTIERE")
    entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")
    produit__nomproduit = tables.Column(verbose_name="PRODUIT")
    immatriculation = tables.Column(verbose_name="IMMAT.")
    dateheurecargaison__date = tables.Column(verbose_name="DATE D'ENT.", attrs={"td": {"bgcolor": "yellow"}})
    requisitiondackdate__date = tables.Column(verbose_name="DATE REQ.", attrs={"td": {"bgcolor": "yellow"}})
    entrepot_echantillon__dateechantillonage__date = tables.Column(verbose_name="DATE ECHANT.", attrs={"td": {"bgcolor": "yellow"}})
    entrepot_echantillon__laboreception__datereceptionlabo__date = tables.Column(verbose_name='DATE REC.LABO', attrs={"td": {"bgcolor": "yellow"}})
    impressionresultat__printDate = tables.Column(verbose_name="DATE D'ANALYSE", attrs={"td": {"bgcolor": "yellow"}})
    inspection__dateinspection = tables.Column(verbose_name="DATE D'INSPECTION", attrs={"td": {"bgcolor": "yellow"}})
    # volume = tables.Column(verbose_name="VOL.DECL", attrs={"td": {"bgcolor": "red"}})
    volume = tables.Column(verbose_name="VOL.DECL")
    inspection__dens = tables.Column(verbose_name='DENS.15')
    inspection__temp = tables.Column(verbose_name='TEMP.ATA')
    mtaTotal = tables.Column(verbose_name='MTA')
    mtvTotal = tables.Column(verbose_name='MTV')
    volConst = tables.Column(verbose_name="GOV")
    gsvT = tables.Column(verbose_name='GSV')
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
    frontiere = tables.Column(verbose_name="FRONTIERE")
    importateur = tables.Column(verbose_name='IMPORTATEUR')
    produit = tables.Column(verbose_name='PRODUIT')
    entrepot = tables.Column(verbose_name="ENTREPOT")
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


# class RapportActivite(tables.Table):
#     # Plain / model fields
#     idcargaison = tables.Column(verbose_name="ID")
#     numdos = tables.Column(verbose_name="Num. Dos")
#     declaration = tables.Column(verbose_name="Déclaration")
#     immatriculation = tables.Column(verbose_name="Immat.")
#     dateheurecargaison = tables.DateTimeColumn(verbose_name="Date Cargaison", format="Y-m-d H:i")
#     requisitiondackdate = tables.DateTimeColumn(verbose_name="Réquisition", format="Y-m-d")
#     volume = tables.Column(verbose_name="Volume")
#
#     # Related fields (use accessors)
#     frontiere__nomville = tables.Column(verbose_name="Frontière", accessor="frontiere.nomville")
#     importateur__nomimportateur = tables.Column(verbose_name="Importateur", accessor="importateur.nomimportateur")
#     entrepot__nomentrepot = tables.Column(verbose_name="Entrepôt", accessor="entrepot.nomentrepot")
#     produit__nomproduit = tables.Column(verbose_name="Produit", accessor="produit.nomproduit")
#     inspection__dens = tables.Column(verbose_name="Densité", accessor="inspection.dens")
#     inspection__temp = tables.Column(verbose_name="Temp.", accessor="inspection.temp")
#     inspection__dateinspection = tables.DateTimeColumn(
#         verbose_name="Date Insp.", accessor="inspection.dateinspection", format="Y-m-d"
#     )
#
#     # Annotated fields from the queryset (.annotate in the view)
#     mtaTotal = tables.Column(verbose_name="MTA Total")
#     mtvTotal = tables.Column(verbose_name="MTV Total")
#     volConst = tables.Column(verbose_name="Vol. Const.")
#     gsvT = tables.Column(verbose_name="GSV Total")
#     echantillon_date = tables.DateTimeColumn(verbose_name="Date Échantillon", format="Y-m-d")
#     labo_recep_date = tables.DateTimeColumn(verbose_name="Date Réception Labo", format="Y-m-d")
#     print_date = tables.DateColumn(verbose_name="Date Impression", format="Y-m-d")
#
#     # Actions
#     actions = tables.TemplateColumn(
#         template_code="""
#           <a href="#" class="btn btn-sm btn-outline-secondary" onclick="confirmAction(event)">Réinspecter</a>
#           <a href="#" class="btn btn-sm btn-outline-primary" onclick="printRappEchantillonnage(event)">Rapport Éch.</a>
#           <a href="#" class="btn btn-sm btn-outline-info" onclick="printRappInspection(event)">Rapport Insp.</a>
#           <a href="#" class="btn btn-sm btn-outline-success" onclick="printDossimport(event)">Dossier</a>
#         """,
#         orderable=False,
#         verbose_name="Actions",
#     )
#
#     # -------- Render helpers (pretty numbers, blank on None) --------
#     @staticmethod
#     def _fmt3(v):
#         try:
#             return f"{float(v):.3f}"
#         except (TypeError, ValueError):
#             return ""
#
#     def render_inspection__dens(self, value):
#         return self._fmt3(value)
#
#     def render_inspection__temp(self, value):
#         return self._fmt3(value)
#
#     def render_mtaTotal(self, value):
#         return self._fmt3(value)
#
#     def render_mtvTotal(self, value):
#         return self._fmt3(value)
#
#     def render_volConst(self, value):
#         return self._fmt3(value)
#
#     def render_gsvT(self, value):
#         return self._fmt3(value)
#
#     def render_volume(self, value):
#         return self._fmt3(value)
#
#     class Meta:
#         attrs = {"class": "table table-striped table-bordered table-sm"}
#         # Keep the tr id so your JS can read it:
#         row_attrs = {"id": lambda record: record.idcargaison}
#         sequence = (
#             "idcargaison",
#             "numdos",
#             "declaration",
#             "frontiere__nomville",
#             "inspection__dens",
#             "inspection__temp",
#             "mtaTotal",
#             "mtvTotal",
#             "entrepot__nomentrepot",
#             "inspection__dateinspection",
#             "importateur__nomimportateur",
#             "immatriculation",
#             "produit__nomproduit",
#             "dateheurecargaison",
#             "requisitiondackdate",
#             "echantillon_date",
#             "labo_recep_date",
#             "print_date",
#             "volume",
#             "volConst",
#             "gsvT",
#             "actions",
#         )

