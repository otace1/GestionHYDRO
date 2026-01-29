from django.test import TestCase, Client
from django.utils import timezone
from enreg.models import Cargaison, Produit, Importateur, Ville, Entrepot
from django.urls import reverse
from datetime import datetime, date
import json
from ads.utils import get_current_year, get_current_year_range

class KPIYearFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create necessary related models
        self.produit = Produit.objects.create(idproduit=1, nomproduit="MOGAS")
        self.importateur = Importateur.objects.create(idimportateur=1, nomimportateur="Test Importer")
        self.ville = Ville.objects.create(idville=1, nomville="Test City")
        self.entrepot = Entrepot.objects.create(identrepot=1, nomentrepot="Test Entrepot", ville=self.ville)
        
        # We need a user to login
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='admin', password='password', is_staff=True)
        # Mock role_id if needed, as Dashboard.chartjs checks role_id
        # Based on ads/views.py:50, it uses user.role_id
        self.user.role_id = 1
        self.user.save()
        self.client.login(username='admin', password='password')

        current_year = get_current_year()
        last_year = current_year - 1
        next_year = current_year + 1

        # Create records for current year
        Cargaison.objects.create(
            idcargaison=1,
            dateheurecargaison=timezone.make_aware(datetime(current_year, 1, 15)),
            produit=self.produit,
            importateur=self.importateur,
            entrepot=self.entrepot,
            volume=100,
            etat="En attente requisition"
        )
        
        # Create records for last year (should be filtered out)
        Cargaison.objects.create(
            idcargaison=2,
            dateheurecargaison=timezone.make_aware(datetime(last_year, 12, 15)),
            produit=self.produit,
            importateur=self.importateur,
            entrepot=self.entrepot,
            volume=200,
            etat="En attente requisition"
        )

        # Create records for next year (should be filtered out by end-exclusive range)
        Cargaison.objects.create(
            idcargaison=3,
            dateheurecargaison=timezone.make_aware(datetime(next_year, 1, 1)),
            produit=self.produit,
            importateur=self.importateur,
            entrepot=self.entrepot,
            volume=300,
            etat="En attente requisition"
        )

    def test_get_current_year_range(self):
        start, end = get_current_year_range()
        current_year = get_current_year()
        self.assertEqual(start, date(current_year, 1, 1))
        self.assertEqual(end, date(current_year + 1, 1, 1))

    def test_kpi_status_counts_filter_by_year(self):
        response = self.client.post(reverse('kpiStatusCounts'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        # Should only count the one from current year (idcargaison=1)
        # last year (idcargaison=2) and next year (idcargaison=3) should be excluded
        self.assertEqual(data['attente_requisition'], 1)

    def test_product_count_filter_by_year(self):
        response = self.client.post(reverse('productCount'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        # Should only count the one from current year
        self.assertEqual(data['mogasCount'], 1)

    def test_top_importers_filter_by_year(self):
        response = self.client.post(reverse('topImporters'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        # Should only sum volume from current year (100)
        self.assertEqual(len(data), 1)
        self.assertEqual(float(data[0]['total_volume']), 100.0)

    def test_last_records_filter_by_year(self):
        response = self.client.post(reverse('lastRecords'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)['data']
        # Should only include current year record
        self.assertEqual(len(data), 1)
        # Check that it is the one from current year
        self.assertTrue(str(get_current_year()) in data[0]['dateheurecargaison'])

    def test_dashboard_chartjs_filter_by_year(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # Check volume in context - should only include idcargaison=1 (100.0)
        self.assertEqual(response.context['totalVolume'], 100.0)
        self.assertEqual(response.context['gasoilVolume'], 0.0)
        self.assertEqual(response.context['mogasVolume'], 100.0)
        self.assertEqual(response.context['current_year'], get_current_year())
