import django_tables2 as tables
from enreg.models import Cargaison, Entrepot_echantillon, LaboReception, Resultat

# TEMPLATE = """
#             <a href="{%url 'reception' record.pk%}" class="btn btn-success">RECEPTION</a>
#            """

TEMPLATE = """ 
            <button type="button" onclick="getRowId(this)" id="data" class="btn btn-success">
                  ACK
                </button>
           """


date = """
 <form method=post action="{% url 'codecq' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numcertificatqualite">
 </form>

"""

rapport = """
 <form method=post action="{% url 'codecq' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numcertificatqualite">
 </form>

"""

date = """
 <form method=post action="{% url 'codecq' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numcertificatqualite">
 </form>

"""

numerore = """
 <form method=post action="{% url 'codecq' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numcertificatqualite">
 </form>

"""


TEMPLATE1 = """
<button type="button" class="btn btn-default" data-toggle="modal" data-target="#modal-default">
                  SAISIE
</button>
            """


TEMPLATE2 = """
<a class="btn btn-primary" href="{%url 'mogasr' record.pk%}" role="button">MOGAS</a>
<a class="btn btn-primary" href="{%url 'gasoilr' record.pk%}" role="button">GASOIL</a>
<a class="btn btn-primary" href="{%url 'jeta1r' record.pk%}" role="button">JET A1</a>
<a class="btn btn-primary" href="{%url 'petroler' record.pk%}" role="button">PETROLE</a>
            """


VALIDATION1 = """
<a href="{%url 'affichageDetailsResultats' record.pk%}" class="btn btn-warning">AFFICHER</a>
<a class="btn btn-success" href="{% url 'conforme' %}" role="button">>> CONFORME >> </a>
<a class="btn btn-danger" href="{% url 'nonconforme' %}" role="button">>> NON CONFORME >> </a>
<a class="btn btn-outline-danger" href="{% url 'refaire' %}" role="button">>> A REFAIRE >> </a>
"""

CQ = """
 <form method=post action="{% url 'codecq' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numcertificatqualite">
 </form>
 
"""

VALIDATION2 = """
<a href="{%url 'affichageDetailsResultatsDroite' record.pk%}" class="btn btn-warning">AFFICHER</a>
"""


IMPRESSION = """
    <a href="{%url 'print' record.pk%}" class="btn btn-info">PRINT</a>
    """

REIMPRESSION = """
    <a href="{%url 'reprint' record.pk%}" class="btn btn-info">Impression</a>
    """

IMPRESSION1 = """   <a href="{%url 'fiche' record.pk%}" class="btn btn-info">Fiche Résultat</a>
             """

GO = """
    <a href="{%url 'conforme2' record.pk%}" class="btn btn-success">Conforme</a>
    <a href="{%url 'nonconforme2' record.pk%}" class="btn btn-danger">Non Conforme</a>
             """

class LaboratoireReception(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE, verbose_name='ACTIONS')
    idcargaison__dateheurecargaison = tables.Column(verbose_name="DATE D'ENTREE")
    dateechantillonage = tables.Column(verbose_name="DATE D'ECHANTILLONNAGE")
    idcargaison__entrepot = tables.Column(verbose_name='ENTREPOT')
    idcargaison__produit = tables.Column(verbose_name="NATURE PRODUIT")
    idcargaison__immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    idcargaison__numdos = tables.Column(verbose_name="NUM. DOSSIER")
    # idcargaison__codecargaison = tables.Column(verbose_name='# Hydro')
    numrappechauto = tables.Column(verbose_name="RAPPORT D'ECHANTILLONNAGE")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        row_attrs = {
            "id": lambda record: record.pk
        }
        # template_name = "django_tables2/bootstrap4.html"
        model = Entrepot_echantillon
        sequence = ['idcargaison__dateheurecargaison','dateechantillonage','idcargaison__entrepot','idcargaison__immatriculation','idcargaison__produit','numrappechauto', 'idcargaison__numdos',
                    ]
        exclude = ['numplombh', 'numplombb', 'numplombbr', 'numplombaph', 'etatphysique', 'numdossier',
                   'idcargaison__codecargaison', 'numrappech', 'useredit', 'matricule', 'methodeutilisee',
                   'qte', 'conformite', 'idcargaison__produit__nomproduit', 'idcargaison', 'natureProduitEntrepot',
                   'nonConformiteProduit']


