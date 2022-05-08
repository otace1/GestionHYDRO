import django_tables2 as tables
from enreg.models import Cargaison, Entrepot_echantillon, LaboReception, Resultat

TEMPLATE = """ 
            <a href="{%url 'reception' record.pk%}" class="btn btn-success">Réception</a>
           """

# <button type="button" class="btn btn-danger" data-id="{{record.pk}}">
#                   Réception
# </button>

#
# <button type="button" class="btn btn-success" data-id={{record.pk}} data-toggle="modal" data-target="#modal-default">
#                   Réception
#                 </button>


# RECEPTIONNER = """
#                 <button type="button" class="btn btn-warning" data-id={{record.pk}} data-toggle="modal" data-target="#modal-modifier">
#                   Modifier
#                 </button>
#                 """

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
<a class="btn btn-primary" href="{%url 'mogas' record.pk%}" role="button">MOGAS</a>
<a class="btn btn-primary" href="{%url 'gasoil' record.pk%}" role="button">GASOIL</a>
<a class="btn btn-primary" href="{%url 'jeta1' record.pk%}" role="button">JET A1</a>
<a class="btn btn-primary" href="{%url 'petrole' record.pk%}" role="button">PETROLE</a>
            """

TEMPLATE2 = """
<a class="btn btn-primary" href="{%url 'mogasr' record.pk%}" role="button">MOGAS</a>
<a class="btn btn-primary" href="{%url 'gasoilr' record.pk%}" role="button">GASOIL</a>
<a class="btn btn-primary" href="{%url 'jeta1r' record.pk%}" role="button">JET A1</a>
<a class="btn btn-primary" href="{%url 'petroler' record.pk%}" role="button">PETROLE</a>
            """

VALIDATION1 = """
<a href="{%url 'rapportvalidationpdf' record.pk%}" class="btn btn-warning">AFFICHER</a>
<a href="{%url 'conforme' record.pk%}" class="btn btn-success">CONFORME</a>
<a href="{%url 'nonconforme' record.pk%}" class="btn btn-danger">NON CONFORME</a>
<a href="{%url 'refaire' record.pk%}" class="btn btn-light">A REFAIRE</a>
"""

CQ = """
 <form method=post action="{% url 'codecq' record.pk%}">
    {% csrf_token %}
     <input type="text" name="numcertificatqualite">
 </form>
 
