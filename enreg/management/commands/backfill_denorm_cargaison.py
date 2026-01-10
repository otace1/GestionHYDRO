from django.core.management.base import BaseCommand
from enreg.tasks import backfill_denorm_cargaison_task

class Command(BaseCommand):
    help = "Backfill denormalized fields on Cargaison (batched)"

    def add_arguments(self, parser):
        parser.add_argument("--batch", type=int, default=2000)
        parser.add_argument("--async", action="store_true", help="Run as Celery task")

    def handle(self, *args, **opts):
        batch = opts["batch"]
        is_async = opts["async"]

        if is_async:
            self.stdout.write("🚀 Dispatching backfill task to Celery...")
            backfill_denorm_cargaison_task.delay(batch=batch)
            self.stdout.write(self.style.SUCCESS("✅ Task dispatched"))
        else:
            self.stdout.write("Running backfill synchronously...")
            backfill_denorm_cargaison_task(batch=batch)
            self.stdout.write(self.style.SUCCESS("✅ Backfill complete"))