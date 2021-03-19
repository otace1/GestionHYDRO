import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from enreg.models import Entrepot, Importateur, Ville, Produit, Dechargement, Cargaison, LaboReception, Resultat,Liquidation, Paiement

TEMPLATE = """
<a href="{%url 'edit_entrepot' record.pk%}" aria-hidden="true"> Modifier  |</a>
<a href="{%url 'del_entrepot' record.pk%}" aria-hidden="true"> |  Effacer</a> 
 """

TEMPLATE1 = """
<a href="{%url 'edit_importateur' record.pk%}" aria-hidden="true"> Modifier  |</a>
<a href="{%url 'del_importateur' record.pk%}" aria-hidden="true"> |  Effacer</a> 
 """

TEMPLATE2 = """
<a href="{%url 'edit_frontiere' record.pk%}"aria-hidden="true"> Modifier |</a> 
<a href="{%url 'del_frontiere' record.pk%}"aria-hidden="true">| Effacer</a> 
 """

TEMPLATE3 = """
<a href="{%url 'edit_produit' record.pk%}" aria-hidden="true"> Modifier |</a> 
<a href="{%url 'del_produit' record.pk%}"  aria-hidden="true">| Effacer</a> 
 """


class EntrepotTable(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE)
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Entrepot
        sequence = ['identrepot', 'nomentrepot', 'adresseentrepot']


class ImportateurTable(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1)
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Importateur
        sequence = ['idimportateur', 'nomimportateur', 'adresseimportateur']


class VilleTable(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE2)
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Ville
        sequence = ['idville', 'nomville', 'province']


class ProduitTable(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE3)
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Produit
        sequence = ['idproduit', 'nomproduit']


class StatistiquesTable(tables.Table):
    export_formats = ['csv', 'xls', 'xlsx']
    dateheurecargaison = tables.Column(verbose_name='Date & Heure')
    volume = tables.Column(verbose_name='Vol. Décl.')
    densitecargaison = tables.Column(verbose_name='Dens.')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'fournisseur', 'importateur', 'frontiere', 'entrepot', 'produit', 'volume',
                    'poids', 'immatriculation', 't1e', 't1d', 'numbtfh', 'numdeclaration', 'manifestdgda']
        exclude = ['idcargaison', 'tempcargaison', 'volume_decl15', 'voie', 'provenance', 'datereceptionlabo',
                   'dateanalyse', 'numcertificatqualite', 'valeurfacture',
                   'transporteur', 'declarant', 'idchauffeur', 'densitecargaison', 'nationalite', 'nomchauffeur',
                   'qrcode', 'impression', 'etat', 'user', 'tampon', 'conformite', 'printactdate', 'densite15',
                   'temperature', 'codecargaison', 'numdossier', 'numact', 'datedechargement', 'gov', 'gsv',
                   'l_control']


class DerniersEnregistrements(tables.Table):
    dateheurecargaison = tables.Column(verbose_name='Date & Heure')
    volume = tables.Column(verbose_name='Vol. Décl.')
    importateur = tables.Column(verbose_name='Import.')
    class Meta:
        model = Cargaison
        sequence = ['dateheurecargaison','frontiere','importateur','produit','volume']
        exclude = ['idcargaison', 'tempcargaison', 'volume_decl15', 'voie', 'provenance', 'datereceptionlabo', 'poids','immatriculation','valeurfacture','numbtfh','numdeclaration','manifestdgda','t1e', 't1d',
                   'dateanalyse', 'numcertificatqualite','fournisseur', 'entrepot',
                   'transporteur', 'declarant', 'idchauffeur', 'densitecargaison', 'nationalite', 'nomchauffeur',
                   'qrcode', 'impression', 'etat', 'user', 'tampon', 'conformite', 'printactdate', 'densite15',
                   'temperature', 'codecargaison', 'numdossier', 'numact', 'datedechargement', 'gov', 'gsv','l_control']


class ProductionTable(tables.Table):
    export_formats = ['csv', 'xls', 'xlsx']
    dateheurecargaison = tables.Column(accessor='idcargaison.idcargaison.idcargaison.idcargaison.dateheurecargaison', verbose_name='Date')
    importateur = tables.Column(accessor='idcargaison.idcargaison.idcargaison.idcargaison.importateur',verbose_name='Importateur')
    entrepot = tables.Column(accessor='idcargaison.idcargaison.idcargaison.idcargaison.entrepot', verbose_name='Entrepot')
    declarant = tables.Column(accessor='idcargaison.idcargaison.idcargaison.idcargaison.declarant', verbose_name='Declarant')
    immatriculation = tables.Column(accessor='idcargaison.idcargaison.idcargaison.idcargaison.immatriculation', verbose_name='Immatriculation')
    produit = tables.Column(accessor='idcargaison.idcargaison.idcargaison.idcargaison.produit', verbose_name='Produit')
    volume = tables.Column(accessor='idcargaison.idcargaison.idcargaison.idcargaison.volume',verbose_name='Vol. Decl.')
    gov = tables.Column(verbose_name='GOV')
    gsv = tables.Column(verbose_name='GSV')
    cgwprod = tables.Column(verbose_name='Prod. Attendu CGW')
    occprod = tables.Column(verbose_name='Prod. Attendu OCC')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Dechargement
        sequence = ['dateheurecargaison','importateur', 'entrepot', 'declarant', 'immatriculation', 'produit', 'volume', 'gov', 'gsv','cgwprod','occprod']
        exclude = ['datedechargement', 'idcargaison', 'temperature', 'mta', 'mtv', 'densite15']


class EncaissementTable(tables.Table):
    export_formats = ['csv', 'xls', 'xlsx']
    nomimportateur = tables.Column(verbose_name='Importateur')
    nom_decl = tables.Column(verbose_name='Declarant')
    numerobl = tables.Column(verbose_name='Num.BL')
    datebl = tables.Column(verbose_name='datebl')
    date_pay = tables.Column(verbose_name='date_pay')
    mont_enc = tables.Column(verbose_name='montant_enc')
    qte_stat = tables.Column(verbose_name='Vol_Paye')
    bnk_nam = tables.Column(verbose_name='Banque')
    codebureau = tables.Column(verbose_name='Cod_BUR')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Liquidation
        sequence = ['codebureau','nomimportateur','nom_decl','numerobl','datebl','date_pay','mont_enc','qte_stat','bnk_nam']
        exclude = ['idliquidation','idcargaison_id','vol_liq','type_appurement','idcargaison']