class TableauEchantillonRecu(tables.Table):
    # actions = tables.TemplateColumn(RECEPTIONNER, verbose_name='')
    datereceptionlabo = tables.Column(verbose_name="Date de réception")
    idcargaison__idcargaison__immatriculation = tables.Column(verbose_name='Immatriculation')
    idcargaison__idcargaison__numdos = tables.Column(verbose_name="Numéro Dossier")
    idcargaison__codecargaison = tables.Column(verbose_name='# Hydro')
    idcargaison__produit__nomproduit = tables.Column(verbose_name='Produit')
    idcargaison__numrappech = tables.Column(verbose_name='# RE')
    codelabo = tables.Column(verbose_name="Code Labo")
    numcertificatqualite = tables.Column(verbose_name="Numéro CQ Attribué")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        # template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['datereceptionlabo', 'idcargaison__numrappech', 'idcargaison__idcargaison__numdos',
                    'idcargaison__idcargaison__immatriculation', 'codelabo', 'numcertificatqualite']
        exclude = ['numplombh', 'numplombb', 'numplombbr', 'numplombaph', 'etatphysique', 'idcargaison__numrappech',
                   'qte', 'conformite', 'idcargaison__produit__nomproduit', 'idcargaison', 'idcargaison__codecargaison']


class AffichageAnalyse(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='ACTIONS')
    numrappechauto = tables.Column(accessor='idcargaison.numrappechauto', verbose_name="NUM.RE")
    codelabo = tables.Column(verbose_name='CODE LABO')
    produit = tables.Column(accessor='idcargaison.idcargaison.produit', verbose_name='NATURE PRODUIT.')
    datereceptionlabo = tables.Column(verbose_name='DATE RECEPT.')
    # natureProduitLabo = tables.Column(verbose_name='Produit CONST.')
    numcertificatqualite = tables.Column(verbose_name='NUM.CQ')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        model = LaboReception
        sequence = ['datereceptionlabo', 'codelabo', 'numrappechauto', 'produit']
        exclude = ['numcertificatqualite', 'idcargaison']


class AffichageAnalyseRefaire(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='ACTIONS')
    numrappechauto = tables.Column(accessor='idcargaison.numrappechauto', verbose_name="NUM.RE")
    codelabo = tables.Column(verbose_name='CODE LABO')
    produit = tables.Column(accessor='idcargaison.idcargaison.produit', verbose_name='NATURE PRODUIT.')
    datereceptionlabo = tables.Column(verbose_name='DATE RECEPT.')
    numcertificatqualite = tables.Column(verbose_name='NUM.CQ')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example2"
        }
        model = LaboReception
        sequence = ['datereceptionlabo', 'codelabo', 'numrappechauto', 'produit']
        exclude = ['numcertificatqualite', 'idcargaison']


class AffichageValidation1(tables.Table):
    actions = tables.TemplateColumn(VALIDATION1, verbose_name='ACTIONS')
    # certificat = tables.TemplateColumn(CQ, verbose_name='C.Q')
    datereceptionlabo = tables.Column(verbose_name='DATE REC.')
    codelabo = tables.Column(verbose_name="CODE LABO")
    numcertificatqualite = tables.Column(verbose_name="NUM.CQ")
    idcargaison__idcargaison__produit__nomproduit = tables.Column(verbose_name="PRODUIT")
    idcargaison__idcargaison__entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        model = LaboReception
        sequence = ['datereceptionlabo', 'codelabo', 'numcertificatqualite',
                    'idcargaison__idcargaison__produit__nomproduit', 'idcargaison__idcargaison__entrepot__nomentrepot'
                    ]
        exclude = ['idcargaison', 'idcargaison__numrappechauto']


class AffichageVal1(tables.Table):
    nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    nomproduit = tables.Column(verbose_name='PRODUIT')
    codelabo = tables.Column(verbose_name='CODE LABO')
    numcertificatqualite = tables.Column(verbose_name='NUM.CQ')

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"


