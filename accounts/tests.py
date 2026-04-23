from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .models import Bill, Complaint, LeaseExtensionRequest, Payment, Property, PropertyUnit, PropertyUnitType, Tenant, User


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
        new_bill = Bill.objects.exclude(id=bill.id).get()
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
            last_rent_charge_at=timezone.now() - timedelta(seconds=61),
            monthly_rent="35000.00",
            security_deposit="70000.00",
        )

        self.client.force_login(tenant_user)
        response = self.client.get(reverse("tenant-overview"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bill.objects.filter(tenant=tenant, category=Bill.Category.RENT).count(), 1)
        self.assertContains(response, "Auto Rent Tenant")

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
