from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django_countries.fields import CountryField


# Create your models here.
class TypeUniteTransport(models.Model):
    idunite = models.AutoField(primary_key=True, auto_created=True)
    unitetransport = models.CharField(max_length=256)

    def __str__(self):
        return self.unitetransport

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idunite})


class Nationalites(models.Model):
    idnationalite = models.AutoField(primary_key=True, auto_created=True)
    nationalite = models.CharField(max_length=256)

    def __str__(self):
        return self.nationalite

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idnationalite})


class Banques(models.Model):
    idbanque = models.AutoField(primary_key=True, auto_created=True)
    nombanque = models.CharField(max_length=256)

    def __str__(self):
        return self.nombanque

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idbanque})


class Voie(models.Model):
    idvoie = models.AutoField(primary_key=True, auto_created=True)
    nomvoie = models.CharField(max_length=30)

    def __str__(self):
        return self.nomvoie

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idvoie})


class Ville(models.Model):
    idville = models.AutoField(primary_key=True, auto_created=True)
    nomville = models.CharField(max_length=30, db_index=True)
    province = models.CharField(max_length=30)

    def __str__(self):
        return self.nomville

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idville})


class Importateur(models.Model):
    idimportateur = models.AutoField(primary_key=True, auto_created=True)
    nomimportateur = models.CharField(max_length=100, db_index=True)
    adresseimportateur = models.CharField(max_length=100, blank=True)
    nifimportateur = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.nomimportateur

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idimportateur})


class Entrepot(models.Model):
    identrepot = models.AutoField(primary_key=True, auto_created=True)
    nomentrepot = models.CharField(max_length=100, verbose_name="NOM ENTREPOT", db_index=True)
    adresseentrepot = models.CharField(max_length=100, verbose_name="ADRESSE PHYSIQUE")
    ville = models.ForeignKey(Ville, on_delete=models.PROTECT, verbose_name="VILLE")

    def __str__(self):
        return self.nomentrepot

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.identrepot})


class Produit(models.Model):
    idproduit = models.AutoField(primary_key=True, auto_created=True)
    nomproduit = models.CharField(max_length=30, db_index=True)

    def __str__(self):
        return self.nomproduit

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idproduit})