class DetailsAnalyse(tables.Table):
    nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    nomproduit = tables.Column(verbose_name='PRODUIT')
    codelabo = tables.Column(verbose_name='CODE LABO')
    numcertificatqualite = tables.Column(verbose_name='NUM.CQ')
    nomParametre = tables.Column(verbose_name='PARAM.')
    valeurResultat = tables.Column(verbose_name='VALEUR')
    etatValeur = tables.Column(verbose_name='')

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"




class AffichageValidation2(tables.Table):
    actions = tables.TemplateColumn(VALIDATION2, verbose_name='ACTIONS')
    datereceptionlabo = tables.Column(verbose_name='DATE REC.')
    codelabo = tables.Column(verbose_name="CODE LABO")
    numcertificatqualite = tables.Column(verbose_name="NUM.CQ")
    idcargaison__idcargaison__produit__nomproduit = tables.Column(verbose_name="PRODUIT")
    idcargaison__idcargaison__entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }
        model = LaboReception
        sequence = ['datereceptionlabo','codelabo','numcertificatqualite','idcargaison__idcargaison__produit__nomproduit','idcargaison__idcargaison__entrepot__nomentrepot'
                    ]
        exclude = ['idcargaison','idcargaison__numrappechauto']


class AffichageValidation2Go(tables.Table):
    actions = tables.TemplateColumn(GO, verbose_name='ACTIONS')
    numrappech = tables.Column(accessor='idcargaison.numrappech', verbose_name='Numéro RE')
    codelabo = tables.Column(accessor='codelabo')
    numcertificatqualite = tables.Column(accessor='numcertificatqualite', verbose_name='Numéro CQ')
    produit = tables.Column(accessor='idcargaison.idcargaison.produit')
    importateur = tables.Column(accessor='idcargaison.idcargaison.importateur')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Resultat
        sequence = ['dateanalyse', 'importateur', 'produit', 'numrappech', 'codelabo', 'numcertificatqualite']
        exclude = ['idcargaison', 'aspect', 'odeur', 'couleursaybolt', 'couleurastm', 'aciditetotal', 'soufre',
                   'soufremercaptan',
                   'docteurtest', 'massevolumique', 'aromatique', 'distillation', 'distillation10',
                   'distillation20', 'distillation50',
                   'distillation90', 'pointinitial', 'pointfinal', 'pointeclair', 'pointfumee', 'freezingpoint',
                   'residu', 'perte',
                   'viscosite', 'pointinflammabilite', 'pointecoulement', 'teneureau', 'sediment', 'corrosion',
                   'conductivite',
                   'pourcent10', 'pourcent20', 'pourcent50', 'pourcent70', 'pourcent90', 'difftemperature',
                   'tensionvapeur', 'plomb', 'indiceoctane',
                   'vol10', 'vol20', 'vol30', 'vol40', 'vol50', 'vol60', 'vol70', 'vol80', 'vol90',
                   'indicecetane', 'densite', 'recuperation362',
                   'cendre', 'massevolumique15', 'dateimpression']


class AffichageTableauImpression(tables.Table):
    # datereceptionlabo = tables.Column(verbose_name='DATE RECEPTION')
    codelabo = tables.Column(verbose_name='CODE LABO')
    numcertificatqualite = tables.Column(verbose_name='NUMERO CQ')
    nomproduit = tables.Column(verbose_name='NATURE PRODUIT')
    nomimportateur = tables.Column(verbose_name='FOURNISSEUR')
    nomentrepot = tables.Column(verbose_name='ENTREPROT')
    certificat = tables.TemplateColumn(IMPRESSION, verbose_name='')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }


