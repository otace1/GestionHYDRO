# Test for faster export to XLSX with PyExcelerate
from io import BytesIO

import pandas as pd


def export_excel(df):
    df = pd.read_json(df, convert_dates=['dateheurecargaison'])
    bn = pd.DataFrame(df)

    with BytesIO() as b:
        writer = pd.ExcelWriter(b, engine='xlsxwriter')
        bn.to_excel(writer, sheet_name='Statistiques', index=False)
        writer.save()
        filename = 'stat'
        content_type = 'application/vnd.ms-excel'
        response = HttpResponse(b.getvalue(), content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="' + filename + '.xlsx"'
        return response

    # a = Dechargement.objects.values(
    #     'idcargaison__idcargaison__idcargaison__idcargaison__importateur__nomimportateur').annotate(nombrecamions=Count('idcargaison'),nombrecamionsc=Count()
    #     Gasoil=Sum('gov', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=1)),
    #     Mogas=Sum('gov', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=2)),
    #     Jet=Sum('gov', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=3)),
    #     Petrole=Sum('gov', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=4)),
    #     Gasoil_D=Sum('gsv', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=1)),
    #     Mogas_D=Sum('gsv', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=2)),
    #     Jet_D=Sum('gsv', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=3)),
    #     Petrole_D=Sum('gsv', filter=Q(idcargaison__idcargaison__idcargaison__idcargaison__produit=4)),
    #     Total=Sum('gsv')).order_by('-Total')
