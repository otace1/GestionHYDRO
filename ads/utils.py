from django.utils import timezone
from datetime import date

def get_current_year():
    """
    Returns the current year using Django's timezone-aware local date.
    Safe for both USE_TZ=True and USE_TZ=False.
    """
    now = timezone.now()
    if timezone.is_aware(now):
        return timezone.localdate(now).year
    return now.year

def get_current_year_range():
    """
    Returns (year_start, year_end) for the current calendar year.
    year_start = Jan 1 of current year
    year_end = Jan 1 of next year (exclusive)
    """
    current_year = get_current_year()
    year_start = date(current_year, 1, 1)
    year_end = date(current_year + 1, 1, 1)
    return year_start, year_end

def get_current_year_range_filter(field_name='dateheurecargaison'):
    """
    Returns a dictionary for filtering a queryset by the current calendar year range.
    Example usage: Cargaison.objects.filter(**get_current_year_range_filter())
    Uses end-exclusive range (>= year_start and < year_end).
    """
    start, end = get_current_year_range()
    return {
        f'{field_name}__gte': start,
        f'{field_name}__lt': end,
    }
