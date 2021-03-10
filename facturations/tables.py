import django_tables2 as tables
from enreg.models import Cargaison, Paiement, Liquidation

TEMPLATE = """
 <button type="button" class="btn btn-warning"  data-id={{record.pk}} data-toggle="modal" data-target="#modal-default">
                  Paiement
                  </button>
"""

TEMPLATE1 = """
 <a href="{%url 'detailsappuration' record.pk%}" class="btn btn-warning">Details</a>
"""

TEMPLATE2 = """
 <a href="{%url 'saisiebl' record.pk%}" class="btn btn-danger">Correction</a>
"""

class Facturations(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE,verbose_name='')
    volume = tables.Column(verbose_name='Vol. Déclaré')
    gsv = tables.Column(verbose_name='GSV')
    datedechargement = tables.Column(verbose_name='Date Déchargement')
    dateheurecargaison = tables.Column(verbose_name="Date d'Entrée")
    frontiere = tables.Column(verbose_name='Frontière')

    class Meta:
        attrs = {
            "class": "table table-hover text-nowrap table-striped",
            "id":"facturations"
        }
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['actions','dateheurecargaison','frontiere','importateur','entrepot','declarant','immatriculation','t1e','t1d','produit','fournisseur','volume','datedechargement','gsv']
        exclude = ['idcargaison','numbtfh','manifestdgda','l_control','tempcargaison','voie','densitecargaison','provenance','numdeclaration','idchauffeur','valeurfacture','poids','nationalite', 'nomchauffeur','etat','volume_decl15','numdossier','user','codecargaison','transporteur','qrcode','impression','numact','conformite','tampon','printactdate']


class Facturations1(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE,verbose_name='')
    datebl = tables.Column(verbose_name='Date BL')
    codebureau = tables.Column(verbose_name='Code BUR')
    numerobl = tables.Column(verbose_name='# BL')
    vol_liq = tables.Column(verbose_name='Vol. Liquidé')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['datebl','codebureau','numerobl','vol_liq','importateur','declarant','immatriculation','entrepot']
        exclude = ['dateheurecargaison','idcargaison','l_control','valeurfacture','numbtfh','manifestdgda','t1e','t1d','numdeclaration','frontiere','produit','fournisseur','volume','tempcargaison','voie','densitecargaison','provenance','idchauffeur','poids','nationalite', 'nomchauffeur','etat','volume_decl15','numdossier','user','codecargaison','transporteur','qrcode','impression','numact','conformite','tampon','printactdate']


class Appuration(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    importateur = tables.Column(accessor='idcargaison.importateur')
    declarant = tables.Column(accessor='idcargaison.declarant')
    immatriculation = tables.Column(accessor='idcargaison.immatriculation')
    entrepot = tables.Column(accessor='idcargaison.entrepot_id')
    numbtfh = tables.Column(accessor='idcargaison.numbtfh')
    manifestdgda = tables.Column(accessor='idcargaison.manifestdgda')
    t1e = tables.Column(accessor='idcargaison.t1e')
    t1d = tables.Column(accessor='idcargaison.t1d')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Liquidation
        sequence = ['datebl','numerobl','vol_liq','importateur','declarant','entrepot','immatriculation','manifestdgda','t1e','t1d']
        exclude = ['idliquidation', 'idcargaison','vol_liquide','vol_liquide','numbtfh','type_appurement']


class Detailsappuration(tables.Table):
    # actions = tables.TemplateColumn(TEMPLATE2, verbose_name='')
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Paiement
        sequence = ['code_bur','importateur','nom_decl','n_liq','date_liq','date_pay','mont_enc','bnk_nam','ref_pay','taux','qte_stat']
        exclude = ['nif_importateur','tax_cod','id','bureau','ide_ser','libelle']


class Liquidat(tables.Table):
    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Liquidation

