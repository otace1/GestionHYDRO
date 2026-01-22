from enreg.models import Cargaison, ResultatAnalyse, ImpressionResultat
from accounts.models import AffectationVille, AffectationLaboratoire, ListeLaboratoire

def get_report_context(idcargaison, user=None, sign_gauche_override=None, sign_droite_override=None, lab_name_override=None, province_override=None):
    try:
        cargaison = Cargaison.objects.select_related(
            'entrepot_echantillon', 
            'entrepot_echantillon__laboreception'
        ).get(idcargaison=idcargaison)
    except Cargaison.DoesNotExist:
        return None

    impressionData = ImpressionResultat.objects.filter(idcargaison_id=idcargaison).first()
    
    labo_rec = cargaison.entrepot_echantillon.laboreception
    mois = labo_rec.datereceptionlabo.month if labo_rec and labo_rec.datereceptionlabo else None
    annee = labo_rec.datereceptionlabo.year if labo_rec and labo_rec.datereceptionlabo else None

    produit = cargaison.nom_produit
    echantillon = cargaison.entrepot_echantillon
    laboratoire = labo_rec

    # Signers and Lab Data
    signGauche = sign_gauche_override
    signDroite = sign_droite_override
    laboratoireData = None
    province = province_override or ""

    if lab_name_override:
        try:
            laboratoireData = ListeLaboratoire.objects.get(denominationLaboratoire=lab_name_override)
        except ListeLaboratoire.DoesNotExist:
            pass

    if user and not (signGauche and signDroite):
        try:
            aff_ville = AffectationVille.objects.select_related('ville').get(username_id=user.id)
            ville_id = aff_ville.ville_id
            if not province:
                province = (aff_ville.ville.province or "").upper()
            
            affects = AffectationLaboratoire.objects.filter(ville_id=ville_id).select_related('userId', 'idLaboratoire')
            for aff in affects:
                if aff.signGauche:
                    if not signGauche: signGauche = aff.userId
                else:
                    if not signDroite: signDroite = aff.userId
                    if not laboratoireData: laboratoireData = aff.idLaboratoire
        except:
            pass

    results = ResultatAnalyse.objects.filter(idcargaison=idcargaison).values('idParametre_id', 'valeurResultat', 'valeurResultatChar')
    res_dict = {r['idParametre_id']: r for r in results}

    context = {
        'laboratoire': laboratoire,
        'cargaison': cargaison,
        'echantillon': echantillon,
        'annee': annee,
        'mois': mois,
        'impressionData': impressionData,
        'produit': produit,
        'signGauche': signGauche,
        'signDroite': signDroite,
        'laboratoireData': laboratoireData,
        'province': province,
    }

    if produit == 'GASOIL':
        context.update({
            'couleurastm': res_dict.get(8, {}).get('valeurResultatChar', ''),
            'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
            'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
            'massevolumique': res_dict.get(21, {}).get('valeurResultat', ''),
            'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
            'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
            'distillation10': res_dict.get(11, {}).get('valeurResultat', ''),
            'distillation20': res_dict.get(12, {}).get('valeurResultat', ''),
            'distillation50': res_dict.get(13, {}).get('valeurResultat', ''),
            'distillation90': res_dict.get(15, {}).get('valeurResultat', ''),
            'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
            'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
            'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
            'viscosite': res_dict.get(38, {}).get('valeurResultat', ''),
            'pointecoulement': res_dict.get(26, {}).get('valeurResultat', ''),
            'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
            'sediment': res_dict.get(32, {}).get('valeurResultat', ''),
            'indicecetane': res_dict.get(19, {}).get('valeurResultat', ''),
            'recuperation362': res_dict.get(10, {}).get('valeurResultat', ''),
            'cendre': res_dict.get(3, {}).get('valeurResultat', ''),
        })
        try:
            cor_str = res_dict.get(6, {}).get('valeurResultat', '')
            context['corrosion'] = int(cor_str) if cor_str != '' else ''
        except: context['corrosion'] = ''

    elif produit == 'MOGAS':
        context.update({
            'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
            'odeur': res_dict.get(22, {}).get('valeurResultatChar', ''),
            'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
            'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
            'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
            'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
            'residu': res_dict.get(31, {}).get('valeurResultat', ''),
            'pourcent10': res_dict.get(11, {}).get('valeurResultat', ''),
            'pourcent20': res_dict.get(12, {}).get('valeurResultat', ''),
            'pourcent50': res_dict.get(13, {}).get('valeurResultat', ''),
            'pourcent70': res_dict.get(14, {}).get('valeurResultat', ''),
            'pourcent90': res_dict.get(15, {}).get('valeurResultat', ''),
            'tensionvapeur': res_dict.get(36, {}).get('valeurResultat', ''),
            'difftemperature': res_dict.get(9, {}).get('valeurResultat', ''),
            'plomb': res_dict.get(24, {}).get('valeurResultat', ''),
            'indiceoctane': res_dict.get(18, {}).get('valeurResultat', ''),
            'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
        })
        try:
            cor_str = res_dict.get(7, {}).get('valeurResultat', '')
            context['corrosion'] = int(cor_str) if cor_str != '' else ''
        except: context['corrosion'] = ''

    elif produit == 'JET A1':
        context.update({
            'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
            'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
            'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
            'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
            'soufremercaptan': res_dict.get(33, {}).get('valeurResultat', ''),
            'docteurtest': res_dict.get(16, {}).get('valeurResultat', ''),
            'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
            'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
            'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
            'pointfumee': res_dict.get(28, {}).get('valeurResultat', ''),
            'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
            'freezingpoint': res_dict.get(17, {}).get('valeurResultat', ''),
            'residu': res_dict.get(31, {}).get('valeurResultat', ''),
            'perte': res_dict.get(23, {}).get('valeurResultat', ''),
            'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
            'viscosite': res_dict.get(37, {}).get('valeurResultat', ''),
            'pointinflammabilite': res_dict.get(27, {}).get('valeurResultat', ''),
            'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
            'conductivite': res_dict.get(4, {}).get('valeurResultat', ''),
            'vol10': res_dict.get(11, {}).get('valeurResultat', ''),
            'vol20': res_dict.get(12, {}).get('valeurResultat', ''),
            'vol30': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol40': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol50': res_dict.get(13, {}).get('valeurResultat', ''),
            'vol60': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol70': res_dict.get(14, {}).get('valeurResultat', ''),
            'vol80': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol90': res_dict.get(15, {}).get('valeurResultat', ''),
        })
        try:
            cor_str = res_dict.get(5, {}).get('valeurResultat', '')
            context['corrosion'] = int(cor_str) if cor_str != '' else ''
        except: context['corrosion'] = ''

    elif produit == 'PETROLE LAMPANT':
        context.update({
            'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
            'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
            'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
            'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
            'soufremercaptan': res_dict.get(33, {}).get('valeurResultat', ''),
            'docteurtest': res_dict.get(16, {}).get('valeurResultat', ''),
            'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
            'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
            'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
            'pointfumee': res_dict.get(28, {}).get('valeurResultat', ''),
            'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
            'freezingpoint': res_dict.get(17, {}).get('valeurResultat', ''),
            'residu': res_dict.get(31, {}).get('valeurResultat', ''),
            'perte': res_dict.get(23, {}).get('valeurResultat', ''),
            'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
            'viscosite': res_dict.get(37, {}).get('valeurResultat', ''),
            'pointinflammabilite': res_dict.get(27, {}).get('valeurResultat', ''),
            'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
            'conductivite': res_dict.get(4, {}).get('valeurResultat', ''),
            'vol10': res_dict.get(11, {}).get('valeurResultat', ''),
            'vol20': res_dict.get(12, {}).get('valeurResultat', ''),
            'vol30': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol40': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol50': res_dict.get(13, {}).get('valeurResultat', ''),
            'vol60': res_dict.get(44, {}).get('valeurResultat', ''),
            'vol70': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol80': res_dict.get(100, {}).get('valeurResultat', ''),
            'vol90': res_dict.get(15, {}).get('valeurResultat', ''),
        })
        try:
            cor_str = res_dict.get(5, {}).get('valeurResultat', '')
            context['corrosion'] = int(cor_str) if cor_str != '' else ''
        except: context['corrosion'] = ''

    return context