class AffichageTableauReImpression(tables.Table):
    certificat = tables.TemplateColumn(REIMPRESSION, verbose_name='ACTIONS')
    # fiches = tables.TemplateColumn(IMPRESSION1)
    numrappech = tables.Column(accessor='idcargaison.idcargaison.numrappech', verbose_name='# RE')
    codelabo = tables.Column(accessor='idcargaison.codelabo', verbose_name='Code Labo')
    numcertificatqualite = tables.Column(accessor='idcargaison.numcertificatqualite', verbose_name='# CQ')
    produit = tables.Column(accessor='idcargaison.idcargaison.idcargaison.produit')
    importateur = tables.Column(accessor='idcargaison.idcargaison.idcargaison.importateur')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Resultat
        sequence = ['numcertificatqualite', 'produit', 'codelabo', 'numrappech', 'importateur']
        exclude = ['idcargaison', 'aspect', 'odeur', 'couleursaybolt', 'couleurastm', 'aciditetotal', 'soufre',
                   'soufremercaptan',
                   'docteurtest', 'massevolumique', 'aromatique', 'distillation', 'distillation10', 'distillation20',
                   'distillation50',
                   'distillation90', 'pointinitial', 'pointfinal', 'pointeclair', 'pointfumee', 'freezingpoint',
                   'residu', 'perte',
                   'viscosite', 'pointinflammabilite', 'pointecoulement', 'teneureau', 'sediment', 'corrosion',
                   'conductivite',
                   'pourcent10', 'pourcent20', 'pourcent50', 'pourcent70', 'pourcent90', 'difftemperature',
                   'tensionvapeur', 'plomb', 'indiceoctane',
                   'vol10', 'vol20', 'vol30', 'vol40', 'vol50', 'vol60', 'vol70', 'vol80', 'vol90', 'indicecetane',
                   'densite', 'recuperation362',
                   'cendre', 'massevolumique15', 'dateanalyse', 'dateimpression']


class TableEnvoiGo(tables.Table):
    actions = tables.TemplateColumn(GO, verbose_name='ACTIONS')
    numrappech = tables.Column(accessor='idcargaison.idcargaison.numrappech', verbose_name='Num. RE')
    codelabo = tables.Column(accessor='idcargaison.codelabo')
    numcertificatqualite = tables.Column(accessor='idcargaison.numcertificatqualite', verbose_name='Num. CQ')
    produit = tables.Column(accessor='idcargaison.idcargaison.idcargaison.produit')
    importateur = tables.Column(accessor='idcargaison.idcargaison.idcargaison.importateur')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Resultat
        sequence = ['numrappech', 'codelabo', 'numcertificatqualite', 'produit', 'importateur']
        exclude = ['idcargaison', 'aspect', 'odeur', 'couleursaybolt', 'couleurastm', 'aciditetotal', 'soufre',
                   'soufremercaptan',
                   'docteurtest', 'massevolumique', 'aromatique', 'distillation', 'distillation10', 'distillation20',
                   'distillation50',
                   'distillation90', 'pointinitial', 'pointfinal', 'pointeclair', 'pointfumee', 'freezingpoint',
                   'residu', 'perte',
                   'viscosite', 'pointinflammabilite', 'pointecoulement', 'teneureau', 'sediment', 'corrosion',
                   'conductivite',
                   'pourcent10', 'pourcent20', 'pourcent50', 'pourcent70', 'pourcent90', 'difftemperature',
                   'tensionvapeur', 'plomb', 'indiceoctane',
                   'vol10', 'vol20', 'vol30', 'vol40', 'vol50', 'vol60', 'vol70', 'vol80', 'vol90', 'indicecetane',
                   'densite', 'recuperation362', 'cendre', 'massevolumique15', 'dateanalyse', 'dateimpression']


class RapportLaboTable(tables.Table):
    dateechantillonage = tables.Column(verbose_name='Date Ech.')
    datereceptionlabo = tables.Column(verbose_name='Date Reception Labo')
    nomimportateur = tables.Column(verbose_name='Importateur')
    nomentrepot = tables.Column(verbose_name='Entrepot')
    immatriculation = tables.Column(verbose_name='Immatriculation')
    numdossier = tables.Column(verbose_name='Num. Dossier')
    codecargaison = tables.Column(verbose_name='Code Camion')
    numrappech = tables.Column(verbose_name="Rapport d'Ech.")
    codelabo = tables.Column(verbose_name='Code Labo')
    dateanalyse = tables.Column(verbose_name='Date Enc.')
    dateimpression = tables.Column(verbose_name='Date Impr.')
    numcertificatqualite = tables.Column(verbose_name='Num. CQ')

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['datereceptionlabo', 'dateechantillonage', 'nomimportateur', 'nomentrepot', 'immatriculation',
                    'numdossier', 'codecargaison', 'numrappech', 'codelabo', 'dateanalyse', 'dateimpression',
                    'numcertificatqualite']
        exclude = ['idcargaison']


