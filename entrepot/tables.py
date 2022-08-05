import django_tables2 as tables
from enreg.models import Cargaison, Entrepot_echantillon, Dechargement

TEMPLATE = """
            <a href="{%url 'echantillonage' record.pk%}" target="_blank" class="btn btn-primary">ECHANTILLONNAGE</a>
           """

TEMPLATE1 = """
            <a href="{%url 'choiceoftype' record.pk%}" class="btn btn-primary">INSPECTION</a>
           """

TEMPLATE2 = """
    <a href="{%url 'rapport' record.pk%}" class="btn btn-danger">RAPPORT D'INSPECTION</a>
    <a href="{%url 'printcert' record.pk%}" class="btn btn-primary">CERTIFICAT DE QUALITE</a>
            """

TEMPLATE3 = """
    <a href="{%url 'rapportechantillonage' record.pk%}" class="btn btn-danger">RAPPORT D'ECHANTILLONNAGE</a>
            """


class EchantillonTable(tables.Table):
    Echantilloner = tables.TemplateColumn(TEMPLATE, verbose_name='')
    dateheurecargaison = tables.Column(verbose_name="DATE ENT.")
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    numreq = tables.Column(verbose_name='REF.REQ.')
    numdos = tables.Column(verbose_name='NUM.DOSSIER')
    idcargaison = tables.Column(verbose_name='N.Enr.')
    numreq = tables.Column(verbose_name='N.Requisition')
    numdos = tables.Column(verbose_name='N.Dossier')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'produit', 'immatriculation', 'numreq', 'numdos']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport', 'entrepot', 'volume15', 'volume20', 'tonnagevide', 'tonnageair',
                   'requisitiondackdate', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control']


class CargaisonEnAttenteRequisition(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="Date d'entree")
    idcargaison = tables.Column(verbose_name='N.Enr.')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'produit', 'immatriculation']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport',
                   'requisitiondackdate', 'numdos', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control']


class RapportEchantillonage(tables.Table):
    impressionre = tables.TemplateColumn(TEMPLATE3, verbose_name='')
    dateheurecargaison = tables.Column(verbose_name="Date d'entree")
    idcargaison = tables.Column(verbose_name='N.Enr.')
    numreq = tables.Column(verbose_name='N.Requisition')
    numdos = tables.Column(verbose_name='N.Dossier')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'produit', 'immatriculation',
                    'numreq', 'numdos']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport',
                   'requisitiondackdate', 'numdos', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control']


class CargaisonDechargement(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    # numdossier = tables.Column(verbose_name='Num. Dossier')
    # codecargaison = tables.Column(verbose_name='#Camion/Wagon/Navire')
    produit = tables.Column(verbose_name='PRODUIT')
    # massevolumique15 = tables.Column(verbose_name='Densité a 15°')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    # idcargaison__idcargaison__idcargaison__numreq = tables.Column(verbose_name='Ref. requisition Client')
    numdos = tables.Column(verbose_name='NUM. DOSSIER')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "DechargementTable"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        row_attrs = {
            "id": lambda record: record.pk
        }
        sequence = ['importateur',
                    'numdos',
                    'immatriculation',
                    'produit']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport', 'volume15', 'volume', 'volume20', 'tonnagevide', 'tonnageair',
                   'dateheurecargaison',
                   'requisitiondackdate', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control']


class CargaisonDechargement2(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    # numdossier = tables.Column(verbose_name='Num. Dossier')
    # codecargaison = tables.Column(verbose_name='#Camion/Wagon/Navire')
    produit = tables.Column(verbose_name='PRODUIT')
    # massevolumique15 = tables.Column(verbose_name='Densité a 15°')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    # idcargaison__idcargaison__idcargaison__numreq = tables.Column(verbose_name='Ref. requisition Client')
    numdos = tables.Column(verbose_name='NUM. DOSSIER')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "DechargementTable"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        row_attrs = {
            "id": lambda record: record.pk
        }
        sequence = ['importateur',
                    'numdos',
                    'immatriculation',
                    'produit']
        exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport', 'volume15', 'volume', 'volume20', 'tonnagevide', 'tonnageair',
                   'dateheurecargaison',
                   'requisitiondackdate', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control']

class EchantillonEnregistrer(tables.Table):
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'importateur', 'immatriculation', 'produit', 't1d', 't1e']
        exclude = ['idcargaison', 'declarant', 'voie', 'tempcargaison', 'densitecargaison', 'idchauffeur', 'nationalite'
            , 'qrcode', 'poids', 'transporteur', 'numdeclaration', 'manifestdgda', 'fournisseur', 'numbtfh',
                   'valeurfacture', 'etat', 'frontiere', 'entrepot', 'impression', 'volume', 'volume_decl15',
                   'nomchauffeur', 'conformite', 'provenance', 'numact', 'user', 'tampon', 'printactdate', 'numdossier',
                   'codecargaison', 'printactdate','l_control']


class CargaisonDechargee(tables.Table):
    Actions = tables.TemplateColumn(TEMPLATE2, verbose_name='')
    gov = tables.Column(verbose_name='GOV')
    gsv = tables.Column(verbose_name='GSV')
    mta = tables.Column(verbose_name='MTA')
    mtv = tables.Column(verbose_name='MTV')
    idcargaison__idcargaison__idcargaison__idcargaison__immatriculation = tables.Column(verbose_name='Immatriculation')
    idcargaison__idcargaison__idcargaison__idcargaison__numdos = tables.Column(verbose_name='Num. Dossier')
    idcargaison__idcargaison__idcargaison__idcargaison__numreq = tables.Column(verbose_name='Ref. Req.')
    datedechargement = tables.Column(verbose_name='Date D.')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Dechargement
        sequence = ['datedechargement', 'idcargaison__idcargaison__idcargaison__idcargaison__numdos',
                    'idcargaison__idcargaison__idcargaison__idcargaison__immatriculation', 'mta', 'mtv', 'gov', 'gsv']
        exclude = ['idcargaison_id', 'temperature', 'densite15', 'idcargaison', 'vcf', 'indexinitial', 'indexfinal',
                   'typescontainer', 'idcargaison__idcargaison__idcargaison__idcargaison__numreq']