class Cargaison(models.Model):
    idcargaison = models.AutoField(primary_key=True, auto_created=True)
    voie = models.ForeignKey(Voie, on_delete=models.PROTECT, verbose_name="Voie d'entrée")
    importateur = models.ForeignKey(Importateur, on_delete=models.PROTECT, verbose_name="Importateur")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, verbose_name="Produit")
    frontiere = models.ForeignKey(Ville, on_delete=models.PROTECT, verbose_name='Frontiere')
    provenance = CountryField(blank_label='(Selectionner le pays)', verbose_name='Provenance')
    entrepot = models.ForeignKey(Entrepot, on_delete=models.PROTECT, verbose_name='Entrepot')
    volume = models.FloatField(verbose_name='Volume')
    immatriculation = models.CharField(max_length=200, blank=True, null=True, verbose_name='Immatriculation',
                                       db_index=True)
    dateheurecargaison = models.DateTimeField(auto_now_add=True, verbose_name='Date et heure', db_index=True)
    qrcode = models.CharField(max_length=250, default='NULL')
    etat = models.CharField(max_length=250, default='NULL', db_index=True)
    numdossier = models.CharField(max_length=30, null=True, blank=True, verbose_name="Numéro Dossier Hydro",
                                  db_index=True)
    codecargaison = models.CharField(max_length=30, null=True, blank=True, verbose_name="Codification Hydro",
                                     db_index=True)
    numact = models.IntegerField(null=True, blank=True, verbose_name="Numéro ACT", db_index=True)
    numCertInspection = models.IntegerField(null=True)
    conformite = models.CharField(max_length=30, blank=True, null=True, verbose_name='DECISION LABO')
    impression = models.BooleanField(default="0")
    user = models.CharField(max_length=200, default='NULL', blank=True, verbose_name='User')
    tampon = models.CharField(max_length=2, default="1")

    # A ajouter en migration apres
    requisitionack = models.CharField(max_length=200, blank=True, null=True)
    requisitiondackdate = models.DateTimeField(blank=True, null=True)

    # numero de dossier a considere
    numdos = models.IntegerField(blank=True, null=True, db_index=True)
    numreq = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    # Controle rapport d'echantillonage
    rapechctrl = models.IntegerField(blank=True, null=True)

    # Nouveau champ a ajouter
    typeunitetransport = models.ForeignKey(TypeUniteTransport, on_delete=models.PROTECT, blank=True, null=True)
    volume15 = models.FloatField(blank=True, null=True)
    volume20 = models.FloatField(blank=True, null=True)
    tonnagevide = models.FloatField(blank=True, null=True)
    tonnageair = models.FloatField(blank=True, null=True)

    # Shore Inspection
    before = models.BooleanField(default=0, verbose_name='SHORE BEFORE')
    after = models.BooleanField(default=0, verbose_name='SHORE AFTER')

    # Champ ajouter apres la mission de l'EST
    declaration = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Numero de declaration

    transitaire = models.CharField(max_length=255, blank=True, null=True)  # Transitaire

    # Champ de control pour l'inspection
    etatInspection = models.BooleanField(default=False, db_index=True)

    # Date et heure d'analyse
    dateHeureAnalyseLabo = models.DateTimeField(blank=True, null=True)
    dateDechargement = models.DateTimeField(blank=True, null=True)

    # For the Consignation
    toBeRefouler = models.BooleanField(default=False)
    toBeConsignated = models.BooleanField(default=False)
    isConsignated = models.BooleanField(default=False)
    isRefouler = models.BooleanField(default=False)

    # True or False, is True if the file is liquidatetd totally, and stay false otherwise
    controlLiquidation = models.BooleanField(default=False)
    partialLiquidattion = models.BooleanField(default=False)  # change based on the type of paiement

    # File path saving
    files_path = models.CharField(blank=True, null=True, max_length=256)

    # Denormalized fields
    nom_importateur = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    nom_entrepot = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    nom_produit = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    nom_frontiere = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    date_echantillon = models.DateTimeField(blank=True, null=True, db_index=True)
    date_reception_labo = models.DateTimeField(blank=True, null=True, db_index=True)
    date_analyse = models.DateTimeField(blank=True, null=True, db_index=True)
    date_inspection = models.DateTimeField(blank=True, null=True, db_index=True)

    gov_total = models.FloatField(default=0.0, db_index=True)
    gsv_total = models.FloatField(default=0.0, db_index=True)
    mta_total = models.FloatField(default=0.0, db_index=True)
    mtv_total = models.FloatField(default=0.0, db_index=True)

    densite_inspection = models.FloatField(null=True, blank=True, db_index=True)
    temperature_inspection = models.FloatField(null=True, blank=True, db_index=True)

    # Denormalized Labo fields
    num_certificat_qualite = models.IntegerField(null=True, blank=True, db_index=True)
    code_labo = models.IntegerField(null=True, blank=True, db_index=True)
    date_resultat = models.DateTimeField(null=True, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        if self.typeunitetransport and self.volume:
            if self.typeunitetransport.unitetransport.strip().upper() == "CAMION CITERNE" and self.volume > 50:
                raise ValidationError("Pour un Camion citerne, le volume ne peut pas dépasser 50.")
        if self.importateur_id:
            self.nom_importateur = self.importateur.nomimportateur
        if self.entrepot_id:
            self.nom_entrepot = self.entrepot.nomentrepot
        if self.produit_id:
            self.nom_produit = self.produit.nomproduit
        if self.frontiere_id:
            self.nom_frontiere = self.frontiere.nomville
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['etat', 'entrepot', '-dateheurecargaison', '-idcargaison']),
            models.Index(fields=['dateheurecargaison']),
            models.Index(fields=['immatriculation']),
            models.Index(fields=['declaration']),
            models.Index(fields=['numdos']),
            models.Index(fields=['nom_importateur']),
            models.Index(fields=['nom_entrepot']),
            models.Index(fields=['nom_produit']),
            models.Index(fields=['nom_frontiere']),
            models.Index(fields=['date_echantillon']),
            models.Index(fields=['date_reception_labo']),
            models.Index(fields=['date_analyse']),
            models.Index(fields=['date_inspection']),
        ]

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idcargaison})


