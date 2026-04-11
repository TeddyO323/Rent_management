from django.test import TestCase
from django.urls import reverse

from .models import Property, User


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            email="landlord.demo@smartrent.local",
            password="DemoPass123!",
            full_name="Demo Landlord",
            role=User.Role.LANDLORD,
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Landlord Sign In")

    def test_landlord_can_log_in(self):
        response = self.client.post(
            reverse("login"),
            {"email": self.landlord.email, "password": "DemoPass123!"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-page="overview"', html=False)

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("landlord-dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_tenant_account_is_blocked_from_landlord_dashboard(self):
        tenant = User.objects.create_user(
            email="tenant.demo@smartrent.local",
            password="DemoPass123!",
            full_name="Demo Tenant",
            role=User.Role.TENANT,
        )
        self.client.force_login(tenant)
        response = self.client.get(reverse("landlord-dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_landlord_can_create_property_and_see_it_on_properties_page(self):
        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("landlord-add-property"),
            {
                "name": "Demo Heights",
                "location": "Kileleshwa, Nairobi",
                "units": 24,
                "occupied_units": 21,
                "monthly_revenue": "720000.00",
                "status": "Stable",
                "trend": "4.8",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Property.objects.filter(name="Demo Heights", landlord=self.landlord).exists())
        self.assertContains(response, "Demo Heights")
