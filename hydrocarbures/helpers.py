import csv
from datetime import datetime, timedelta, time
from io import StringIO, BytesIO

from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.timezone import make_aware, get_current_timezone

from hydrocarbures import settings

TZ = get_current_timezone()

def _safe_int(val, default):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _parse_date(date_str, end_of_day=False):
    """
    Expect 'YYYY-MM-DD'. Returns a naive datetime (no tzinfo) since USE_TZ=False.
    If end_of_day=True, set time to 23:59:59 to cover the full day.
    """
    if not date_str:
        return None
    try:
        if end_of_day:
            # inclusive end of day
            return datetime.strptime(date_str, "%Y-%m-%d") + timedelta(hours=23, minutes=59, seconds=59)
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def _parse_date_yyyymmdd(s: str, *, end_of_day: bool = False):
    """
    Parse 'YYYY-MM-DD' into a datetime.
    - If settings.USE_TZ is True => returns *aware* (in current timezone)
    - If settings.USE_TZ is False => returns *naive* (MySQL requirement)
    """
    if not s:
        return None
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None

    t = time(23, 59, 59, 999999) if end_of_day else time(0, 0, 0, 0)
    dt = datetime.combine(d, t)

    if getattr(settings, "USE_TZ", False):
        # make aware in the current timezone
        tz = timezone.get_current_timezone()
        return timezone.make_aware(dt, tz)
    else:
        # leave naive for MySQL when USE_TZ=False
        return dt



def _fmt_dt(dt):
    """Safe datetime → 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' depending on presence of time."""
    if not dt:
        return ""
    try:
        # if there is any nonzero time component, include time; otherwise just date
        if getattr(dt, "hour", 0) or getattr(dt, "minute", 0) or getattr(dt, "second", 0):
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(dt)


# ---- helpers ---------------------------------------------------------------
def _status_q(status):
    """
    Map your UI statuses → queryset filters.
    Adjust the mapping to your real business rules if needed.
    """
    if not status:
        return Q()  # no-op

    status = status.lower()
    if status == "declared":
        # All registered cargo (baseline). No extra filter.
        return Q()
    if status == "certified":
        # Example: “certified” when lab result/conformity exists & is positive.
        return Q(conformite__iexact="CONFORME") | Q(isConsignated=True)
    if status == "pending":
        # Example: pending = no conformity yet and not refouled.
        return Q(conformite__isnull=True) & Q(isRefouler=False)
    if status == "rejected":
        # Example: rejected = refouled or conformity explicitly negative
        return Q(isRefouler=True) | Q(conformite__iexact="NON CONFORME")
    return Q()


def _filename(base, ext):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{ts}.{ext}"


def _write_csv_response(filename, headers, rows_iterable):
    """
    `rows_iterable` yields lists/tuples matching headers length.
    """
    # Use UTF-8 BOM to open nicely in Excel
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    sio = StringIO()
    sio.write("\ufeff")
    writer = csv.writer(sio)
    writer.writerow(headers)
    for row in rows_iterable:
        writer.writerow(row)
    resp.write(sio.getvalue())
    return resp


def _write_xlsx_response(filename, headers, rows_iterable, title="Report"):
    """
    Minimal XLSX writer using openpyxl if available. Falls back to CSV if not.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter
        from openpyxl.styles import Font, Alignment
    except Exception:
        # Fallback to CSV
        return _write_csv_response(filename.replace(".xlsx", ".csv"), headers, rows_iterable)

    wb = Workbook()
    ws = wb.active
    ws.title = title

    # Header
    bold = Font(bold=True)
    for c_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=c_idx, value=h)
        cell.font = bold
        cell.alignment = Alignment(vertical="center")
        ws.column_dimensions[get_column_letter(c_idx)].width = max(12, min(36, len(h) + 2))

    # Rows
    r = 2
    for row in rows_iterable:
        for c_idx, val in enumerate(row, start=1):
            ws.cell(row=r, column=c_idx, value=val)
        r += 1

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    resp = HttpResponse(bio.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def _write_pdf_response(filename, headers, rows_iterable, title="Report"):
    """
    Extremely simple PDF using reportlab (if installed).
    Not styled; good enough as a proof of concept.
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
    except Exception:
        return HttpResponseBadRequest("PDF export is not available on this server (reportlab not installed).")

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    width, height = landscape(A4)
    x_margin, y_margin = 15 * mm, 15 * mm
    y = height - y_margin

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_margin, y, title)
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_margin, y, " | ".join(headers))
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    for row in rows_iterable:
        line = " | ".join("" if v is None else str(v) for v in row)
        if y < 20 * mm:
            c.showPage()
            y = height - y_margin
            c.setFont("Helvetica", 9)
        c.drawString(x_margin, y, line[:260])  # keep it on page
        y -= 5 * mm

    c.showPage()
    c.save()
    pdf = buf.getvalue()
    buf.close()

    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