class Entrepot_echantillon(models.Model):
    idcargaison = models.OneToOneField(Cargaison, on_delete=models.PROTECT, primary_key=True)
    numrappech = models.CharField(max_length=256, verbose_name="Rapport d'Echantillonage", blank=True, null=True)
    numrappechauto = models.IntegerField(blank=True, null=True, verbose_name="Num. RE", db_index=True)
    qte = models.CharField(max_length=256, blank=True, null=True)
    conformite = models.CharField(max_length=256, blank=True)
    dateechantillonage = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    useredit = models.CharField(max_length=256, null=True, blank=True)
    matricule = models.CharField(max_length=256, blank=True)
    methodeutilisee = models.CharField(max_length=256, blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.idcargaison.date_echantillon = self.dateechantillonage
            self.idcargaison.save(update_fields=['date_echantillon'])


class LaboReception(models.Model):
    idcargaison = models.OneToOneField(Entrepot_echantillon, on_delete=models.PROTECT, primary_key=True)
    numcertificatqualite = models.IntegerField(verbose_name="Numero du Certificat de Qualite ", null=True, blank=True,
                                               db_index=True)
    codelabo = models.IntegerField(null=True, blank=True, verbose_name="Code Labo ", db_index=True)
    datereceptionlabo = models.DateTimeField(blank=True, null=True, db_index=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Up to Cargaison (via Entrepot_echantillon)
        cargaison = self.idcargaison.idcargaison
        cargaison.date_reception_labo = self.datereceptionlabo
        cargaison.num_certificat_qualite = self.numcertificatqualite
        cargaison.code_labo = self.codelabo
        cargaison.save(update_fields=['date_reception_labo', 'num_certificat_qualite', 'code_labo'])

    def get_absolute_url(self):
        return reverse('reception', kwargs={'pk': self.idcargaison})


class Resultat(models.Model):
    idcargaison = models.OneToOneField(LaboReception, on_delete=models.PROTECT, primary_key=True)
    aspect = models.CharField(max_length=32, blank=True, default='Claire et Limpide')
    odeur = models.CharField(max_length=32, blank=True, default='Marchande')
    couleursaybolt = models.CharField(max_length=32, blank=True, null=True)
    couleurastm = models.CharField(max_length=32, blank=True, null=True)
    aciditetotal = models.FloatField(max_length=20, blank=True, null=True)
    soufre = models.FloatField(max_length=20, blank=True, null=True)
    soufremercaptan = models.FloatField(max_length=20, blank=True, null=True)
    docteurtest = models.FloatField(max_length=20, blank=True, null=True)
    massevolumique = models.FloatField(max_length=20, blank=True, null=True)
    aromatique = models.CharField(max_length=20, blank=True, null=True)
    distillation = models.FloatField(max_length=20, blank=True, null=True)
    distillation10 = models.FloatField(max_length=20, blank=True, null=True)
    distillation20 = models.FloatField(max_length=20, blank=True, null=True)
    distillation50 = models.FloatField(max_length=20, blank=True, null=True)
    distillation90 = models.FloatField(max_length=20, blank=True, null=True)
    pointinitial = models.FloatField(max_length=20, blank=True, null=True)
    pointfinal = models.FloatField(max_length=20, blank=True, null=True)
    pointeclair = models.FloatField(max_length=20, blank=True, null=True)
    pointfumee = models.FloatField(max_length=20, blank=True, null=True)
    freezingpoint = models.FloatField(max_length=20, blank=True, null=True)
    residu = models.FloatField(max_length=20, blank=True, null=True)
    perte = models.FloatField(max_length=20, blank=True, null=True)
    viscosite = models.FloatField(max_length=20, blank=True, null=True)
    pointinflammabilite = models.FloatField(max_length=20, blank=True, null=True)
    pointecoulement = models.FloatField(max_length=20, blank=True, null=True)
    teneureau = models.FloatField(max_length=20, blank=True, null=True)
    sediment = models.FloatField(max_length=20, blank=True, null=True)
    corrosion = models.CharField(max_length=20, blank=True, default='1b', null=True)
    conductivite = models.FloatField(max_length=20, blank=True, null=True)
    pourcent10 = models.FloatField(max_length=20, blank=True, null=True)
    pourcent20 = models.FloatField(max_length=20, blank=True, null=True)
    pourcent50 = models.FloatField(max_length=20, blank=True, null=True)
    pourcent70 = models.FloatField(max_length=20, blank=True, null=True)
    pourcent90 = models.FloatField(max_length=20, blank=True, null=True)
    difftemperature = models.FloatField(max_length=20, blank=True, null=True)
    tensionvapeur = models.FloatField(max_length=20, blank=True, null=True)
    plomb = models.FloatField(max_length=20, blank=True, null=True)
    indiceoctane = models.FloatField(max_length=20, blank=True, null=True)
    vol10 = models.FloatField(max_length=20, blank=True, null=True)
    vol20 = models.FloatField(max_length=20, blank=True, null=True)
    vol30 = models.FloatField(max_length=20, blank=True, null=True)
    vol40 = models.FloatField(max_length=20, blank=True, null=True)
    vol50 = models.FloatField(max_length=20, blank=True, null=True)
    vol60 = models.FloatField(max_length=20, blank=True, null=True)
    vol70 = models.FloatField(max_length=20, blank=True, null=True)
    vol80 = models.FloatField(max_length=20, blank=True, null=True)
    vol90 = models.FloatField(max_length=20, blank=True, null=True)
    indicecetane = models.FloatField(max_length=20, blank=True, null=True)
    densite = models.FloatField(max_length=20, blank=True, null=True)
    recuperation362 = models.FloatField(max_length=20, blank=True, null=True)
    cendre = models.FloatField(max_length=20, blank=True, null=True)
    massevolumique15 = models.FloatField(max_length=20, blank=True, null=True)

    dateanalyse = models.DateTimeField(auto_now_add=True, verbose_name="Date d'analyse", blank=True, null=True)
    dateimpression = models.DateField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Up to Cargaison (via LaboReception -> Entrepot_echantillon)
        cargaison = self.idcargaison.idcargaison.idcargaison
        cargaison.date_analyse = self.dateanalyse
        cargaison.save(update_fields=['date_analyse'])


class Dechargement(models.Model):
    idcargaison = models.OneToOneField(Resultat, on_delete=models.PROTECT, primary_key=True)
    densite = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    govmeter = models.FloatField(null=True, blank=True)
    gsvjaugee = models.FloatField(blank=True, null=True)
    gsvmeter = models.FloatField(blank=True, null=True)
    mta = models.FloatField()
    mtv = models.FloatField()
    vcf = models.FloatField(null=True, blank=True)
    indexinitial = models.FloatField(null=True, blank=True)
    indexfinal = models.FloatField(null=True, blank=True)
    typescontainer = models.CharField(max_length=32, blank=True, null=True)
    datedechargement = models.DateField(auto_now=True)
    user = models.CharField(max_length=256, blank=True)
    mtameter = models.FloatField(blank=True, null=True)
    mtvmeter = models.FloatField(blank=True, null=True)
    vcfmeter = models.FloatField(blank=True, null=True)
    govjaugee = models.FloatField(blank=True, null=True)


class BureauDGDA(models.Model):
    idbureau = models.AutoField(primary_key=True, auto_created=True)
    codebureau = models.CharField(max_length=20)
    descriptionbureau = models.CharField(max_length=250)

    def __str__(self):
        return self.codebureau

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idbureau})