class EchantReception(tables.Table):
    datereceptionlabo = tables.Column(verbose_name='Date Récep.')
    idcargaison__idcargaison__entrepot = tables.Column(verbose_name='Entrepot')
    idcargaison__idcargaison__importateur = tables.Column(verbose_name='Importateur')
    codelabo = tables.Column(verbose_name='Code Labo')
    idcargaison__idcargaison__numrappech = tables.Column(verbose_name='# RE')
    idcargaison__idcargaison__produit__nomproduit = tables.Column(verbose_name='Produit')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped",
                 "id": "table1"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['datereceptionlabo', 'idcargaison__idcargaison__importateur', 'idcargaison__idcargaison__entrepot',
                    'codelabo', 'idcargaison__idcargaison__numrappech', 'idcargaison__idcargaison__produit__nomproduit']
        exclude = ['idcargaison', 'numcertificatqualite']


#Template Column
champSaisieValeurResultat = """
 <form method=post action="{% url 'saisieResultatParametre' record.pk%}">
    {% csrf_token %}
     <input type="text" name="valeurResultat">
 </form>

"""

class SaisieResultat(tables.Table):
    nomproduit = tables.Column(verbose_name='PRODUIT')
    nomParametre = tables.Column(verbose_name='PARAMETRE(S)')
    valeurResultat = tables.Column(verbose_name='VALEUR RESULTAT NUM.')
    valeurResultatChar = tables.Column(verbose_name='VALEUR RESULTAT ALP.')
    saisieValeur = tables.TemplateColumn(champSaisieValeurResultat, verbose_name='ACTIONS')

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }


class AffichageDetailResultat(tables.Table):
    codelabo = tables.Column(verbose_name='CODE LABO')
    nomParametre = tables.Column(verbose_name='NOM PARAMETRE(S)')
    valeurMin = tables.Column(verbose_name='VALEUR MIN')
    valeurMax = tables.Column(verbose_name='VALEUR MAX')
    valeurResultatChar = tables.Column(verbose_name='RESULTAT(S) ALPH.')
    valeurResultat = tables.Column(verbose_name='RESULTAT(S) NUM')
    etatValeur = tables.Column(verbose_name='OBSERVATION(S)')

    class Meta:
        row_attrs = {
            'id':lambda record:record.etatValeur,
        }
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }


class RapportsLaboratoireReception(tables.Table):
    # actions = tables.TemplateColumn(TEMPLATE, verbose_name='ACTIONS')
    idcargaison__idcargaison__numdos = tables.Column(verbose_name="NUM.HYDRO")
    numrappechauto = tables.Column(accessor='idcargaison.numrappechauto',verbose_name="NUM.RE")
    idcargaison__dateechantillonage = tables.Column(verbose_name='DATE ECHANT.')
    datereceptionlabo = tables.Column(verbose_name="DATE RECEP.")
    idcargaison__idcargaison__entrepot = tables.Column(verbose_name='ENTREPOT')
    idcargaison__idcargaison__importateur = tables.Column(verbose_name="FOURNISSEUR")
    idcargaison__idcargaison__immatriculation = tables.Column(verbose_name="IMMATRICULATION")
    idcargaison__idcargaison__produit = tables.Column(verbose_name="PRODUIT")
    codelabo = tables.Column(verbose_name="CODE LABO")

    class Meta:
        attrs = {
            "class": "table table-bordered table-striped",
            "id": "example1"
        }


