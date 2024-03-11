from datetime import datetime as dt
from accounts.models import *
from enreg.models import *

def numCq(v):
    current_date = dt.now()
    current_year = current_date.year

    query = f'''
                SELECT l.idcargaison_id, c.idcargaison, MAX(l.numcertificatqualite) as last_code
                FROM enreg_laboreception l
                JOIN enreg_cargaison c ON l.idcargaison_id = c.idcargaison
                JOIN enreg_entrepot e ON c.entrepot_id = e.identrepot
                JOIN enreg_ville v ON e.ville_id = v.idville
                WHERE YEAR(l.datereceptionlabo) = {current_year}
                AND v.idville = {v}
                GROUP BY l.idcargaison_id, c.idcargaison
            '''

    last_code_result = Cargaison.objects.raw(query)
    last_code = None

    for result in last_code_result:
        last_code = result.last_code

    return last_code
