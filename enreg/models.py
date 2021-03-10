from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django_countries.fields import CountryField


# Create your models here.
class Nationalites(models.Model):
    idnationalite = models.AutoField(primary_key=True, auto_created=True)
    nationalite = models.CharField(max_length=256)

    def __str__(self):
        return self.nationalite

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idnationalite})

    def natural_key(self):
        return self.my_natural_key


class Banques(models.Model):
    idbanque = models.AutoField(primary_key=True, auto_created=True)
    nombanque = models.CharField(max_length=256)

    def __str__(self):
        return self.nombanque

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idbanque})

    def natural_key(self):
        return self.my_natural_key


class Voie(models.Model):
    idvoie = models.AutoField(primary_key=True, auto_created=True)
    nomvoie = models.CharField(max_length=30)

    def __str__(self):
        return self.nomvoie

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idvoie})

    def natural_key(self):
        return self.my_natural_key


class Ville(models.Model):
    idville = models.AutoField(primary_key=True, auto_created=True)
    nomville = models.CharField(max_length=30)
    province = models.CharField(max_length=30)

    def __str__(self):
        return self.nomville

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idville})

    def natural_key(self):
        return self.my_natural_key


class Importateur(models.Model):
    idimportateur = models.AutoField(primary_key=True, auto_created=True)
    nomimportateur = models.CharField(max_length=100)
    adresseimportateur = models.CharField(max_length=100, blank=True)
    nifimportateur = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nomimportateur

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idimportateur})

    def natural_key(self):
        return self.my_natural_key


class Entrepot(models.Model):
    identrepot = models.AutoField(primary_key=True, auto_created=True)
    nomentrepot = models.CharField(max_length=100)
    adresseentrepot = models.CharField(max_length=100)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)

    def __str__(self):
        return self.nomentrepot

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.identrepot})

    def natural_key(self):
        return self.my_natural_key


class Produit(models.Model):
    idproduit = models.AutoField(primary_key=True, auto_created=True)
    nomproduit = models.CharField(max_length=30)

    def __str__(self):
        return self.nomproduit

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idproduit})

    def natural_key(self):
        return self.my_natural_key


class Cargaison(models.Model):
    idcargaison = models.AutoField(primary_key=True, auto_created=True)
    voie = models.ForeignKey(Voie, on_delete=models.CASCADE, verbose_name="Voie d'entrée")
    fournisseur = models.CharField(max_length=100, verbose_name='Fournisseur', blank=True)
    importateur = models.ForeignKey(Importateur, on_delete=models.CASCADE, verbose_name="Importateur")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, verbose_name="Produit")
    frontiere = models.ForeignKey(Ville, on_delete=models.CASCADE, verbose_name='Frontiere')
    provenance = CountryField(blank_label='(Selectionner le pays)', verbose_name='Provenance')
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, verbose_name='Entrepot')
    transporteur = models.CharField(max_length=30, verbose_name='Transporteur')
    declarant = models.CharField(max_length=30, verbose_name='Déclarant')
    poids = models.DecimalField(max_digits=20, decimal_places=2, default='0', verbose_name='Poids')
    volume = models.DecimalField(max_digits=20, decimal_places=2, default='0', verbose_name='Volume')
    tempcargaison = models.DecimalField(max_digits=20, decimal_places=2, default='20', blank=True)
    densitecargaison = models.DecimalField(max_digits=20, decimal_places=2, default='0', blank=True)
    t1d = models.CharField(max_length=64, default='0000', blank=True, verbose_name='T1D')
    t1e = models.CharField(max_length=64, default='0000', blank=True, verbose_name='T1E')
    numdeclaration = models.CharField(max_length=64, blank=True, verbose_name='Numéro Declaration')
    manifestdgda = models.CharField(max_length=65, blank=True, verbose_name='Manifeste DGDA')
    numbtfh = models.CharField(max_length=65, blank=True, verbose_name='Numéro BT/ Fiche Chauffeur')
    valeurfacture = models.DecimalField(max_digits=65, blank=True, decimal_places=3, default=0,
                                        verbose_name='Valeur facture')
    idchauffeur = models.CharField(max_length=30, blank=True)
    nationalite = models.ForeignKey(Nationalites, on_delete=models.CASCADE)
    nomchauffeur = models.CharField(max_length=200)
    immatriculation = models.CharField(max_length=200, verbose_name='Immatriculation')

    dateheurecargaison = models.DateTimeField(auto_now_add=True, verbose_name='Date et heure')
    qrcode = models.CharField(max_length=250, default='NULL')
    etat = models.CharField(max_length=250, default='NULL')

    volume_decl15 = models.DecimalField(max_digits=20, decimal_places=2, default='0', blank=True,
                                        verbose_name="Volume a 15 degré")
    numdossier = models.CharField(max_length=30, default='NULL', blank=True, verbose_name="Numéro Dossier Hydro")
    codecargaison = models.CharField(max_length=30, default='NULL', blank=True, verbose_name="Codification Hydro")
    numact = models.IntegerField(null=True, verbose_name="Numéro ACT")
    conformite = models.CharField(max_length=30, default='NULL', blank=True, verbose_name='Conformité aux exigences')
    impression = models.BooleanField(default="0")
    user = models.CharField(max_length=200, default='NULL', blank=True, verbose_name='User')
    tampon = models.CharField(max_length=2, default="1")

    l_control = models.IntegerField(null=True)

    printactdate = models.DateField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idcargaison})

    def natural_key(self):
        return self.my_natural_key


class Entrepot_echantillon(models.Model):
    idcargaison = models.OneToOneField(Cargaison, on_delete=models.CASCADE, primary_key=True)
    numrappech = models.CharField(max_length=256, verbose_name="Rapport d'Echantillonage")
    numplombh = models.CharField(max_length=256, verbose_name="Numero Plomb H")
    numplombb = models.CharField(max_length=256)
    numplombbr = models.CharField(max_length=256)
    numplombaph = models.CharField(max_length=256)
    etatphysique = models.CharField(max_length=256)
    qte = models.CharField(max_length=256)
    conformite = models.CharField(max_length=256)
    dateechantillonage = models.DateField(verbose_name="Date d'Echantillonage")


class LaboReception(models.Model):
    idcargaison = models.OneToOneField(Entrepot_echantillon, on_delete=models.CASCADE, primary_key=True)
    numcertificatqualite = models.CharField(max_length=256, verbose_name="Numero du Certificat de Qualite ", blank=True)
    codelabo = models.CharField(max_length=256, verbose_name="Code Labo ")
    datereceptionlabo = models.DateField(verbose_name="Date reception")

    def get_absolute_url(self):
        return reverse('reception', kwargs={'pk': self.idcargaison})

    def natural_key(self):
        return self.my_natural_key


class Resultat(models.Model):
    idcargaison = models.OneToOneField(LaboReception, on_delete=models.CASCADE, primary_key=True)
    aspect = models.CharField(max_length=32, blank=True, default='Claire et Limpide')
    odeur = models.CharField(max_length=32, blank=True, default='Marchande')
    couleursaybolt = models.CharField(max_length=32, blank=True)
    couleurastm = models.CharField(max_length=32, blank=True)
    aciditetotal = models.CharField(max_length=32, blank=True)
    soufre = models.CharField(max_length=32, blank=True)
    soufremercaptan = models.CharField(max_length=32, blank=True)
    docteurtest = models.CharField(max_length=32, blank=True)
    massevolumique = models.CharField(max_length=32, blank=True)
    aromatique = models.CharField(max_length=32, blank=True)
    distillation = models.CharField(max_length=32, blank=True)
    distillation10 = models.CharField(max_length=32, blank=True)
    distillation20 = models.CharField(max_length=32, blank=True)
    distillation50 = models.CharField(max_length=32, blank=True)
    distillation90 = models.CharField(max_length=32, blank=True)
    pointinitial = models.CharField(max_length=32, blank=True)
    pointfinal = models.CharField(max_length=32, blank=True)
    pointeclair = models.CharField(max_length=32, blank=True)
    pointfumee = models.CharField(max_length=32, blank=True)
    freezingpoint = models.CharField(max_length=32, blank=True)
    residu = models.CharField(max_length=32, blank=True)
    perte = models.CharField(max_length=32, blank=True)
    viscosite = models.CharField(max_length=32, blank=True)
    pointinflammabilite = models.CharField(max_length=32, blank=True)
    pointecoulement = models.CharField(max_length=32, blank=True)
    teneureau = models.CharField(max_length=32, blank=True)
    sediment = models.CharField(max_length=32, blank=True)
    corrosion = models.CharField(max_length=32, blank=True, default='1b')
    conductivite = models.CharField(max_length=32, blank=True)
    pourcent10 = models.CharField(max_length=32, blank=True)
    pourcent20 = models.CharField(max_length=32, blank=True)
    pourcent50 = models.CharField(max_length=32, blank=True)
    pourcent70 = models.CharField(max_length=32, blank=True)
    pourcent90 = models.CharField(max_length=32, blank=True)
    difftemperature = models.CharField(max_length=32, blank=True)
    tensionvapeur = models.CharField(max_length=32, blank=True)
    plomb = models.CharField(max_length=32, blank=True)
    indiceoctane = models.CharField(max_length=32, blank=True)
    vol10 = models.CharField(max_length=32, blank=True)
    vol20 = models.CharField(max_length=32, blank=True)
    vol30 = models.CharField(max_length=32, blank=True)
    vol40 = models.CharField(max_length=32, blank=True)
    vol50 = models.CharField(max_length=32, blank=True)
    vol60 = models.CharField(max_length=32, blank=True)
    vol70 = models.CharField(max_length=32, blank=True)
    vol80 = models.CharField(max_length=32, blank=True)
    vol90 = models.CharField(max_length=32, blank=True)
    indicecetane = models.CharField(max_length=32, blank=True)
    densite = models.CharField(max_length=32, blank=True)
    recuperation362 = models.CharField(max_length=32, blank=True)
    cendre = models.CharField(max_length=32, blank=True)
    massevolumique15 = models.CharField(max_length=32, blank=True)

    dateanalyse = models.DateTimeField(auto_now_add=True, verbose_name="Date d'analyse")
    dateimpression = models.DateField(blank=True)


class Dechargement(models.Model):
    idcargaison = models.OneToOneField(Resultat, on_delete=models.CASCADE, primary_key=True)
    densite15 = models.DecimalField(max_digits=20, decimal_places=3)
    temperature = models.DecimalField(max_digits=20, decimal_places=3)
    gov = models.DecimalField(max_digits=20, decimal_places=3)
    gsv = models.DecimalField(max_digits=20, decimal_places=3)
    mta = models.DecimalField(max_digits=20, decimal_places=3)
    mtv = models.DecimalField(max_digits=20, decimal_places=3)
    datedechargement = models.DateField(auto_now=True)


class BureauDGDA(models.Model):
    idbureau = models.AutoField(primary_key=True, auto_created=True)
    codebureau = models.CharField(max_length=20)
    descriptionbureau = models.CharField(max_length=250)

    def __str__(self):
        return self.codebureau

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idbureau})

    def natural_key(self):
        return self.my_natural_key


class Paiement(models.Model):
    code_bur = models.CharField(max_length=128, verbose_name='Code BUR')
    bureau = models.CharField(max_length=128, verbose_name='Nom BUR')
    modele = models.CharField(max_length=128, verbose_name='Modele')
    nif_importateur = models.CharField(max_length=128, verbose_name='NIF Importateur')
    importateur = models.CharField(max_length=250, verbose_name='Nom Importateur')
    nom_decl = models.CharField(max_length=128, verbose_name='Declarant')
    n_liq = models.CharField(max_length=128, verbose_name='BL')
    date_liq = models.DateField(verbose_name='Date BL')
    ide_ser = models.CharField(max_length=128, verbose_name='')
    ide_nbr = models.CharField(max_length=128, verbose_name='Quittance')
    date_pay = models.DateField(verbose_name='Date Paiement')
    tax_cod = models.CharField(max_length=128)
    mont_enc = models.DecimalField(max_digits=32, decimal_places=4, verbose_name='Montant')
    bnk_nam = models.CharField(max_length=128, verbose_name='Nom Banque')
    libelle = models.CharField(max_length=128, verbose_name='libelle')
    ref_pay = models.CharField(max_length=128, verbose_name='')
    taux = models.DecimalField(max_digits=32, decimal_places=4, verbose_name='Taux')
    qte_stat = models.DecimalField(max_digits=32, decimal_places=4, verbose_name='Qte payee')

    def __str__(self):
        return self.bnk_nam

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idbureau})

    def natural_key(self):
        return self.my_natural_key


class Liquidation(models.Model):
    idliquidation = models.AutoField(primary_key=True, auto_created=True)
    idcargaison = models.ForeignKey(Cargaison, on_delete=models.CASCADE)
    numerobl = models.CharField(max_length=30, blank=True, verbose_name='Numéro BL')
    datebl = models.DateField(blank=True, verbose_name='Date de BL')
    codebureau = models.ForeignKey(BureauDGDA, on_delete=models.CASCADE, verbose_name='Code Bureau')
    vol_liq = models.DecimalField(max_digits=32, decimal_places=4, blank=True)
    type_appurement = models.IntegerField(default=False, blank=True)
