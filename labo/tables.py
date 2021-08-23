import django_tables2 as tables
from enreg.models import Cargaison, Entrepot_echantillon, LaboReception, Resultat

TEMPLATE = """
            <button type="button" class="btn btn-success" data-id={{record.pk}} data-toggle="modal" data-target="#modal-default">
                  Réception
                </button>
           """

RECEPTIONNER = """
                <button type="button" class="btn btn-success" data-id={{record.pk}} data-toggle="modal" data-target="#modal-modifier">
                  Modifier
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
<a href="{%url 'rapportvalidationpdf' record.pk%}" class="btn btn-info">Afficher les résultats</a>
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
    immatriculation = tables.Column(verbose_name='Immatriculation')
    numdossier = tables.Column(verbose_name="# Dossier")
    codecargaison = tables.Column(verbose_name='# Hydro')
    produit = tables.Column(verbose_name='Produit')
    numrappech = tables.Column(verbose_name='# RE')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped",
                 "id":"table1"}
        template_name = "django_tables2/bootstrap4.html"
        model = Entrepot_echantillon
        sequence = ['numrappech', 'numdossier', 'codecargaison', 'produit', 'immatriculation']
        exclude = ['numplombh', 'numplombb', 'numplombbr', 'numplombaph', 'etatphysique',
                   'qte', 'conformite', 'idcargaison', 'dateechantillonage']


class TableauEchantillonRecu(tables.Table):
    actions = tables.TemplateColumn(RECEPTIONNER, verbose_name='')
    immatriculation = tables.Column(verbose_name='Immatriculation ')
    numdossier = tables.Column(verbose_name='# Dossier')
    codecargaison = tables.Column(verbose_name='# Hydro')
    codelabo = tables.Column(verbose_name='Code Labo')
    datereceptionlabo = tables.Column(verbose_name='Date de réception Labo')
    produit = tables.Column(verbose_name='Produit')
    numrappech = tables.Column(verbose_name='# RE')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Entrepot_echantillon
        sequence = ['codelabo', 'numrappech', 'codecargaison', 'immatriculation']
        exclude = ['numplombh', 'numplombb', 'numplombbr', 'numplombaph', 'etatphysique', 'idcargaison','numdossier',
                   'qte', 'produit', 'conformite', 'dateechantillonage', 'datereceptionlabo']


class AffichageAnalyse(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE1, verbose_name='')
    numrappech = tables.Column(accessor='idcargaison.numrappech', verbose_name='# RE')
    produit = tables.Column(accessor='idcargaison.idcargaison.produit')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['codelabo', 'numrappech', 'produit']
        exclude = ['idcargaison', 'datereceptionlabo', 'numcertificatqualite']


class AffichageAnalyseRefaire(tables.Table):
    actions = tables.TemplateColumn(TEMPLATE2, verbose_name='')
    numrappech = tables.Column(accessor='idcargaison.numrappech', verbose_name='# RE')
    produit = tables.Column(accessor='idcargaison.idcargaison.produit')

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = LaboReception
        sequence = ['codelabo', 'numrappech', 'produit']
        exclude = ['idcargaison', 'datereceptionlabo', 'numcertificatqualite']


class AffichageValidation1(tables.Table):
    actions = tables.TemplateColumn(VALIDATION1, verbose_name='')
    certificat = tables.TemplateColumn(CQ, verbose_name='C.Q')
    numrappech = tables.Column(accessor='idcargaison.idcargaison.numrappech', verbose_name='Numéro RE')
    codelabo = tables.Column(accessor='idcargaison.codelabo', verbose_name="Code Labo")
    numcertificatqualite = tables.Column(accessor='idcargaison.numcertificatqualite', verbose_name="Numéro CQ")
    produit = tables.Column(accessor='idcargaison.idcargaison.idcargaison.produit', verbose_name="Produit")
    importateur = tables.Column(accessor='idcargaison.idcargaison.idcargaison.importateur', verbose_name="Importateur")

    class Meta:
        attrs = {"class": "table table-hover table-bordered table-responsive-sm"}
        template_name = "django_tables2/bootstrap4.html"
        model = Resultat
        sequence = ['codelabo', 'numrappech', 'importateur', 'produit', 'numcertificatqualite', 'certificat']
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
                   'cendre', 'massevolumique15', 'dateimpression', 'dateanalyse']


class AffichageValidation2(tables.Table):
    actions = tables.TemplateColumn(VALIDATION2)
    numrappech = tables.Column(accessor='idcargaison.idcargaison.numrappech', verbose_name='Numéro RE')
    codelabo = tables.Column(accessor='idcargaison.codelabo', verbose_name="Code Labo")
    numcertificatqualite = tables.Column(accessor='idcargaison.numcertificatqualite', verbose_name="Numéro CQ")
    produit = tables.Column(accessor='idcargaison.idcargaison.idcargaison.produit', verbose_name="Produit")
    importateur = tables.Column(accessor='idcargaison.idcargaison.idcargaison.importateur', verbose_name="Importateur")

    class Meta:
        attrs = {"class": "table table-hover text-nowrap table-striped"}
        template_name = "django_tables2/bootstrap4.html"
        model = Resultat
        sequence = ['dateanalyse', 'codelabo', 'numcertificatqualite', 'numrappech', 'importateur', 'produit']
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