class Paiement(models.Model):
    code_bur = models.CharField(max_length=128, verbose_name='Code BUR', db_index=True)
    bureau = models.CharField(max_length=255, verbose_name='Nom BUR')
    modele = models.CharField(max_length=255, verbose_name='Modele')
    nif_importateur = models.CharField(max_length=128, verbose_name='NIF Importateur', db_index=True)
    importateur = models.CharField(max_length=255, verbose_name='Nom Importateur', db_index=True)
    nom_decl = models.CharField(max_length=255, verbose_name='Declarant', db_index=True)
    n_liq = models.CharField(max_length=128, verbose_name='BL', db_index=True)
    date_liq = models.DateField(verbose_name='Date BL', db_index=True)
    ide_ser = models.CharField(max_length=128, verbose_name='')
    ide_nbr = models.CharField(max_length=128, verbose_name='Quittance', db_index=True)
    date_pay = models.DateField(verbose_name='Date Paiement', db_index=True)
    tax_cod = models.CharField(max_length=128, verbose_name='')
    bnk_nam = models.CharField(max_length=255, verbose_name='Nom Banque', db_index=True)
    libelle = models.CharField(max_length=255, verbose_name='libelle')
    ref_pay = models.CharField(max_length=255, verbose_name='')
    taux = models.DecimalField(max_digits=32, decimal_places=4, verbose_name='Taux')
    qte_stat = models.DecimalField(max_digits=32, decimal_places=4, verbose_name='Qte payee')
    qp_cgw = models.DecimalField(max_digits=32, decimal_places=4, verbose_name='QP CGW')
    qp_occ = models.DecimalField(max_digits=32, decimal_places=4, verbose_name='QP OCC')

    class Meta:
        indexes = [
            models.Index(fields=['code_bur', 'date_liq', 'n_liq']),
            models.Index(fields=['importateur']),
            models.Index(fields=['nif_importateur']),
            models.Index(fields=['date_pay']),
            models.Index(fields=['ide_nbr']),
        ]

    def __str__(self):
        return self.bnk_nam

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.pk})