"""

VALIDATION2 = """
<a href="{%url 'rapportvalidationpdf' record.pk%}" class="btn btn-warning">AFFICHER</a>
<a href="{%url 'conforme2' record.pk%}" class="btn btn-success">CONFORME</a>
<a href="{%url 'nonconforme2' record.pk%}" class="btn btn-danger">NON CONFORME</a>
"""

IMPRESSION = """
    <a href="{%url 'print' record.pk%}" class="btn btn-info">Impression</a>
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
    actions = tables.TemplateColumn(TEMPLATE, verbose_name='')
    idcargaison__dateheurecargaison = tables.Column(verbose_name="Date d'Entrée")
    dateechantillonage = tables.Column(verbose_name="Date d'Echantillonnage")
    idcargaison__immatriculation = tables.Column(verbose_name='Immatriculation')
    idcargaison__numdos = tables.Column(verbose_name="Numéro Dossier")
    # idcargaison__codecargaison = tables.Column(verbose_name='# Hydro')
    idcargaison__produit__nomproduit = tables.Column(verbose_name='Produit')
    numrappechauto = tables.Column(verbose_name="Rapport d'Echantillonnage")

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped",
                 "id": "table1"}
        template_name = "django_tables2/bootstrap4.html"
        model = Entrepot_echantillon
        sequence = ['idcargaison__dateheurecargaison', 'dateechantillonage', 'numrappechauto', 'idcargaison__numdos',
                    'idcargaison__immatriculation']
        exclude = ['numplombh', 'numplombb', 'numplombbr', 'numplombaph', 'etatphysique', 'numdossier',
                   'idcargaison__codecargaison', 'numrappech', 'useredit',
                   'qte', 'conformite', 'idcargaison__produit__nomproduit', 'idcargaison']


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
        attrs = {"class": "table table-hover text-nowrap table-striped",
                 "id": "table1"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['datereceptionlabo', 'idcargaison__numrappech', 'idcargaison__idcargaison__numdos',
                    'idcargaison__idcargaison__immatriculation', 'codelabo', 'numcertificatqualite']
        exclude = ['numplombh', 'numplombb', 'numplombbr', 'numplombaph', 'etatphysique', 'idcargaison__numrappech',
                   'qte', 'conformite', 'idcargaison__produit__nomproduit', 'idcargaison', 'idcargaison__codecargaison']


class AffichageAnalyse(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    numrappech = tables.Column(accessor='idcargaison.numrappech', verbose_name="Numéro de RE")
    produit = tables.Column(accessor='idcargaison.idcargaison.produit', verbose_name='Nature produit')
    datereceptionlabo = tables.Column(verbose_name='Date de réception')
    numcertificatqualite = tables.Column(verbose_name='Numéro CQ Attribué')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['datereceptionlabo', 'codelabo', 'numrappech', 'produit']
        exclude = ['numcertificatqualite', 'idcargaison']


class AffichageAnalyseRefaire(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE2, verbose_name='')
    numrappech = tables.Column(accessor='idcargaison.numrappech', verbose_name="Numéro de RE")
    produit = tables.Column(accessor='idcargaison.idcargaison.produit', verbose_name='Nature produit')
    datereceptionlabo = tables.Column(verbose_name='Date de réception')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['datereceptionlabo', 'codelabo', 'numrappech', 'produit']
        exclude = ['idcargaison', 'numcertificatqualite']


class AffichageValidation1(tables.Table):
    actions = tables.TemplateColumn(VALIDATION1, verbose_name='')
    # certificat = tables.TemplateColumn(CQ, verbose_name='C.Q')
    idcargaison__idcargaison__numrappech = tables.Column(verbose_name='Numéro RE')
    idcargaison__codelabo = tables.Column(verbose_name="Code Labo")
    idcargaison__numcertificatqualite = tables.Column(verbose_name="Numéro CQ")
    idcargaison__idcargaison__idcargaison__produit__nomproduit = tables.Column(verbose_name="Produit")
    idcargaison__idcargaison__idcargaison__importateur__nomimportateur = tables.Column(verbose_name="Importateur")

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['idcargaison__codelabo', 'idcargaison__idcargaison__numrappech',
                    'idcargaison__idcargaison__idcargaison__importateur__nomimportateur',
                    'idcargaison__idcargaison__idcargaison__produit__nomproduit', 'idcargaison__numcertificatqualite']
        exclude = ['idcargaison', 'numcertificatqualite', 'codelabo', 'datereceptionlabo']


class AffichageValidation2(tables.Table):
    actions = tables.TemplateColumn(VALIDATION2, verbose_name='')
    # certificat = tables.TemplateColumn(CQ, verbose_name='C.Q')
    idcargaison__idcargaison__numrappech = tables.Column(verbose_name='Numéro RE')
    idcargaison__codelabo = tables.Column(verbose_name="Code Labo")
    idcargaison__numcertificatqualite = tables.Column(verbose_name="Numéro CQ")
    idcargaison__idcargaison__idcargaison__produit__nomproduit = tables.Column(verbose_name="Produit")
    idcargaison__idcargaison__idcargaison__importateur__nomimportateur = tables.Column(verbose_name="Importateur")

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['idcargaison__codelabo', 'idcargaison__idcargaison__numrappech',
                    'idcargaison__idcargaison__idcargaison__importateur__nomimportateur',
                    'idcargaison__idcargaison__idcargaison__produit__nomproduit', 'idcargaison__numcertificatqualite']
        exclude = ['idcargaison', 'numcertificatqualite', 'codelabo', 'datereceptionlabo']


class AffichageValidation2Go(tables.Table):
    actions = tables.TemplateColumn(GO)
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
    certificat = tables.TemplateColumn(IMPRESSION, verbose_name='')
    # fiches = tables.TemplateColumn(IMPRESSION1)
    numrappech = tables.Column(accessor='idcargaison.idcargaison.numrappech', verbose_name='Numero RE')
    codelabo = tables.Column(accessor='idcargaison.codelabo', verbose_name='Code Labo')
    numcertificatqualite = tables.Column(accessor='idcargaison.numcertificatqualite', verbose_name='Numero CQ')
    produit = tables.Column(accessor='idcargaison.idcargaison.idcargaison.produit')
    importateur = tables.Column(accessor='idcargaison.idcargaison.idcargaison.importateur')
    immatriculation = tables.Column(accessor='idcargaison.idcargaison.idcargaison.immatriculation')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Resultat
        sequence = ['dateanalyse','numcertificatqualite', 'codelabo', 'numrappech','produit', 'importateur','immatriculation']
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
                   'cendre', 'massevolumique15', 'dateimpression']


class AffichageTableauReImpression(tables.Table):
    certificat = tables.TemplateColumn(REIMPRESSION, verbose_name='')
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
    actions = tables.TemplateColumn(GO)
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
