from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from enreg.models import Cargaison


from django.views.decorators.http import require_POST


@login_required(login_url='login')
@require_POST
def kpiStatusCounts(request):
    """
    KPI counters for dashboard cards based on Cargaison statuses.
    Returns JSON: { data: { ... } }
    """
    try:
        # If needed, scope by user as per business rules; currently using global counts
        base = Cargaison.objects.all()

        data = {
            'attente_requisition': base.filter(etat="En attente requisition").count(),
            'attente_echantillonage': base.filter(etat="En attente d'echantillonage").count(),
            'analyse_labo_cours': base.filter(etat="Analyse Labo en cours").count(),
            'inspection_en_attente': base.filter(etatInspection=1).count(),
            'echantillonner': base.filter(etat="Echantillonner").count(),
            'conforme_exigences': base.filter(etat="Conforme aux exigences").count(),
        }
        return JsonResponse({'data': data})
    except Exception as exc:
        return JsonResponse({'error': 'Failed to load KPI status counts', 'detail': str(exc)}, status=500)