class LiquidationModel(models.Model):
    idLiquidationMod = models.AutoField(primary_key=True, auto_created=True)
    liquidationModel = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.liquidationModel


class Liquidation(models.Model):
    idliquidation = models.AutoField(primary_key=True, auto_created=True)
    idcargaison = models.ForeignKey(Cargaison, on_delete=models.PROTECT)
    numerobl = models.CharField(max_length=30, blank=True, verbose_name='Numéro BL', db_index=True)
    datebl = models.DateField(blank=True, null=True, verbose_name='Date de BL')
    datepay = models.DateField(blank=True, null=True)
    bankName = models.CharField(max_length=128, blank=True)
    codebureau = models.ForeignKey(BureauDGDA, on_delete=models.PROTECT, verbose_name='Code Bureau')
    modele = models.ForeignKey(LiquidationModel, on_delete=models.PROTECT, null=True)
    vol_liq = models.DecimalField(max_digits=32, decimal_places=4, blank=True)
    type_appurement = models.CharField(max_length=32, blank=True, null=True)
    user = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['idcargaison', 'codebureau']),
        ]


class SealState(models.Model):
    idsealstate = models.AutoField(primary_key=True, auto_created=True)
    sealstate = models.CharField(max_length=256)

    def __str__(self):
        return self.sealstate


class InspectionSeal(models.Model):
    manifoldnumber = models.CharField(max_length=256, verbose_name='MANIFOLD NUMBER')
    sealstate = models.ForeignKey(SealState, on_delete=models.PROTECT, verbose_name='SEALS STATE')
    idcargaison = models.ForeignKey(Cargaison, on_delete=models.PROTECT)

    def __str__(self):
        return self.manifoldnumber

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.id})


class Inspection(models.Model):
    idcargaison = models.OneToOneField(Cargaison, on_delete=models.PROTECT)
    idinspection = models.AutoField(primary_key=True, auto_created=True)
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, null=True)
    dens = models.FloatField(null=True)
    temp = models.FloatField(null=True)
    innagein = models.CharField(max_length=256, blank=True, null=True)
    volumein = models.CharField(max_length=256, blank=True, null=True)
    tempin = models.CharField(max_length=256, blank=True, null=True)
    weightin = models.CharField(max_length=256, blank=True, null=True)
    meterbefore = models.FloatField(null=True)
    meterafter = models.FloatField(null=True)
    dateinspection = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.idcargaison.date_inspection = self.dateinspection
        self.idcargaison.densite_inspection = self.dens
        self.idcargaison.temperature_inspection = self.temp
        self.idcargaison.save(update_fields=['date_inspection', 'densite_inspection', 'temperature_inspection'])

    # def __str__(self):
    #     return self.idinspection

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idinspection})


