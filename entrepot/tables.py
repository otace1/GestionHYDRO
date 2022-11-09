import django_tables2 as tables
from enreg.models import Cargaison, Entrepot_echantillon, Dechargement
from django.urls import reverse
from django.utils.safestring import mark_safe


# TEMPLATE = """
#             <a href="{%url 'echantillonage' record.pk%}" target="_blank" class="btn btn-primary">ECHANTILLONNAGE</a>
#            """


TEMPLATE6 = """
            <a href="{%url 'meterafter' record.pk%}" class="btn btn-primary">DECHARGEMENT</a>
           """

TEMPLATE = """
            <a href="{%url 'echantillonage' record.pk%}" class="btn btn-primary">ECHANTILLONNAGE</a>
           """

TEMPLATE1 = """
            <a href="{%url 'choiceoftype' record.pk%}" class="btn btn-primary">INSPECTION</a>
           """

TEMPLATE4 = """
            <a href="{%url 'choiceoftype' record.pk%}" class="btn btn-primary">INSPECTION AFTER</a>
           """

TEMPLATE2 = """
    <a href="{%url 'rapport' record.pk%}" class="btn btn-danger">RAPPORT D'INSPECTION</a>
    <a href="{%url 'printcert' record.pk%}" class="btn btn-primary">CERTIFICAT DE QUALITE</a>
            """

TEMPLATE3 = """
    <a href="{%url 'rapportechantillonage' record.pk%}" class="btn btn-danger">RAPPORT D'ECHANTILLONNAGE</a>
            """

TEMPLATE5 = """
    <a href="{%url 'rapport' record.pk%}" class="btn btn-danger">RE</a>
    <a href="{%url 'rapport' record.pk%}" class="btn btn-danger">CQ</a>
    <a href="{%url 'rapport' record.pk%}" class="btn btn-danger">RI</a>
            """

A = """
    <a href="{%url 'correctionConformiteProduit' record.pk%}" class="btn btn-danger">CORRECTION</a>
            """


class EchantillonTable(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="DATE ENT.")
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    numreq = tables.Column(verbose_name='REF.REQ.')
    numdos = tables.Column(verbose_name='NUM.DOSSIER')
    idcargaison = tables.Column(verbose_name='N.ENR.')
    declaration = tables.Column(verbose_name='N.DECL.')
    echantilloner = tables.TemplateColumn(TEMPLATE, verbose_name='')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        # model = Cargaison
        # sequence = ['dateheurecargaison', 'importateur', 'produit', 'immatriculation', 'numdos', 'declaration']
        # exclude = ['idcargaison', 'valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
        #            'typeunitetransport', 'entrepot', 'volume15', 'volume20', 'tonnagevide', 'tonnageair',
        #            'requisitiondackdate', 'voie', 'provenance', 'poids', 'numreq',
        #            'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
        #            'tampon', 'printactdate', 'l_control', 'before', 'after', 'volume', 'controlOrganoleptique']


class CargaisonEnAttenteRequisition(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="DATE ENTREE.")
    idcargaison = tables.Column(verbose_name='N.Enr.')
    declaration = tables.Column(verbose_name='N.DECL.')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION.')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    frontiere = tables.Column(verbose_name="FRONTIERE D'ENT.")
    produit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOL.DECL.(Cu.MTrs)')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['idcargaison', 'declaration', 'dateheurecargaison', 'frontiere', 'importateur', 'produit', 'volume',
                    'immatriculation']
        exclude = ['valeurfacture', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport',
                   'requisitiondackdate', 'numdos', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control', 'volume15', 'volume20', 'tonnagevide', 'tonnageair'
            , 'before', 'after', 'entrepot', 'controlOrganoleptique']


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
    actions = tables.TemplateColumn(TEMPLATE6, verbose_name='')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    numdos = tables.Column(verbose_name='NUM. DOSSIER')
    conformite = tables.Column(verbose_name='DECISION DU LABORATOIRE',attrs={"td": {"bgcolor": "green"}})

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
                    'produit',
                    'conformite']
        exclude = ['idcargaison', 'etatInspection','valeurfacture', 'frontiere', 'origine', 'rapechctrl', 'requisitionack',
                   'typeunitetransport', 'volume15', 'volume', 'volume20', 'tonnagevide', 'tonnageair',
                   'dateheurecargaison', 'entrepot','declaration',
                   'requisitiondackdate', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact',
                   'tampon', 'printactdate', 'l_control', 'before', 'after', 'controlOrganoleptique']