class RapportLaboratoireEnAttenteReception(tables.Table):
    entrepot_echantillon__dateechantillonage = tables.Column(verbose_name="DATE PRELEVEMENT.")
    entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")
    importateur__nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    produit__nomproduit = tables.Column(verbose_name="PRODUIT")
    numdos = tables.Column(verbose_name="NUM.DOSSIER")
    entrepot_echantillon__numrappechauto = tables.Column(verbose_name="NUM.RAPPORT ECHANT.")
    entrepot_echantillon__qte = tables.Column(verbose_name="QTE ECHANT.")

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"


class RapportLaboratoireEnAttenteResultat(tables.Table):
    entrepot_echantillon__dateechantillonage = tables.Column(verbose_name="DATE ECHANT.")
    entrepot_echantillon__laboreception__datereceptionlabo = tables.Column(verbose_name="DATE DE RECEPTION")
    numdos = tables.Column(verbose_name="NUM.DOSSIER")
    entrepot_echantillon__numrappechauto = tables.Column(verbose_name="NUM.RE")
    entrepot_echantillon__laboreception__codelabo = tables.Column(verbose_name='CODE LABO')
    entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")
    importateur__nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    produit__nomproduit = tables.Column(verbose_name="PRODUIT")
    entrepot_echantillon__qte = tables.Column(verbose_name="QTE")

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"



class RapportLaboratoireEnAttenteValidation(tables.Table):
    entrepot_echantillon__dateechantillonage = tables.Column(verbose_name="DATE ECHANT.")
    entrepot_echantillon__laboreception__datereceptionlabo = tables.Column(verbose_name="DATE DE RECEPTION")
    numdos = tables.Column(verbose_name="NUM.DOSSIER")
    entrepot_echantillon__numrappechauto = tables.Column(verbose_name="NUM.RE")
    entrepot_echantillon__laboreception__codelabo = tables.Column(verbose_name='CODE LABO')
    entrepot_echantillon__laboreception__numcertificatqualite = tables.Column(verbose_name='NUM.CQ')
    entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")
    importateur__nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    produit__nomproduit = tables.Column(verbose_name="PRODUIT")

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"


class RapportLaboratoireEnchPrintedCert(tables.Table):
    entrepot_echantillon__dateechantillonage = tables.Column(verbose_name="DATE ECHANT.")
    entrepot_echantillon__laboreception__datereceptionlabo = tables.Column(verbose_name="DATE DE RECEPTION")
    impressionresultat__printDate = tables.Column(verbose_name="DATE D'IMPRESSION")
    numdos = tables.Column(verbose_name="NUM.DOSSIER")
    entrepot_echantillon__numrappechauto = tables.Column(verbose_name="NUM.RE")
    entrepot_echantillon__laboreception__codelabo = tables.Column(verbose_name='CODE LABO')
    entrepot_echantillon__laboreception__numcertificatqualite = tables.Column(verbose_name='NUM.CQ')
    entrepot__nomentrepot = tables.Column(verbose_name="ENTREPOT")
    importateur__nomimportateur = tables.Column(verbose_name="FOURNISSEUR")
    produit__nomproduit = tables.Column(verbose_name="PRODUIT")

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"



class rapportActiviteCQ(tables.Table):
    entrepot_echantillon__dateechantillonage = tables.Column(verbose_name='DATE ECHANT.')
    entrepot_echantillon__laboreception__datereceptionlabo = tables.Column(verbose_name='DATE RECEP.')
    numdos = tables.Column(verbose_name='NUM.DOSSIER')
    entrepot_echantillon__numrappechauto = tables.Column(verbose_name='NUM.RE')
    entrepot_echantillon__laboreception__codelabo = tables.Column(verbose_name='CODE LABO')
    entrepot_echantillon__laboreception__numcertificatqualite = tables.Column(verbose_name='NUM.CQ')
    entrepot__nomentrepot = tables.Column(verbose_name='ENTREPOT')
    importateur__nomimportateur = tables.Column(verbose_name='IMPORTATEUR')
    immatriculation = tables.Column(verbose_name='IMMATRICULATION')
    produit__nomproduit = tables.Column(verbose_name='PRODUIT')
    conformiteProduit = tables.Column(verbose_name='CONFORMITE')

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"