class Compartiment(models.Model):
    idinspection = models.ForeignKey(Inspection, on_delete=models.PROTECT)
    id = models.AutoField(primary_key=True, auto_created=True)
    compart = models.CharField(max_length=32, blank=True, verbose_name='DENOM. COMPARTIMENT')
    sealstate = models.ForeignKey(SealState, on_delete=models.PROTECT, verbose_name='SEAL STATE')
    sealNumber = models.CharField(max_length=30, blank=True, null=True, verbose_name='SEAL NUMBER')
    # produit = models.ForeignKey(Produit, on_delete=models.PROTECT, verbose_name='PRODUIT')
    innage = models.FloatField(null=True, blank=True, verbose_name='INNAGE')
    gov = models.FloatField(null=True, verbose_name='GOV JAUGE')
    tempcomp = models.FloatField(null=True, verbose_name='TEMPERATURE')
    vcf = models.FloatField(null=True)
    mta = models.FloatField(null=True)
    mtv = models.FloatField(null=True)
    gsv = models.FloatField(null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update Cargaison totals
        inspection = self.idinspection
        cargaison = inspection.idcargaison
        from django.db.models import Sum
        totals = Compartiment.objects.filter(idinspection=inspection).aggregate(
            gov=Sum('gov'), gsv=Sum('gsv'), mta=Sum('mta'), mtv=Sum('mtv')
        )
        cargaison.gov_total = totals['gov'] or 0.0
        cargaison.gsv_total = totals['gsv'] or 0.0
        cargaison.mta_total = totals['mta'] or 0.0
        cargaison.mtv_total = totals['mtv'] or 0.0
        cargaison.save(update_fields=['gov_total', 'gsv_total', 'mta_total', 'mtv_total'])

    def __str__(self):
        return self.compart

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idinspection_id})


class ShoreTank(models.Model):
    idinspection = models.ForeignKey(Inspection, on_delete=models.PROTECT)
    id = models.AutoField(primary_key=True, auto_created=True)
    tankdenombefore = models.CharField(max_length=32, verbose_name='TANK DENOM.')
    prodinnagebefore = models.FloatField(null=True, verbose_name='PROD. INNAGE')
    fwdeepbefore = models.FloatField(null=True, verbose_name='FW DEEP')
    govbefore = models.FloatField(null=True, verbose_name='GOV')
    tempbefore = models.FloatField(null=True, verbose_name='Temp.')
    fwvolbefore = models.FloatField(null=True, verbose_name='FW VOL.')
    tankdenomafter = models.CharField(max_length=32, verbose_name='TANK DENOM.')
    prodinnageafter = models.FloatField(null=True, verbose_name='PROD. INNAGE')
    fwdeepafter = models.FloatField(null=True, verbose_name='FW DEEP')
    govafter = models.FloatField(null=True, verbose_name='GOV')
    tempafter = models.FloatField(null=True, verbose_name='Temp.')
    fwvolafter = models.FloatField(null=True, verbose_name='FW VOL.')
    dateheurebefore = models.DateTimeField(auto_now_add=True)
    dateheureafter = models.DateTimeField(null=True)

    densitybefore = models.FloatField(null=True, verbose_name='DENS.15')
    densityafter = models.FloatField(null=True, verbose_name='DENS.15')

    gsvbefore = models.FloatField(null=True, verbose_name='GSV')
    gsvafter = models.FloatField(null=True, verbose_name='GSV')

    mtvbefore = models.FloatField(null=True, verbose_name='MTV')
    mtvafter = models.FloatField(null=True, verbose_name='MTV')

    mtabefore = models.FloatField(null=True, verbose_name='MTA')
    mtaafter = models.FloatField(null=True, verbose_name='MTA')

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.id})


