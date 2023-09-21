import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from enreg.models import Entrepot, Importateur, Ville, Produit, Dechargement, Cargaison, LaboReception, Resultat,Liquidation, Paiement

TEMPLATE = """
<a href="{%url 'edit_entrepot' record.pk%}" class="btn btn-success">Modifier</a>
<a href="{%url 'del_entrepot' record.pk%}" class="btn btn-danger">Effacer</a> 
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
    identrepot = tables.Column(verbose_name='ID')
    nomentrepot = tables.Column(verbose_name='NOM ENTREPOT')
    adresseentrepot = tables.Column(verbose_name='ADRESSE PHYSIQUE')
    ville = tables.Column(verbose_name='VILLE')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Entrepot
        sequence = ['identrepot', 'nomentrepot', 'adresseentrepot', 'ville']


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
    export_formats = ['csv', 'xlsx', 'xls']
    dateheurecargaison = tables.Column(verbose_name='DATE')
    frontiere_id__nomville = tables.Column(verbose_name='FRONTIERE')
    importateur_id__nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    produit_id__nomproduit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOL.DECL')
    densitecargaison = tables.Column(verbose_name='DENSIT')
    entrepot_id__nomentrepot = tables.Column(verbose_name='ENTREPOT')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }

    # model = Cargaison
    # sequence = ['dateheurecargaison', 'importateur', 'entrepot', 'immatriculation', 'produit', 'volume']
    # exclude = ['dateHeureAnalyseLabo', 'idcargaison', 'etatInspection', 'valeurfacture', 'frontiere', 'origine',
    #            'rapechctrl', 'requisitionack',
    #            'typeunitetransport', 'controlOrganoleptique', 'dateDechargement', 'volume15',
    #            'volume20', 'tonnagevide', 'toBeRefouler', 'toBeConsignated', 'isConsignated', 'isRefouler',
    #            'tonnageair', 'transitaire',
    #            'requisitiondackdate', 'numdos', 'numreq', 'voie', 'provenance', 'poids',
    #            'etat', 'numdossier', 'user', 'codecargaison', 'qrcode', 'impression', 'numact', 'conformite',
    #            'tampon', 'printactdate', 'l_control', 'before', 'after', 'declaration']



class StatistiquesJour(tables.Table):
    export_formats = ['csv', 'xlsx', 'xls']
    dateheurecargaison = tables.Column(verbose_name='Date & Heure')
    volume = tables.Column(verbose_name='Vol. Décl.')
    densitecargaison = tables.Column(verbose_name='Dens.')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Cargaison
        sequence = ['dateheurecargaison', 'fournisseur', 'importateur', 'frontiere', 'entrepot', 'produit', 'volume',
                    'immatriculation', 't1e', 't1d', 'numbtfh', 'numdeclaration', 'manifestdgda']
        exclude = ['idcargaison', 'tempcargaison', 'volume_decl15', 'voie', 'provenance', 'datereceptionlabo',
                   'dateanalyse', 'numcertificatqualite', 'valeurfacture',
                   'transporteur', 'declarant', 'idchauffeur', 'densitecargaison', 'nationalite', 'nomchauffeur',
                   'qrcode', 'impression', 'etat', 'user', 'tampon', 'conformite', 'printactdate', 'densite15',
                   'temperature', 'codecargaison', 'numdossier', 'numact', 'datedechargement', 'gov', 'gsv',
                   'l_control', 'poids']


class DerniersEnregistrements(tables.Table):
    dateheurecargaison = tables.Column(verbose_name='DATE & HEURE')
    frontiere = tables.Column(verbose_name='FRONTIERE')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot = tables.Column(verbose_name='ENTREPOT')
    produit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOL.DECL.')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"




class ProductionTable(tables.Table):
    export_formats = ['csv', 'xlsx', 'xls']
    idcargaison__idcargaison__idcargaison__idcargaison__dateheurecargaison = tables.Column(verbose_name='Date')
    idcargaison__idcargaison__idcargaison__idcargaison__importateur__nomimportateur = tables.Column(
        verbose_name='Importateur')
    idcargaison__idcargaison__idcargaison__idcargaison__entrepot__nomentrepot = tables.Column(verbose_name='Entrepot')
    idcargaison__idcargaison__idcargaison__idcargaison__declarant = tables.Column(verbose_name='Declarant')
    idcargaison__idcargaison__idcargaison__idcargaison__immatriculation = tables.Column(verbose_name='Immatriculation')
    idcargaison__idcargaison__idcargaison__idcargaison__produit__nomproduit = tables.Column(verbose_name='Produit')
    idcargaison__idcargaison__idcargaison__idcargaison__volume = tables.Column(verbose_name='Vol. Decl.')
    gov = tables.Column(verbose_name='GOV')
    gsv = tables.Column(verbose_name='GSV')
    cgwprod = tables.Column(verbose_name='Prod. Attendu CGW')
    occprod = tables.Column(verbose_name='Prod. Attendu OCC')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Dechargement
        sequence = ['idcargaison__idcargaison__idcargaison__idcargaison__dateheurecargaison',
                    'idcargaison__idcargaison__idcargaison__idcargaison__importateur__nomimportateur',
                    'idcargaison__idcargaison__idcargaison__idcargaison__entrepot__nomentrepot',
                    'idcargaison__idcargaison__idcargaison__idcargaison__declarant',
                    'idcargaison__idcargaison__idcargaison__idcargaison__immatriculation',
                    'idcargaison__idcargaison__idcargaison__idcargaison__produit__nomproduit',
                    'idcargaison__idcargaison__idcargaison__idcargaison__volume', 'gov', 'gsv', 'cgwprod', 'occprod']
        exclude = ['datedechargement', 'idcargaison', 'temperature', 'mta', 'mtv', 'densite15']


class EncaissementTable(tables.Table):
    export_formats = ['csv', 'xlsx', 'xls']
    nomimportateur = tables.Column(verbose_name='Importateur')
    nif_importateur = tables.Column(verbose_name='NIF')
    # nom_decl = tables.Column(verbose_name='Déclarant')
    date_e = tables.Column(verbose_name="Date d'Entrée")
    immatriculation = tables.Column(verbose_name='Immatr.')
    # bureau = tables.Column(verbose_name='Bureau')
    # modele = tables.Column(verbose_name='Modèle')
    numerobl = tables.Column(verbose_name='Num.BL')
    datebl = tables.Column(verbose_name='Date BL')
    ide_nbr = tables.Column(verbose_name='N.Quitt.')
    date_pay = tables.Column(verbose_name='Date Paiement')
    cgw_p = tables.Column(verbose_name='Q.CGW')
    occ_q = tables.Column(verbose_name='Q.OCC')
    libelle = tables.Column(verbose_name='Libellé')
    ref_pay = tables.Column(verbose_name='Ref.Paiement')
    qte_stat = tables.Column(verbose_name='Vol.Payé')
    bnk_nam = tables.Column(verbose_name='Banque')
    gsv = tables.Column(verbose_name='Vol.GSV')
    # diff = tables.Column(verbose_name='Diff.Vol')
    codebureau = tables.Column(verbose_name='Cod.BUR')

    class Meta:
        attrs = {"id": "myTable"}
        template_name = "django_tables2/bootstrap4.html"
        model = Liquidation
        sequence = ['codebureau', 'nomimportateur', 'nif_importateur', 'date_e',
                    'immatriculation', 'numerobl', 'datebl', 'ide_nbr', 'date_pay', 'bnk_nam',
                    'ref_pay', 'gsv', 'qte_stat', 'cgw_p', 'occ_q']
        exclude = ['idliquidation', 'idcargaison_id', 'vol_liq', 'type_appurement', 'idcargaison', 'taux', 'libelle']


class SyntheseImportation(tables.Table):
    importateur__nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    nombredecl = tables.Column(verbose_name="Nbr. CAMION(S)")
    mogas = tables.Column(verbose_name="VOL. MOGAS DECL.")
    gasoil = tables.Column(verbose_name="VOL. GASOIL DECL.")
    jet = tables.Column(verbose_name="VOL. JETA1 DECL.")
    petrole = tables.Column(verbose_name="VOL. PETROLE DECL.")
    total = tables.Column(verbose_name="TOTAL VOL. DECL.")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # model = Cargaison
        # sequence = ['importateur__nomimportateur', 'nombredecl', 'mogas', 'gasoil', 'jet', 'petrole', 'total']
        # exclude = ['idcargaison', 'tempcargaison', 'volume_decl15', 'voie', 'provenance', 'datereceptionlabo', 'poids',
        #            'immatriculation', 'valeurfacture', 'numbtfh', 'numdeclaration', 'manifestdgda', 't1e', 't1d',
        #            'dateanalyse', 'numcertificatqualite', 'fournisseur', 'entrepot',
        #            'transporteur', 'declarant', 'idchauffeur', 'densitecargaison', 'nationalite', 'nomchauffeur',
        #            'qrcode', 'impression', 'etat', 'user', 'tampon', 'conformite', 'printactdate', 'densite15',
        #            'temperature', 'codecargaison', 'numdossier', 'numact', 'datedechargement', 'gov', 'gsv',
        #            'l_control', 'dateheurecargaison', 'frontiere', 'importateur', 'produit', 'volume']


class SyntheseProduction(tables.Table):
    export_formats = ['csv', 'xlsx', 'xls']
    idinspection__idcargaison__importateur__nomimportateur = tables.Column(
        verbose_name='FOURNISSEUR')
    gasoilGOV = tables.Column(verbose_name='GOV GASOIL')
    mogasGOV = tables.Column(verbose_name='GOV MOGAS')
    jetGOV = tables.Column(verbose_name='GOV JETA1')
    petroleGOV = tables.Column(verbose_name='GOV PETROLE')
    gasoilGSV = tables.Column(verbose_name='GSV GASOIL')
    mogasGSV = tables.Column(verbose_name='GSV MOGAS')
    jetGSV = tables.Column(verbose_name='GSV JETA1')
    petroleGSV = tables.Column(verbose_name='GSV PETROLE')
    gsvtotal = tables.Column(verbose_name='TOTAL GSV')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # sequence = ['idcargaison__idcargaison__idcargaison__idcargaison__importateur__nomimportateur', 'gasoilGOV',
        #             'mogasGOV', 'jetGOV', 'petroleGOV', 'gasoilGSV', 'mogasGSV', 'jetGSV', 'petroleGSV', 'gsvtotal']
        # exclude = ['datedechargement', 'idcargaison', 'temperature', 'mta', 'mtv', 'densite15', 'gov', 'gsv']


class SyntheseEncaissement(tables.Table):
    export_formats = ['csv', 'xlsx', 'xls']
    nomimportateur = tables.Column(verbose_name='Importateur')
    total_vol_decharge = tables.Column(verbose_name='Total GSV Decharge')
    total_vol_paye = tables.Column(verbose_name='Total Volume Paye')
    cgw_p = tables.Column(verbose_name='Quote Part CGW Encaissee')
    occ_q = tables.Column(verbose_name='Quote Part OCC Encaissee')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Dechargement
        sequence = ['nomimportateur', 'total_vol_decharge', 'total_vol_paye', 'cgw_p', 'occ_q']
        exclude = ['datedechargement', 'idcargaison', 'temperature', 'mta', 'mtv', 'densite15', 'gov', 'gsv']



class RapportBrut(tables.Table):
    dateheurecargaison__date = tables.Column(verbose_name="DATE ENTREE")
    frontiere__nomville = tables.Column(verbose_name="FRONTIERE")
    declaration = tables.Column(verbose_name='DECL.#T1D')
    importateur__nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot__nomentrepot = tables.Column(verbose_name='ENTREPOT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    produit__nomproduit = tables.Column(verbose_name='PRODUIT')
    requisitiondackdate__date = tables.Column(verbose_name='DATE REQ.')
    entrepot_echantillon__dateechantillonage__date = tables.Column(verbose_name='DATE ECH.')
    entrepot_echantillon__laboreception__datereceptionlabo__date = tables.Column(verbose_name='DATE REC.LABO')
    impressionresultat__printDate = tables.Column(verbose_name='DATE ANALYSE')
    inspection__dateinspection__date = tables.Column(verbose_name="DATE INSPEC.")
    entrepot__cargaison__dateDechargement = tables.Column(verbose_name='DATE DECH.')
    volume = tables.Column(verbose_name='VOL. DECL.')
    volJauge = tables.Column(verbose_name='VOL. JAUGE')
    inspection__dens = tables.Column(verbose_name='DENS.15')
    inspection__temp = tables.Column(verbose_name='TEMP.')
    vcf = tables.Column(verbose_name='VCF')
    mta = tables.Column(verbose_name='MTA')
    mtv = tables.Column(verbose_name='MTV')
    gsvJauge = tables.Column(verbose_name='GSV')
    gsvMeter = tables.Column(verbose_name='GSV (METER)')
    fraisOcc = tables.Column(verbose_name='FRAIS A PAYER')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            # "id": "example1"
        }
        template_name = "django_tables2/bootstrap5-responsive.html"




class RapportBrutJournalier(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="DATE ENT.")
    frontiere__nomville = tables.Column(verbose_name="FRONTIERE D'ENT.")
    declaration = tables.Column(verbose_name='N.T1E')
    importateur__nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot__nomentrepot = tables.Column(verbose_name='ENTREPOT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    produit__nomproduit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOL. DECL.')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }



class RapportBrutJournalierEchantillonnage(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="DATE ENT.")
    frontiere = tables.Column(verbose_name="FRONTIERE D'ENT.")
    declaration = tables.Column(verbose_name='N.T1E')
    importateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot = tables.Column(verbose_name='ENTREPOT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    produit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOL. DECL.')
    requisitiondackdate = tables.Column(verbose_name='DATE REQUISITION')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }


class RapportBrutJournalierAnalyse(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="DATE ENT.")
    frontiere__nomville = tables.Column(verbose_name="FRONTIERE D'ENT.")
    declaration = tables.Column(verbose_name='N.T1E')
    importateur__nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot__nomentrepot = tables.Column(verbose_name='ENTREPOT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    produit__nomproduit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOL. DECL.')
    requisitiondackdate = tables.Column(verbose_name='DATE REQUISITION')
    entrepot_echantillon__dateechantillonage = tables.Column(verbose_name='DATE ECHANTILLONNAGE')
    entrepot_echantillon__laboreception__datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }


class RapportBrutJournalierInspection(tables.Table):
    dateheurecargaison = tables.Column(verbose_name="DATE ENT.")
    frontiere__nomville = tables.Column(verbose_name="FRONTIERE D'ENT.")
    declaration = tables.Column(verbose_name='N.T1E')
    importateur__nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    entrepot__nomentrepot = tables.Column(verbose_name='ENTREPOT')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    produit__nomproduit = tables.Column(verbose_name='PRODUIT')
    volume = tables.Column(verbose_name='VOL. DECL.')
    requisitiondackdate = tables.Column(verbose_name='DATE REQUISITION')
    entrepot_echantillon__dateechantillonage = tables.Column(verbose_name='DATE ECHANTILLONNAGE')
    entrepot_echantillon__laboreception__datereceptionlabo = tables.Column(verbose_name='DATE REC.LABO')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }


