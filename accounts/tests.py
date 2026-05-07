from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from .models import Bill, Complaint, LeaseExtensionRequest, MaintenanceExpense, Notification, Payment, PaymentAllocation, Property, PropertyUnit, PropertyUnitType, Tenant, User


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            email="landlord.demo@smartrent.local",
            password="DemoPass123!",
            full_name="Demo Landlord",
            role=User.Role.LANDLORD,
        )
        self.property = Property.objects.create(
            landlord=self.landlord,
            name="Existing Place",
            location="Kilimani, Nairobi",
            units=10,
            occupied_units=0,
            monthly_revenue=0,
            occupancy=0,
            status="Stable",
            trend=2.1,
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account Sign In")

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

    def test_landlord_can_save_persistent_settings(self):
        self.client.force_login(self.landlord)

        profile_response = self.client.post(
            reverse("landlord-settings"),
            {
                "form_action": "profile",
                "business_name": "SmartRent Management",
                "support_email": "ops@smartrent.local",
                "support_phone": "+254700100200",
            },
            follow=True,
        )
        automation_response = self.client.post(
            reverse("landlord-settings"),
            {
                "form_action": "automation",
                "owner_digest_enabled": "on",
                "weekly_report_enabled": "on",
                "maintenance_escalation_enabled": "on",
                "rent_reminder_days": "7",
                "overdue_follow_up_days": "3",
                "maintenance_escalation_hours": "12",
            },
            follow=True,
        )

        settings_obj = self.landlord.landlord_settings
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(automation_response.status_code, 200)
        self.assertEqual(settings_obj.business_name, "SmartRent Management")
        self.assertEqual(settings_obj.support_email, "ops@smartrent.local")
        self.assertEqual(settings_obj.support_phone, "+254700100200")
        self.assertEqual(settings_obj.rent_reminder_days, 7)
        self.assertEqual(settings_obj.overdue_follow_up_days, 3)
        self.assertEqual(settings_obj.maintenance_escalation_hours, 12)
        self.assertTrue(settings_obj.owner_digest_enabled)

    def test_landlord_analytics_uses_live_data_context(self):
        tenant_user = User.objects.create_user(
            email="analytics@example.com",
            password="DemoPass123!",
            full_name="Analytics Tenant",
            role=User.Role.TENANT,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 33",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Analytics Tenant",
            email="analytics@example.com",
            phone="+254700000023",
            id_number="63636363",
            unit_number="House 33",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            autopay_enabled=True,
            security_deposit="70000.00",
        )
        Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Water bill",
            category=Bill.Category.WATER,
            amount="5000.00",
            remaining_amount="2000.00",
            status=Bill.Status.PARTIALLY_PAID,
            due_date=timezone.localdate(),
        )
        Complaint.objects.create(
            tenant=tenant,
            title="Leaking sink",
            category=Complaint.Category.PLUMBING,
            description="Kitchen sink is leaking.",
        )
        Payment.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            method=Payment.Method.MPESA,
            status=Payment.Status.CONFIRMED,
            scope=Payment.Scope.ALL,
            amount="3000.00",
            paid_on=timezone.localdate(),
        )

        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-analytics"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("analytics_dashboard_data", response.context)
        analytics_data = response.context["analytics_dashboard_data"]
        self.assertEqual(analytics_data["metrics"][0]["label"], "Collection Rate")
        self.assertGreaterEqual(analytics_data["metrics"][1]["value"], 100.0)
        self.assertIn("Plumbing", analytics_data["maintenanceCategories"]["labels"])

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
                "status": "Stable",
                "trend": "4.8",
                "unit_types-TOTAL_FORMS": "2",
                "unit_types-INITIAL_FORMS": "0",
                "unit_types-MIN_NUM_FORMS": "0",
                "unit_types-MAX_NUM_FORMS": "1000",
                "unit_types-0-unit_type": "1 Bedroom",
                "unit_types-0-unit_count": "10",
                "unit_types-0-renting_price": "35000.00",
                "unit_types-0-buying_price": "6200000.00",
                "unit_types-1-unit_type": "2 Bedroom",
                "unit_types-1-unit_count": "6",
                "unit_types-1-renting_price": "52000.00",
                "unit_types-1-buying_price": "9100000.00",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Property.objects.filter(name="Demo Heights", landlord=self.landlord).exists())
        self.assertEqual(Property.objects.get(name="Demo Heights").units, 16)
        self.assertEqual(Property.objects.get(name="Demo Heights").occupied_units, 0)
        self.assertEqual(Property.objects.get(name="Demo Heights").monthly_revenue, 0)
        self.assertEqual(PropertyUnitType.objects.filter(property__name="Demo Heights").count(), 2)
        self.assertContains(response, "Demo Heights")

    def test_landlord_can_view_property_detail(self):
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-property-detail", args=[self.property.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Existing Place")

    def test_landlord_can_delete_property(self):
        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("landlord-delete-property", args=[self.property.id]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Property.objects.filter(id=self.property.id).exists())

    def test_landlord_can_add_rental_tenant_from_available_unit(self):
        self.client.force_login(self.landlord)
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 1",
        )

        response = self.client.post(
            reverse("landlord-add-tenant"),
            {
                "property": str(self.property.id),
                "unit_type": "1 Bedroom",
                "property_unit": str(unit.id),
                "full_name": "Brian Mwangi",
                "email": "brian@example.com",
                "phone": "+254700000001",
                "id_number": "12345678",
                "lease_type": Tenant.LeaseType.RENT,
                "lease_start": "2026-04-01",
                "lease_end": "2027-03-31",
                "security_deposit": "70000.00",
                "emergency_contact_name": "",
                "emergency_contact_phone": "",
                "emergency_contact_relationship": "",
                "occupation": "Engineer",
                "status": Tenant.Status.GOOD_STANDING,
                "risk_level": Tenant.RiskLevel.LOW,
                "notes": "",
            },
            follow=True,
        )

        tenant = Tenant.objects.get(full_name="Brian Mwangi")
        unit.refresh_from_db()
        self.property.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tenant.monthly_rent, Decimal("35000.00"))
        self.assertIsNone(tenant.purchase_price)
        self.assertTrue(unit.is_occupied)
        self.assertEqual(self.property.occupied_units, 1)

    def test_landlord_can_add_purchase_occupant_from_available_unit(self):
        self.client.force_login(self.landlord)
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="2 Bedroom",
            unit_count=1,
            renting_price="52000.00",
            buying_price="9100000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 2",
        )

        response = self.client.post(
            reverse("landlord-add-tenant"),
            {
                "property": str(self.property.id),
                "unit_type": "2 Bedroom",
                "property_unit": str(unit.id),
                "full_name": "Naomi Wanjiku",
                "email": "naomi@example.com",
                "phone": "+254700000002",
                "id_number": "87654321",
                "lease_type": Tenant.LeaseType.PURCHASE,
                "lease_start": "2026-04-01",
                "lease_end": "",
                "security_deposit": "0.00",
                "emergency_contact_name": "",
                "emergency_contact_phone": "",
                "emergency_contact_relationship": "",
                "occupation": "Designer",
                "status": Tenant.Status.GOOD_STANDING,
                "risk_level": Tenant.RiskLevel.LOW,
                "notes": "",
            },
            follow=True,
        )

        tenant = Tenant.objects.get(full_name="Naomi Wanjiku")
        unit.refresh_from_db()
        self.property.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tenant.purchase_price, Decimal("9100000.00"))
        self.assertIsNone(tenant.monthly_rent)
        self.assertIsNone(tenant.lease_end)
        self.assertTrue(unit.is_occupied)
        self.assertEqual(self.property.monthly_revenue, 0)

    def test_landlord_adding_tenant_creates_tenant_login_account(self):
        self.client.force_login(self.landlord)
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 13",
        )

        response = self.client.post(
            reverse("landlord-add-tenant"),
            {
                "property": str(self.property.id),
                "unit_type": "1 Bedroom",
                "property_unit": str(unit.id),
                "full_name": "Grace Wairimu",
                "email": "grace@example.com",
                "phone": "+254700000003",
                "id_number": "11223344",
                "lease_type": Tenant.LeaseType.RENT,
                "lease_start": "2026-04-01",
                "lease_end": "2027-03-31",
                "security_deposit": "70000.00",
                "emergency_contact_name": "",
                "emergency_contact_phone": "",
                "emergency_contact_relationship": "",
                "occupation": "Analyst",
                "status": Tenant.Status.GOOD_STANDING,
                "risk_level": Tenant.RiskLevel.LOW,
                "notes": "",
            },
            follow=True,
        )

        tenant = Tenant.objects.get(email="grace@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(tenant.user)
        self.assertEqual(tenant.user.email, "grace@example.com")
        self.assertTrue(tenant.user.password_change_required)
        self.assertTrue(tenant.user.check_password("Existing-Place-House-13"))
        self.assertContains(response, "Existing-Place-House-13")

    def test_tenant_login_redirects_to_tenant_panel_and_password_change_clears_prompt(self):
        tenant_user = User.objects.create_user(
            email="tenant.panel@example.com",
            password="Existing-Place-House-7",
            full_name="Tenant Panel",
            role=User.Role.TENANT,
            password_change_required=True,
        )
        tenant_property = Property.objects.create(
            landlord=self.landlord,
            name="Existing Place",
            location="Kilimani, Nairobi",
            units=1,
            occupied_units=1,
            monthly_revenue=35000,
            occupancy=100,
            status="Stable",
            trend=2.1,
        )
        unit_type = PropertyUnitType.objects.create(
            property=tenant_property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=tenant_property,
            unit_type=unit_type,
            unit_number="House 7",
            is_occupied=True,
        )
        Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=tenant_property,
            property_unit=unit,
            full_name="Tenant Panel",
            email=tenant_user.email,
            phone="+254700000004",
            id_number="99887766",
            unit_number="House 7",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        login_response = self.client.post(
            reverse("login"),
            {"email": tenant_user.email, "password": "Existing-Place-House-7"},
            follow=True,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "Tenant Panel")
        self.assertContains(login_response, "Please change your password")

        settings_response = self.client.post(
            reverse("tenant-settings"),
            {
                "old_password": "Existing-Place-House-7",
                "new_password1": "BrandNewPass123!",
                "new_password2": "BrandNewPass123!",
            },
            follow=True,
        )
        tenant_user.refresh_from_db()
        self.assertEqual(settings_response.status_code, 200)
        self.assertFalse(tenant_user.password_change_required)
        self.assertNotContains(settings_response, "Please change your password")

    def test_tenant_can_update_profile_details(self):
        tenant_user = User.objects.create_user(
            email="tenant.profile@example.com",
            password="Existing-Place-House-34",
            full_name="Tenant Profile",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        tenant_property = Property.objects.create(
            landlord=self.landlord,
            name="Existing Place",
            location="Kilimani, Nairobi",
            units=1,
            occupied_units=1,
            monthly_revenue=35000,
            occupancy=100,
            status="Stable",
            trend=2.1,
        )
        unit_type = PropertyUnitType.objects.create(
            property=tenant_property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=tenant_property,
            unit_type=unit_type,
            unit_number="House 34",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=tenant_property,
            property_unit=unit,
            full_name="Tenant Profile",
            email=tenant_user.email,
            phone="+254700000024",
            id_number="90901122",
            unit_number="House 34",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-profile"),
            {
                "full_name": "Tenant Profile Updated",
                "phone": "+254799000111",
                "id_number": "12312312",
                "occupation": "Architect",
                "emergency_contact_name": "Jane Profile",
                "emergency_contact_phone": "+254711222333",
                "emergency_contact_relationship": "Sibling",
            },
            follow=True,
        )

        tenant.refresh_from_db()
        tenant_user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tenant.full_name, "Tenant Profile Updated")
        self.assertEqual(tenant.phone, "+254799000111")
        self.assertEqual(tenant.occupation, "Architect")
        self.assertEqual(tenant.emergency_contact_name, "Jane Profile")
        self.assertEqual(tenant_user.full_name, "Tenant Profile Updated")
        self.assertContains(response, "updated successfully")

    def test_legacy_tenant_without_user_can_log_in_and_gets_account_backfilled(self):
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 5",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            property=self.property,
            property_unit=unit,
            full_name="Legacy Tenant",
            email="legacy@example.com",
            phone="+254700000007",
            id_number="10101010",
            unit_number="House 5",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        response = self.client.post(
            reverse("login"),
            {"email": "legacy@example.com", "password": "Existing-Place-House-5"},
            follow=True,
        )
        tenant.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(tenant.user)
        self.assertContains(response, "Tenant Panel")

    def test_tenant_can_submit_lease_extension_request(self):
        tenant_user = User.objects.create_user(
            email="extension@example.com",
            password="Existing-Place-House-11",
            full_name="Extension Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 11",
            is_occupied=True,
        )
        Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Extension Tenant",
            email=tenant_user.email,
            phone="+254700000008",
            id_number="11112222",
            unit_number="House 11",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-receipts"),
            {
                "requested_end_date": "2027-09-30",
                "reason": "I would like to remain in the unit for another six months.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LeaseExtensionRequest.objects.count(), 1)
        self.assertContains(response, "submitted")

    def test_landlord_can_approve_lease_extension_and_tenant_sees_update(self):
        tenant_user = User.objects.create_user(
            email="extension-approval@example.com",
            password="Existing-Place-House-31",
            full_name="Extension Approval Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 31",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Extension Approval Tenant",
            email=tenant_user.email,
            phone="+254700000021",
            id_number="41414141",
            unit_number="House 31",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            status=Tenant.Status.RENEWING_SOON,
            security_deposit="70000.00",
        )
        extension_request = LeaseExtensionRequest.objects.create(
            tenant=tenant,
            requested_end_date="2027-09-30",
            reason="Need six more months in the same unit.",
        )

        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("landlord-extension-request-detail", args=[extension_request.id]),
            {
                "status": LeaseExtensionRequest.Status.APPROVED,
                "landlord_notes": "Approved for another six months.",
            },
            follow=True,
        )

        extension_request.refresh_from_db()
        tenant.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(extension_request.status, LeaseExtensionRequest.Status.APPROVED)
        self.assertEqual(extension_request.landlord_notes, "Approved for another six months.")
        self.assertEqual(str(tenant.lease_end), "2027-09-30")
        self.assertEqual(tenant.status, Tenant.Status.GOOD_STANDING)

        self.client.force_login(tenant_user)
        tenant_response = self.client.get(reverse("tenant-receipts"))
        self.assertEqual(tenant_response.status_code, 200)
        self.assertContains(tenant_response, "Approved")
        self.assertContains(tenant_response, "Approved for another six months.")

    def test_landlord_overview_uses_live_portfolio_signals(self):
        tenant_user = User.objects.create_user(
            email="overviewlive@example.com",
            password="Existing-Place-House-32",
            full_name="Overview Live Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 32",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Overview Live Tenant",
            email=tenant_user.email,
            phone="+254700000022",
            id_number="52525252",
            unit_number="House 32",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Water bill",
            category=Bill.Category.WATER,
            amount="5000.00",
            remaining_amount="5000.00",
            due_date=timezone.localdate(),
        )
        LeaseExtensionRequest.objects.create(
            tenant=tenant,
            requested_end_date=timezone.localdate() + timedelta(days=500),
            reason="Requesting an early renewal decision.",
        )

        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-overview"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Action board")
        self.assertContains(response, "Lease extension requests waiting")
        self.assertContains(response, "Overdue balances are open")
        self.assertContains(response, "Overview Live Tenant")
        self.assertContains(response, "overview-dashboard-data")

    def test_tenant_can_log_complaint(self):
        tenant_user = User.objects.create_user(
            email="complaint@example.com",
            password="Existing-Place-House-12",
            full_name="Complaint Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 12",
            is_occupied=True,
        )
        Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Complaint Tenant",
            email=tenant_user.email,
            phone="+254700000009",
            id_number="33334444",
            unit_number="House 12",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-complaints"),
            {
                "title": "Broken window latch",
                "category": Complaint.Category.WINDOWS,
                "description": "The bedroom window latch is broken and the window does not close properly.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 1)
        self.assertEqual(Complaint.objects.first().status, Complaint.Status.PENDING)
        self.assertContains(response, "logged successfully")

    def test_landlord_can_update_complaint_status_and_notes(self):
        tenant_user = User.objects.create_user(
            email="maintstatus@example.com",
            password="Existing-Place-House-27",
            full_name="Maintenance Status Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 27",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Maintenance Status Tenant",
            email="maintstatus@example.com",
            phone="+254700000019",
            id_number="78781212",
            unit_number="House 27",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        complaint = Complaint.objects.create(
            tenant=tenant,
            title="Power outage in kitchen",
            category=Complaint.Category.ELECTRICITY,
            description="The kitchen sockets are not working.",
        )

        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("landlord-complaint-detail", args=[complaint.id]),
            {
                "status": Complaint.Status.IN_PROGRESS,
                "landlord_notes": "Electrician scheduled for tomorrow morning.",
            },
            follow=True,
        )
        complaint.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(complaint.status, Complaint.Status.IN_PROGRESS)
        self.assertEqual(complaint.landlord_notes, "Electrician scheduled for tomorrow morning.")

    def test_landlord_can_add_management_expense_without_creating_tenant_bill(self):
        tenant_user = User.objects.create_user(
            email="maintenanceexpense@example.com",
            password="Existing-Place-House-29",
            full_name="Maintenance Expense Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 29",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Maintenance Expense Tenant",
            email="maintenanceexpense@example.com",
            phone="+254700000021",
            id_number="21212121",
            unit_number="House 29",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        complaint = Complaint.objects.create(
            tenant=tenant,
            title="Burst pipe",
            category=Complaint.Category.PLUMBING,
            description="Water is leaking in the kitchen.",
        )

        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("landlord-complaint-detail", args=[complaint.id]),
            {
                "form_action": "expense",
                "title": "Emergency plumber callout",
                "amount": "12000.00",
                "cost_bearer": MaintenanceExpense.CostBearer.MANAGEMENT,
                "notes": "Management is covering this plumbing repair.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MaintenanceExpense.objects.count(), 1)
        self.assertEqual(Bill.objects.filter(tenant=tenant, category=Bill.Category.REPAIRS).count(), 0)

    def test_landlord_can_add_tenant_expense_and_create_repair_bill(self):
        tenant_user = User.objects.create_user(
            email="tenantexpense@example.com",
            password="Existing-Place-House-30",
            full_name="Tenant Expense Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 30",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Tenant Expense Tenant",
            email="tenantexpense@example.com",
            phone="+254700000022",
            id_number="31313131",
            unit_number="House 30",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        complaint = Complaint.objects.create(
            tenant=tenant,
            title="Broken window panel",
            category=Complaint.Category.WINDOWS,
            description="The window panel cracked after impact damage.",
        )

        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("landlord-complaint-detail", args=[complaint.id]),
            {
                "form_action": "expense",
                "title": "Replacement window panel",
                "amount": "9500.00",
                "cost_bearer": MaintenanceExpense.CostBearer.TENANT,
                "notes": "Tenant is responsible for accidental damage.",
            },
            follow=True,
        )

        expense = MaintenanceExpense.objects.get()
        bill = Bill.objects.get(tenant=tenant, category=Bill.Category.REPAIRS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expense.bill, bill)
        self.assertEqual(bill.amount, Decimal("9500.00"))
        self.assertContains(response, "tenant repair bill was created")

    def test_tenant_complaints_page_shows_rejected_status_and_landlord_note(self):
        tenant_user = User.objects.create_user(
            email="rejectedcomplaint@example.com",
            password="Existing-Place-House-28",
            full_name="Rejected Complaint Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 28",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Rejected Complaint Tenant",
            email="rejectedcomplaint@example.com",
            phone="+254700000020",
            id_number="89898989",
            unit_number="House 28",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        Complaint.objects.create(
            tenant=tenant,
            title="Wall repaint request",
            category=Complaint.Category.OTHER,
            description="Please repaint the sitting room walls.",
            status=Complaint.Status.REJECTED,
            landlord_notes="This request falls under aesthetic customization and is not covered by maintenance.",
        )

        self.client.force_login(tenant_user)
        response = self.client.get(reverse("tenant-complaints"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rejected")
        self.assertContains(response, "aesthetic customization")

    def test_tenant_can_view_complaint_detail_with_linked_repair_bill(self):
        tenant_user = User.objects.create_user(
            email="complaintdetail@example.com",
            password="Existing-Place-House-31",
            full_name="Complaint Detail Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 31",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Complaint Detail Tenant",
            email="complaintdetail@example.com",
            phone="+254700000024",
            id_number="41414141",
            unit_number="House 31",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        complaint = Complaint.objects.create(
            tenant=tenant,
            title="Broken wardrobe hinge",
            category=Complaint.Category.OTHER,
            description="The wardrobe hinge came off.",
            status=Complaint.Status.IN_PROGRESS,
            landlord_notes="Carpenter scheduled for tomorrow.",
        )
        bill = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Maintenance expense: Wardrobe hinge replacement",
            category=Bill.Category.REPAIRS,
            amount="2500.00",
            remaining_amount="2500.00",
            due_date=timezone.localdate(),
        )
        MaintenanceExpense.objects.create(
            complaint=complaint,
            landlord=self.landlord,
            bill=bill,
            title="Wardrobe hinge replacement",
            amount="2500.00",
            cost_bearer=MaintenanceExpense.CostBearer.TENANT,
            notes="Tenant damage confirmed.",
        )

        self.client.force_login(tenant_user)
        response = self.client.get(reverse("tenant-complaint-detail", args=[complaint.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carpenter scheduled for tomorrow.")
        self.assertContains(response, "Maintenance expense: Wardrobe hinge replacement")

    def test_notifications_are_created_for_complaint_submission(self):
        tenant_user = User.objects.create_user(
            email="notifcomplaint@example.com",
            password="Existing-Place-House-32",
            full_name="Notification Complaint Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 32",
            is_occupied=True,
        )
        Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Notification Complaint Tenant",
            email="notifcomplaint@example.com",
            phone="+254700000025",
            id_number="51515151",
            unit_number="House 32",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-complaints"),
            {
                "title": "Water meter leak",
                "category": Complaint.Category.PLUMBING,
                "description": "The meter area is leaking.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Notification.objects.filter(recipient=tenant_user, title="Complaint logged").exists())
        self.assertTrue(Notification.objects.filter(recipient=self.landlord, title="New complaint submitted").exists())

    def test_tenant_notifications_page_and_mark_read_work(self):
        tenant_user = User.objects.create_user(
            email="notifpage@example.com",
            password="Existing-Place-House-34",
            full_name="Notification Page Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 34",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Notification Page Tenant",
            email="notifpage@example.com",
            phone="+254700000026",
            id_number="61616161",
            unit_number="House 34",
            lease_start=timezone.localdate() - timedelta(days=25),
            lease_end=timezone.localdate() + timedelta(days=15),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        Notification.objects.create(
            recipient=tenant_user,
            tenant=tenant,
            property=self.property,
            category=Notification.Category.PAYMENTS,
            priority=Notification.Priority.HIGH,
            title="Test payment alert",
            message="A payment issue needs your attention.",
        )

        self.client.force_login(tenant_user)
        response = self.client.get(reverse("tenant-notifications"))
        notification = Notification.objects.filter(recipient=tenant_user, title="Test payment alert").first()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test payment alert")

        mark_response = self.client.post(
            reverse("tenant-mark-notification-read", args=[notification.id]),
            {"next": reverse("tenant-notifications")},
            follow=True,
        )
        notification.refresh_from_db()
        self.assertEqual(mark_response.status_code, 200)
        self.assertTrue(notification.is_read)

    def test_landlord_can_record_payment(self):
        self.client.force_login(self.landlord)
        tenant_user = User.objects.create_user(
            email="payment@example.com",
            password="DemoPass123!",
            full_name="Payment Tenant",
            role=User.Role.TENANT,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 16",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Payment Tenant",
            email="payment@example.com",
            phone="+254700000010",
            id_number="55556666",
            unit_number="House 16",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            current_balance="0.00",
            security_deposit="70000.00",
        )
        bill = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="April rent",
            category=Bill.Category.RENT,
            amount="10000.00",
            remaining_amount="10000.00",
            due_date="2026-04-30",
        )
        response = self.client.post(
            reverse("landlord-record-payment"),
            {
                "tenant": str(tenant.id),
                "property": str(self.property.id),
                "method": Payment.Method.MPESA,
                "amount": "7500.00",
                "paid_on": "2026-04-11",
                "notes": "M-Pesa receipt",
            },
            follow=True,
        )
        bill.refresh_from_db()
        tenant.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(bill.remaining_amount, Decimal("2500.00"))
        self.assertEqual(tenant.current_balance, Decimal("0.00"))

    def test_landlord_can_add_bill(self):
        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("landlord-add-bill"),
            {
                "property": str(self.property.id),
                "tenant": "",
                "title": "April service charge",
                "category": Bill.Category.SERVICE_CHARGE,
                "amount": "6500.00",
                "due_date": "2026-04-30",
                "status": Bill.Status.UNPAID,
                "notes": "Property-wide bill",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bill.objects.count(), 1)
        self.assertContains(response, "April service charge")

    def test_overpayment_becomes_credit_and_reduces_next_bill(self):
        self.client.force_login(self.landlord)
        tenant_user = User.objects.create_user(
            email="credit@example.com",
            password="DemoPass123!",
            full_name="Credit Tenant",
            role=User.Role.TENANT,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 18",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Credit Tenant",
            email="credit@example.com",
            phone="+254700000011",
            id_number="77778888",
            unit_number="House 18",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        bill = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="April service charge",
            category=Bill.Category.SERVICE_CHARGE,
            amount="10000.00",
            remaining_amount="10000.00",
            due_date="2026-04-30",
        )
        self.client.post(
            reverse("landlord-record-payment"),
            {
                "tenant": str(tenant.id),
                "property": str(self.property.id),
                "method": Payment.Method.MPESA,
                "amount": "14000.00",
                "paid_on": "2026-04-11",
                "notes": "Overpayment",
            },
            follow=True,
        )
        bill.refresh_from_db()
        tenant.refresh_from_db()
        self.assertEqual(bill.remaining_amount, Decimal("0.00"))
        self.assertEqual(tenant.current_balance, Decimal("4000.00"))

        response = self.client.post(
            reverse("landlord-add-bill"),
            {
                "property": str(self.property.id),
                "tenant": str(tenant.id),
                "title": "May service charge",
                "category": Bill.Category.SERVICE_CHARGE,
                "amount": "10000.00",
                "due_date": "2026-05-31",
                "status": Bill.Status.UNPAID,
                "notes": "",
            },
            follow=True,
        )
        new_bill = Bill.objects.get(title="May service charge")
        tenant.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(new_bill.remaining_amount, Decimal("6000.00"))
        self.assertEqual(new_bill.status, Bill.Status.PARTIALLY_PAID)
        self.assertEqual(tenant.current_balance, Decimal("0.00"))

    def test_rent_bill_is_generated_automatically_for_rental_tenant(self):
        tenant_user = User.objects.create_user(
            email="autorent@example.com",
            password="Existing-Place-House-20",
            full_name="Auto Rent Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 20",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Auto Rent Tenant",
            email="autorent@example.com",
            phone="+254700000012",
            id_number="90909090",
            unit_number="House 20",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            last_rent_charge_at=timezone.now() - timedelta(days=31),
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        self.client.force_login(tenant_user)
        response = self.client.get(reverse("tenant-overview"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bill.objects.filter(tenant=tenant, category=Bill.Category.RENT).count(), 1)
        self.assertContains(response, "Auto Rent Tenant")

    def test_autopay_pays_generated_rent_bill_only(self):
        tenant_user = User.objects.create_user(
            email="autopayrent@example.com",
            password="Existing-Place-House-21",
            full_name="Autopay Rent Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 21",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Autopay Rent Tenant",
            email="autopayrent@example.com",
            phone="+254700000013",
            id_number="78787878",
            unit_number="House 21",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            last_rent_charge_at=timezone.now() - timedelta(days=31),
            monthly_rent="35000.00",
            autopay_enabled=True,
            autopay_bank_name="Demo Bank",
            autopay_account_number="1234567890",
            security_deposit="70000.00",
        )

        self.client.force_login(tenant_user)
        response = self.client.get(reverse("tenant-overview"))
        rent_bill = Bill.objects.get(tenant=tenant, category=Bill.Category.RENT)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(rent_bill.status, Bill.Status.PAID)
        self.assertEqual(rent_bill.remaining_amount, Decimal("0.00"))
        self.assertEqual(Payment.objects.filter(tenant=tenant).count(), 1)

    def test_tenant_can_enable_autopay_from_settings_and_pay_open_rent_bill(self):
        tenant_user = User.objects.create_user(
            email="settings-autopay@example.com",
            password="Existing-Place-House-22",
            full_name="Settings Autopay Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 22",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Settings Autopay Tenant",
            email="settings-autopay@example.com",
            phone="+254700000014",
            id_number="56565656",
            unit_number="House 22",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        rent_bill = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Open rent charge",
            category=Bill.Category.RENT,
            amount="35000.00",
            remaining_amount="35000.00",
            due_date=timezone.localdate(),
        )
        service_bill = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Open service charge",
            category=Bill.Category.SERVICE_CHARGE,
            amount="10000.00",
            remaining_amount="10000.00",
            due_date=timezone.localdate(),
        )

        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-settings"),
            {
                "form_action": "autopay",
                "autopay_enabled": "on",
                "autopay_bank_name": "Demo Bank",
                "autopay_account_holder": "Settings Tenant",
                "autopay_account_number": "90807060",
                "autopay_card_number": "4111111111111111",
                "autopay_card_expiry": "08/29",
            },
            follow=True,
        )

        tenant.refresh_from_db()
        rent_bill.refresh_from_db()
        service_bill.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(tenant.autopay_enabled)
        self.assertEqual(rent_bill.status, Bill.Status.PAID)
        self.assertEqual(service_bill.status, Bill.Status.UNPAID)
        self.assertEqual(Payment.objects.filter(tenant=tenant).count(), 1)

    def test_tenant_overview_shows_rent_due_notice_within_five_days(self):
        tenant_user = User.objects.create_user(
            email="reminder@example.com",
            password="Existing-Place-House-23",
            full_name="Reminder Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 23",
            is_occupied=True,
        )
        Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Reminder Tenant",
            email="reminder@example.com",
            phone="+254700000015",
            id_number="45454545",
            unit_number="House 23",
            lease_start=timezone.localdate() - timedelta(days=25),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            last_rent_charge_at=timezone.now() - timedelta(days=25),
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        self.client.force_login(tenant_user)
        response = self.client.get(reverse("tenant-overview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rent reminder")

    def test_tenant_cash_payment_stays_pending_until_landlord_approves(self):
        tenant_user = User.objects.create_user(
            email="cashpending@example.com",
            password="Existing-Place-House-24",
            full_name="Cash Pending Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 24",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Cash Pending Tenant",
            email="cashpending@example.com",
            phone="+254700000016",
            id_number="34343434",
            unit_number="House 24",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        bill = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Water bill",
            category=Bill.Category.WATER,
            amount="5000.00",
            remaining_amount="5000.00",
            due_date=timezone.localdate(),
        )

        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-receipts"),
            {
                "form_action": "payment",
                "payment_target": Payment.Scope.BILL,
                "bill": str(bill.id),
                "method": Payment.Method.CASH,
            },
            follow=True,
        )
        payment = Payment.objects.get(tenant=tenant)
        bill.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(bill.remaining_amount, Decimal("5000.00"))

        self.client.force_login(self.landlord)
        approve_response = self.client.post(reverse("landlord-approve-payment", args=[payment.id]), follow=True)
        payment.refresh_from_db()
        bill.refresh_from_db()
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(payment.status, Payment.Status.CONFIRMED)
        self.assertEqual(bill.remaining_amount, Decimal("0.00"))

    def test_tenant_can_pay_multiple_selected_bills_together(self):
        tenant_user = User.objects.create_user(
            email="multibill@example.com",
            password="Existing-Place-House-26",
            full_name="Multi Bill Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 26",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Multi Bill Tenant",
            email="multibill@example.com",
            phone="+254700000018",
            id_number="12121212",
            unit_number="House 26",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        bill_one = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Water bill",
            category=Bill.Category.WATER,
            amount="5000.00",
            remaining_amount="5000.00",
            due_date=timezone.localdate(),
        )
        bill_two = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Service charge",
            category=Bill.Category.SERVICE_CHARGE,
            amount="10000.00",
            remaining_amount="10000.00",
            due_date=timezone.localdate(),
        )

        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-receipts"),
            {
                "form_action": "payment",
                "payment_target": Payment.Scope.BILL,
                "selected_bill_ids": f"{bill_one.id},{bill_two.id}",
                "method": Payment.Method.MPESA,
            },
            follow=True,
        )

        bill_one.refresh_from_db()
        bill_two.refresh_from_db()
        payment = Payment.objects.get(tenant=tenant)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.amount, Decimal("15000.00"))
        self.assertEqual(payment.selected_bill_ids, f"{bill_one.id},{bill_two.id}")
        self.assertEqual(bill_one.remaining_amount, Decimal("0.00"))
        self.assertEqual(bill_two.remaining_amount, Decimal("0.00"))
        self.assertEqual(PaymentAllocation.objects.filter(payment=payment).count(), 2)

    def test_landlord_bills_page_uses_live_balance_math(self):
        self.client.force_login(self.landlord)
        tenant_user = User.objects.create_user(
            email="billmath@example.com",
            password="DemoPass123!",
            full_name="Bill Math Tenant",
            role=User.Role.TENANT,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 27",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Bill Math Tenant",
            email="billmath@example.com",
            phone="+254700000019",
            id_number="67676767",
            unit_number="House 27",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Service charge April",
            category=Bill.Category.SERVICE_CHARGE,
            amount="10000.00",
            remaining_amount="4000.00",
            status=Bill.Status.PARTIALLY_PAID,
            due_date=timezone.localdate(),
        )

        response = self.client.get(reverse("landlord-bills"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bills-dashboard-data")
        self.assertContains(response, '"amount_due": 4000.0')
        self.assertContains(response, '"amount_paid": 6000.0')
        self.assertContains(response, '"original_amount": 10000.0')
        self.assertContains(response, '"status": "Partially Paid"')

    def test_landlord_bill_detail_shows_payment_allocations(self):
        tenant_user = User.objects.create_user(
            email="billdetail@example.com",
            password="DemoPass123!",
            full_name="Bill Detail Tenant",
            role=User.Role.TENANT,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 28",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Bill Detail Tenant",
            email="billdetail@example.com",
            phone="+254700000020",
            id_number="89898989",
            unit_number="House 28",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=365),
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )
        bill = Bill.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            title="Water bill May",
            category=Bill.Category.WATER,
            amount="5000.00",
            remaining_amount="0.00",
            status=Bill.Status.PAID,
            due_date=timezone.localdate(),
        )
        payment = Payment.objects.create(
            landlord=self.landlord,
            property=self.property,
            tenant=tenant,
            method=Payment.Method.MPESA,
            status=Payment.Status.CONFIRMED,
            scope=Payment.Scope.BILL,
            amount="5000.00",
            paid_on=timezone.localdate(),
        )
        PaymentAllocation.objects.create(
            payment=payment,
            bill=bill,
            amount="5000.00",
        )

        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-bill-detail", args=[bill.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment Applications")
        self.assertContains(response, "Water bill May")
        self.assertContains(response, "M-Pesa")
        self.assertContains(response, "KSh 5000")

    def test_tenant_can_prepay_future_rent_without_exceeding_lease_end(self):
        tenant_user = User.objects.create_user(
            email="prepay@example.com",
            password="Existing-Place-House-25",
            full_name="Prepay Tenant",
            role=User.Role.TENANT,
            password_change_required=False,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 25",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Prepay Tenant",
            email="prepay@example.com",
            phone="+254700000017",
            id_number="23232323",
            unit_number="House 25",
            lease_start=timezone.localdate(),
            lease_end=timezone.localdate() + timedelta(days=125),
            lease_type=Tenant.LeaseType.RENT,
            last_rent_charge_at=timezone.make_aware(datetime.combine(timezone.localdate(), datetime.min.time())),
            monthly_rent="35000.00",
            autopay_account_holder="Prepay Tenant",
            autopay_card_number="4111111111111111",
            autopay_card_expiry="08/29",
            security_deposit="70000.00",
        )

        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant-receipts"),
            {
                "form_action": "payment",
                "payment_target": Payment.Scope.RENT,
                "rent_periods": "4",
                "method": Payment.Method.CARD,
            },
            follow=True,
        )
        tenant.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.filter(tenant=tenant).count(), 1)
        self.assertEqual(tenant.rent_credit_balance, Decimal("140000.00"))

    def test_landlord_bill_form_does_not_offer_rent_category(self):
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-add-bill"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<option value="Rent">', html=False)

    def test_landlord_can_view_tenant_detail_with_initial_password_reference(self):
        self.client.force_login(self.landlord)
        tenant_user = User.objects.create_user(
            email="detail@example.com",
            password="Existing-Place-House-9",
            full_name="Detail Tenant",
            role=User.Role.TENANT,
            password_change_required=True,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 9",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Detail Tenant",
            email="detail@example.com",
            phone="+254700000005",
            id_number="66554433",
            unit_number="House 9",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        response = self.client.get(reverse("landlord-tenant-detail", args=[tenant.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Existing-Place-House-9")
        self.assertContains(response, "Default Active")

    def test_landlord_can_delete_tenant_and_release_house(self):
        self.client.force_login(self.landlord)
        tenant_user = User.objects.create_user(
            email="delete@example.com",
            password="Existing-Place-House-10",
            full_name="Delete Tenant",
            role=User.Role.TENANT,
            password_change_required=True,
        )
        unit_type = PropertyUnitType.objects.create(
            property=self.property,
            unit_type="1 Bedroom",
            unit_count=1,
            renting_price="35000.00",
            buying_price="6200000.00",
        )
        unit = PropertyUnit.objects.create(
            property=self.property,
            unit_type=unit_type,
            unit_number="House 10",
            is_occupied=True,
        )
        tenant = Tenant.objects.create(
            landlord=self.landlord,
            user=tenant_user,
            property=self.property,
            property_unit=unit,
            full_name="Delete Tenant",
            email="delete@example.com",
            phone="+254700000006",
            id_number="22334455",
            unit_number="House 10",
            lease_start="2026-04-01",
            lease_end="2027-03-31",
            lease_type=Tenant.LeaseType.RENT,
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        response = self.client.post(
            reverse("landlord-delete-tenant", args=[tenant.id]),
            follow=True,
        )
        unit.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tenant.objects.filter(id=tenant.id).exists())
        self.assertFalse(User.objects.filter(id=tenant_user.id).exists())
        self.assertFalse(unit.is_occupied)