class Shore(models.Model):
    idinspection = models.ForeignKey(Inspection, on_delete=models.PROTECT, null=True)
    idshore = models.AutoField(primary_key=True, auto_created=True)
    innagein = models.FloatField(null=True)
    volumein = models.FloatField(null=True)
    tempin = models.FloatField(null=True)
    weightin = models.FloatField(null=True)

    def __str__(self):
        return self.idshore

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idshore})


class ShoreBefore(models.Model):
    idshore = models.ForeignKey(Shore, on_delete=models.PROTECT)
    tankdenombefore = models.CharField(max_length=32, verbose_name='TANK DENOM.')
    prodinnagebefore = models.FloatField(null=True, verbose_name='PROD. INNAGE')
    fwdeepbefore = models.FloatField(null=True, verbose_name='FW DEEP')
    govbefore = models.FloatField(null=True, verbose_name='GOV')
    tempbefore = models.FloatField(null=True, verbose_name='Temp.')
    fwvolbefore = models.FloatField(null=True, verbose_name='FW VOL.')

    def __str__(self):
        return self.idshore

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idshore})


class ShoreAfter(models.Model):
    idshore = models.ForeignKey(Shore, on_delete=models.PROTECT)
    tankdenomafter = models.CharField(max_length=32, verbose_name='TANK DENOM.')
    prodinnageafter = models.FloatField(null=True, verbose_name='PROD. INNAGE')
    fwdeepafter = models.FloatField(null=True, verbose_name='FW DEEP')
    govafter = models.FloatField(null=True, verbose_name='GOV')
    tempafter = models.FloatField(null=True, verbose_name='Temp.')
    fwvolafter = models.FloatField(null=True, verbose_name='FW VOL.')

    def __str__(self):
        return self.idshore

    def get_absolute_url(self):
        return reverse('update', kwargs={'pk': self.idshore})


class ControlNatureProduit(models.Model):
    idcontrol = models.AutoField(primary_key=True, auto_created=True)
    idcargaison = models.ForeignKey(Cargaison, on_delete=models.PROTECT, blank=True, null=True)
    natureProduitEntrepot = models.CharField(max_length=20, blank=True, null=True)
    natureProduitLabo = models.CharField(max_length=20, blank=True, null=True)
    userEntrepot = models.IntegerField(blank=True, null=True)
    userLabo = models.IntegerField(blank=True, null=True)
    conformiteProduit = models.BooleanField(default=True)
    correctionNature = models.CharField(max_length=20, blank=True, null=True)
    userHydro = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now=True, blank=True, null=True)


class ParametresProduits(models.Model):
    idParametre = models.AutoField(primary_key=True, auto_created=True)
    nomParametre = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.nomParametre


class AffectationParametre(models.Model):
    idParametre = models.ForeignKey(ParametresProduits, on_delete=models.PROTECT)
    idproduit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    valeurMin = models.FloatField(blank=True, null=True)
    valeurMax = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ('idParametre', 'idproduit')


class ResultatAnalyse(models.Model):
    idResultatAnalyse = models.AutoField(primary_key=True, auto_created=True)
    idParametre = models.ForeignKey(ParametresProduits, on_delete=models.PROTECT)
    idcargaison = models.ForeignKey(Cargaison, on_delete=models.PROTECT, db_index=True)
    valeurResultat = models.FloatField(blank=True, null=True)
    valeurResultatChar = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        unique_together = ('idcargaison', 'idParametre')
        indexes = [
            models.Index(fields=['idcargaison', 'idParametre']),
            models.Index(fields=['idParametre', 'valeurResultat']),
        ]


class ImpressionResultat(models.Model):
    idImpression = models.AutoField(primary_key=True, auto_created=True)
    idcargaison = models.ForeignKey(Cargaison, on_delete=models.PROTECT)
    printDate = models.DateField(blank=True, null=True)
    isConforme = models.BooleanField(null=True, blank=True)
    isPrinted = models.BooleanField(null=True, blank=True)
    control = models.BooleanField(default=0)
