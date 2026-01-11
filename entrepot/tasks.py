import base64
import datetime
from celery import shared_task
from django.utils import timezone
from enreg.models import Cargaison, Entrepot_echantillon
from accounts.models import MyUser
from accounts.services import log_action
from labo.utils import render_to_pdf_content
from .numrappech import numRappEch

@shared_task(bind=True)
def process_sampling_task(self, pk, form_data, user_id):
    """
    Asynchronous task to process sampling and generate a report.
    """
    self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Récupération des données...'})
    
    try:
        user = MyUser.objects.get(id=user_id)
        c = Cargaison.objects.get(idcargaison=pk)
        
        # Check if sampling already exists
        if Entrepot_echantillon.objects.filter(idcargaison_id=pk).exists():
            return {
                'status': 'error', 
                'message': 'Cet échantillonnage a déjà été enregistré.'
            }

        self.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Enregistrement de l\'échantillonnage...'})
        
        ville = c.entrepot.ville
        numrappechauto = numRappEch(pk, ville)
        
        today = datetime.datetime.now()
        
        c.rapechctrl = 1
        c.etatInspection = 1
        c.etat = "Echantillonner"
        c.save(update_fields=['etat', 'rapechctrl', 'etatInspection'])

        e = Entrepot_echantillon.objects.create(
            idcargaison=c,
            numrappechauto=numrappechauto,
            matricule=form_data['matricule'],
            methodeutilisee=form_data['methodeutilisee'],
            qte=form_data['qte'],
            conformite=form_data['conformite'],
            dateechantillonage=today
        )

        log_action(
            user=user,
            action="SAMPLING_CREATE",
            description=f"Échantillonnage créé pour la cargaison {c.idcargaison} (via Celery)",
            obj=e
        )

        self.update_state(state='PROGRESS', meta={'progress': 60, 'status': 'Génération du rapport PDF...'})
        
        # Prepare data for PDF
        template = 'rapportechantillonage.html'
        data = {
            'dateechantillonage': e.dateechantillonage,
            'dateech': e.dateechantillonage,
            'entrepot': c.entrepot,
            'numdos': c.numdos,
            'methodeutilisee': e.methodeutilisee,
            'importateur': c.importateur,
            'adresseimportateur': c.importateur.adresseimportateur,
            'produit': c.produit,
            'volume': c.volume,
            'provenance': c.provenance.name,
            'voie': c.voie.nomvoie,
            'immatriculation': c.immatriculation,
            'matricule': e.matricule,
            'qtelabo': e.qte,
            'conformite': e.conformite,
            'numrappechauto': e.numrappechauto,
        }

        pdf_content = render_to_pdf_content(template, data)
        self.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Finalisation...'})
        
        if pdf_content:
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            return {
                'status': 'success', 
                'pdf_base64': pdf_base64,
                'message': 'Échantillonnage et rapport générés avec succès.'
            }
        else:
            return {
                'status': 'warning', 
                'message': 'Échantillonnage enregistré, mais erreur lors de la génération du PDF.'
            }

    except Cargaison.DoesNotExist:
        return {'status': 'error', 'message': f'Cargaison {pk} non trouvée.'}
    except Exception as ex:
        return {'status': 'error', 'message': str(ex)}
