from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Q

from enreg.models import Cargaison
from .utils import get_current_year, get_current_year_range_filter


from django.views.decorators.http import require_POST


@login_required(login_url='login')
@require_POST
def kpiStatusCounts(request):
    """
    KPI counters for dashboard cards based on Cargaison statuses.
    Returns JSON: { data: { ... } }
    Cached for performance.
    """
    current_year = get_current_year()
    cache_key = f"ads:kpi_status_counts_{current_year}"
    data = cache.get(cache_key)

    if data is not None:
        return JsonResponse({'data': data})

    try:
        # Filter by current year
        year_filter = get_current_year_range_filter()
        base = Cargaison.objects.filter(**year_filter)

        data = {
            'attente_requisition': base.filter(etat="En attente requisition").count(),
            'attente_echantillonage': base.filter(etat="En attente d'echantillonage").count(),
            'analyse_labo_cours': base.filter(etat="Analyse Labo en cours").count(),
            'inspection_en_attente': base.filter(etatInspection=True).count(),
            'echantillonner': base.filter(etat="Echantillonner").count(),
            'conforme_exigences': base.filter(etat="Conforme aux exigences").count(),
        }
        # Cache for 5 minutes
        cache.set(cache_key, data, 5 * 60)
        return JsonResponse({'data': data})
    except Exception as exc:
        return JsonResponse({'error': 'Failed to load KPI status counts', 'detail': str(exc)}, status=500)
