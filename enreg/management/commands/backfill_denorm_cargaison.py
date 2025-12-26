from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from enreg.models import (
    Cargaison, Entrepot_echantillon, LaboReception, Resultat, Inspection, Compartiment
)

class Command(BaseCommand):
    help = "Backfill denormalized fields on Cargaison (batched)"

    def add_arguments(self, parser):
        parser.add_argument("--batch", type=int, default=2000)

    def handle(self, *args, **opts):
        batch = opts["batch"]

        qs = Cargaison.objects.all().order_by("idcargaison")
        last_id = 0

        while True:
            ids = list(
                qs.filter(idcargaison__gt=last_id)
                  .values_list("idcargaison", flat=True)[:batch]
            )
            if not ids:
                break

            # 1) names (join only inside this chunk)
            rows = (
                Cargaison.objects.filter(idcargaison__in=ids)
                .select_related("importateur", "entrepot", "produit", "frontiere")
                .only(
                    "idcargaison",
                    "importateur__nomimportateur",
                    "entrepot__nomentrepot",
                    "produit__nomproduit",
                    "frontiere__nomville",
                )
            )
            upd = []
            for c in rows:
                c.nom_importateur = c.importateur.nomimportateur if c.importateur_id else None
                c.nom_entrepot = c.entrepot.nomentrepot if c.entrepot_id else None
                c.nom_produit = c.produit.nomproduit if c.produit_id else None
                c.nom_frontiere = c.frontiere.nomville if c.frontiere_id else None
                upd.append(c)

            Cargaison.objects.bulk_update(
                upd,
                ["nom_importateur", "nom_entrepot", "nom_produit", "nom_frontiere"],
                batch_size=batch
            )

            # 2) date_echantillon
            ee_map = dict(
                Entrepot_echantillon.objects.filter(idcargaison_id__in=ids)
                .values_list("idcargaison_id", "dateechantillonage")
            )
            if ee_map:
                to_upd = []
                for cid, dt in ee_map.items():
                    to_upd.append(Cargaison(idcargaison=cid, date_echantillon=dt))
                Cargaison.objects.bulk_update(to_upd, ["date_echantillon"], batch_size=batch)

            # 3) date_reception_labo + num_certificat_qualite + code_labo
            lr_rows = (
                LaboReception.objects.filter(idcargaison__idcargaison_id__in=ids)
                .values_list("idcargaison__idcargaison_id", "datereceptionlabo", "numcertificatqualite", "codelabo")
            )
            if lr_rows:
                to_upd = [
                    Cargaison(
                        idcargaison=cid,
                        date_reception_labo=dt,
                        num_certificat_qualite=ncq,
                        code_labo=cl
                    )
                    for cid, dt, ncq, cl in lr_rows
                ]
                Cargaison.objects.bulk_update(
                    to_upd, ["date_reception_labo", "num_certificat_qualite", "code_labo"],
                    batch_size=batch
                )

            # 4) date_analyse
            res_rows = (
                Resultat.objects.filter(idcargaison__idcargaison__idcargaison_id__in=ids)
                .values_list("idcargaison__idcargaison__idcargaison_id", "dateanalyse")
            )
            res_map = dict(res_rows)
            if res_map:
                to_upd = [Cargaison(idcargaison=cid, date_analyse=dt) for cid, dt in res_map.items()]
                Cargaison.objects.bulk_update(to_upd, ["date_analyse"], batch_size=batch)

            # 5) date_inspection + dens/temp
            insp_rows = (
                Inspection.objects.filter(idcargaison_id__in=ids)
                .values_list("idcargaison_id", "dateinspection", "dens", "temp")
            )
            if insp_rows:
                to_upd = [
                    Cargaison(
                        idcargaison=cid,
                        date_inspection=dt,
                        densite_inspection=dens,
                        temperature_inspection=temp
                    )
                    for cid, dt, dens, temp in insp_rows
                ]
                Cargaison.objects.bulk_update(
                    to_upd, ["date_inspection", "densite_inspection", "temperature_inspection"],
                    batch_size=batch
                )

            # 6) totals (aggregate per cargaison in this chunk)
            agg = (
                Compartiment.objects
                .filter(idinspection__idcargaison_id__in=ids)
                .values("idinspection__idcargaison_id")
                .annotate(
                    gov=Sum("gov"),
                    gsv=Sum("gsv"),
                    mta=Sum("mta"),
                    mtv=Sum("mtv"),
                )
            )
            if agg:
                to_upd = []
                for r in agg:
                    cid = r["idinspection__idcargaison_id"]
                    to_upd.append(Cargaison(
                        idcargaison=cid,
                        gov_total=r["gov"] or 0.0,
                        gsv_total=r["gsv"] or 0.0,
                        mta_total=r["mta"] or 0.0,
                        mtv_total=r["mtv"] or 0.0,
                    ))
                Cargaison.objects.bulk_update(
                    to_upd, ["gov_total", "gsv_total", "mta_total", "mtv_total"], batch_size=batch
                )

            last_id = ids[-1]
            self.stdout.write(f"✅ updated up to idcargaison={last_id}")

        self.stdout.write(self.style.SUCCESS("✅ Backfill complete"))