class EnAttenteInspection(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="DATE ENT.")
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    numreq = tables.Column(verbose_name='REF.REQ.')
    numdos = tables.Column(verbose_name='NUM.DOSSIER')
    idcargaison = tables.Column(verbose_name='N.ENR.')
    declaration = tables.Column(verbose_name='N.DECL.')
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"


class CargaisonDechargement2(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
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
                   'tampon', 'printactdate', 'l_control', 'before', 'after']


class TankerCabotteur(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE4, verbose_name='')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
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
                   'dateheurecargaison', 'before', 'after',
                   'requisitiondackdate', 'numreq', 'voie', 'provenance', 'poids',
                   'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
                   'tampon', 'printactdate', 'l_control', 'entrepot']


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


class RapportInspectionCamion(tables.Table):
    nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    declaration = tables.Column(verbose_name='N.DECL.')
    dateheurecargaison = tables.Column(verbose_name="DATE ENTR.")
    requisitiondackdate = tables.Column(verbose_name="DATE REQ.")
    dateechantillonage = tables.Column(verbose_name='DATE ECH.')
    dateinspection = tables.Column(verbose_name="DATE D'INSPECTION")
    datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO')
    dateanalyse = tables.Column(verbose_name='DATE ANALYSE')
    # dateDech = tables.Column(verbose_name="DATE DECH.")
    volConst = tables.Column(verbose_name='GOV')
    gsvT = tables.Column(verbose_name='GSV')
    actions = tables.TemplateColumn(TEMPLATE5, verbose_name='')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"


class RapportInspectionTanker(tables.Table):
    nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    produit = tables.Column(verbose_name='PRODUIT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    dateheurecargaison = tables.Column(verbose_name="DATE ENTR.")
    dateechantillonage = tables.Column(verbose_name='DATE ECH.')
    dateinspection = tables.Column(verbose_name="DATE D'INSPECTION")
    dateReceptionLabo = tables.Column(verbose_name='DATE REC.LABO')
    dateAnalyse = tables.Column(verbose_name='DATE ANALYSE')
    dateDech = tables.Column(verbose_name="DATE DECH.")
    GOV = tables.Column(verbose_name='GOV')
    MTA = tables.Column(verbose_name='MTA')
    MTV = tables.Column(verbose_name='MTV')
    VCF = tables.Column(verbose_name='VCF')
    GSV = tables.Column(verbose_name='GSV')
    actions = tables.TemplateColumn(TEMPLATE5, verbose_name='')


    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"

class NonConformeOrganoleptique(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.")
    idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")
    idcargaison__produit = tables.Column(verbose_name="PRODUIT DECL.")
    natureProduitEntrepot = tables.Column(verbose_name="PRODUIT CONST. ENTREPOT", attrs={"td": {"bgcolor": "red"}})
    natureProduitLabo = tables.Column(verbose_name="PRODUIT CONST. LABORATOIRE", attrs={"td": {"bgcolor": "green"}})
    action = tables.TemplateColumn(A, verbose_name='')


    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"



class NonConformeLaboratoire(tables.Table):
    idcargaison__numdos = tables.Column(verbose_name="#.DOS")
    idcargaison__declaration = tables.Column(verbose_name="#.DECL.")
    idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__entrepot = tables.Column(verbose_name="ENTREPOT")
    idcargaison__produit = tables.Column(verbose_name="PRODUIT")
    idcargaison__immatriculation = tables.Column(verbose_name="IMMAT.")

    # volume = tables.Column(verbose_name="VOLUME DECL.")
    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id": "example2"
        }
        template_name = "django_tables2/bootstrap4.html"

