from datetime import timedelta
from decimal import Decimal
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import BillForm, ComplaintForm, LandlordLoginForm, LeaseExtensionRequestForm, PaymentForm, PropertyForm, TenantForm, TenantPasswordChangeForm, UnitTypeFormSet
from .models import Bill, Complaint, LeaseExtensionRequest, Payment, Property, PropertyUnit, PropertyUnitType, Tenant, User

LANDLORD_PAGES = {
    "overview": "Overview",
    "properties": "Properties",
    "tenants": "Tenants",
    "payments": "Rent Payments",
    "bills": "Bills",
    "maintenance": "Maintenance",
    "analytics": "Analytics",
    "notifications": "Notifications",
    "settings": "Settings",
}

LANDLORD_TEMPLATES = {
    "overview": "landlord/overview/index.html",
    "properties": "landlord/properties/index.html",
    "tenants": "landlord/tenants/index.html",
    "payments": "landlord/payments/index.html",
    "bills": "landlord/bills/index.html",
    "maintenance": "landlord/maintenance/index.html",
    "analytics": "landlord/analytics/index.html",
    "notifications": "landlord/notifications/index.html",
    "settings": "landlord/settings/index.html",
}

TENANT_PAGES = {
    "overview": "Overview",
    "receipts": "Receipts & Payments",
    "profile": "Profile",
    "complaints": "Complaints",
    "notifications": "Notifications",
    "analytics": "Analytics",
    "settings": "Settings",
}

TENANT_TEMPLATES = {
    "overview": "tenant/overview/index.html",
    "receipts": "tenant/receipts/index.html",
    "profile": "tenant/profile/index.html",
    "complaints": "tenant/complaints/index.html",
    "notifications": "tenant/notifications/index.html",
    "analytics": "tenant/analytics/index.html",
    "settings": "tenant/settings/index.html",
}


def get_dashboard_redirect_name(user):
    if user.role == User.Role.TENANT:
        return "tenant-dashboard"
    return "landlord-dashboard"


def home(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_name(request.user))
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_name(request.user))

    form = LandlordLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=email, password=password)

        if user is None:
            provision_legacy_tenant_account(email)
            user = authenticate(request, username=email, password=password)

        if user is None:
            form.add_error(None, "Invalid email or password.")
        else:
            login(request, user)
            request.session.set_expiry(0)
            messages.success(request, f"Welcome back, {user.full_name}.")
            return redirect(get_dashboard_redirect_name(user))

    return render(request, "accounts/login.html", {"form": form})


def serialize_property(property_obj):
    projected_revenue = sum(
        item.unit_count * item.renting_price for item in property_obj.unit_types.all()
    )
    return {
        "id": property_obj.id,
        "name": property_obj.name,
        "location": property_obj.location,
        "units": property_obj.units,
        "occupiedUnits": property_obj.occupied_units,
        "revenue": float(projected_revenue or property_obj.monthly_revenue),
        "occupancy": property_obj.occupancy,
        "status": property_obj.status,
        "trend": float(property_obj.trend),
        "detailUrl": reverse("landlord-property-detail", args=[property_obj.id]),
        "editUrl": reverse("landlord-edit-property", args=[property_obj.id]),
        "deleteUrl": reverse("landlord-delete-property", args=[property_obj.id]),
    }


def update_property_occupancy(property_obj):
    occupied_units = property_obj.property_units.filter(is_occupied=True).count()
    property_obj.occupied_units = occupied_units
    property_obj.units = property_obj.property_units.count()
    property_obj.monthly_revenue = sum(
        (tenant.monthly_rent or 0)
        for tenant in property_obj.tenants.select_related("property_unit")
        if tenant.status != Tenant.Status.INACTIVE and tenant.lease_type == Tenant.LeaseType.RENT
    )
    property_obj.save()


def build_property_dashboard_data(user_properties):
    properties = list(user_properties.prefetch_related("unit_types", "property_units__unit_type"))
    total_properties = len(properties)
    total_units = sum(item.units for item in properties)
    occupied_units = sum(item.occupied_units for item in properties)
    vacant_units = max(total_units - occupied_units, 0)
    occupancy_rate = round((occupied_units / total_units) * 100, 1) if total_units else 0
    projected_monthly_rent = sum(
        item.unit_count * item.renting_price
        for property_obj in properties
        for item in property_obj.unit_types.all()
    )

    unit_mix_map = {}
    for property_obj in properties:
        for item in property_obj.unit_types.all():
            entry = unit_mix_map.setdefault(
                item.unit_type,
                {
                    "label": item.unit_type,
                    "count": 0,
                    "occupied": 0,
                    "avgRent": 0,
                    "avgBuyingPrice": 0,
                    "projectedRevenue": 0,
                    "projectedSalesValue": 0,
                },
            )
            entry["count"] += item.unit_count
            entry["projectedRevenue"] += float(item.unit_count * item.renting_price)
            entry["projectedSalesValue"] += float(item.unit_count * item.buying_price)
        for unit in property_obj.property_units.filter(is_occupied=True).select_related("unit_type"):
            if unit.unit_type:
                entry = unit_mix_map.setdefault(
                    unit.unit_type.unit_type,
                    {
                        "label": unit.unit_type.unit_type,
                        "count": 0,
                        "occupied": 0,
                        "avgRent": 0,
                        "avgBuyingPrice": 0,
                        "projectedRevenue": 0,
                        "projectedSalesValue": 0,
                    },
                )
                entry["occupied"] += 1

    for entry in unit_mix_map.values():
        entry["avgRent"] = round(entry["projectedRevenue"] / entry["count"], 2) if entry["count"] else 0
        entry["avgBuyingPrice"] = round(entry["projectedSalesValue"] / entry["count"], 2) if entry["count"] else 0

    best_performer = max(properties, key=lambda item: item.occupancy, default=None)
    most_capacity = max(properties, key=lambda item: item.units, default=None)

    return {
        "metricSet": [
            {
                "label": "Active Properties",
                "value": total_properties,
                "format": "number",
                "copy": "Buildings currently configured for this landlord account.",
                "trendLabel": "Live data",
                "trendStyle": "positive",
                "icon": "fa-building",
                "accent": True,
            },
            {
                "label": "Total Units",
                "value": total_units,
                "format": "number",
                "copy": "Unit count derived from the configured mix across all properties.",
                "trendLabel": "Live data",
                "trendStyle": "positive",
                "icon": "fa-layer-group",
                "iconTone": "mint",
            },
            {
                "label": "Occupied Units",
                "value": occupied_units,
                "format": "number",
                "copy": "This will increase as tenants begin occupying configured units.",
                "trendLabel": "Tenant-driven",
                "trendStyle": "positive",
                "icon": "fa-door-open",
                "iconTone": "gold",
            },
            {
                "label": "Projected Monthly Rent",
                "value": float(projected_monthly_rent),
                "format": "currency",
                "copy": "Projected from unit pricing before lease occupancy is applied.",
                "trendLabel": "Pricing-based",
                "trendStyle": "positive",
                "icon": "fa-wallet",
                "iconTone": "rose",
            },
        ],
        "unitMix": list(unit_mix_map.values()),
        "occupancyBreakdown": [
            {"label": "Occupied", "value": occupied_units, "color": "#2f74ff"},
            {"label": "Vacant", "value": vacant_units, "color": "#ffb24d"},
            {"label": "Reserved", "value": 0, "color": "#1bc6a6"},
        ],
        "hero": {
            "chips": [
                {"value": f"{total_properties} Properties", "label": "Configured in your portfolio"},
                {"value": f"{total_units} Units", "label": "Derived from the saved unit mix"},
                {"value": f"KSh {int(projected_monthly_rent):,}", "label": "Projected monthly rent potential"},
            ],
            "spotlights": [
                {
                    "label": "Best occupancy",
                    "value": best_performer.name if best_performer else "No properties yet",
                    "text": (
                        f"{best_performer.occupancy}% current occupancy on this property."
                        if best_performer else
                        "Add your first property to start tracking occupancy and rent potential."
                    ),
                },
                {
                    "label": "Largest inventory",
                    "value": most_capacity.name if most_capacity else "No properties yet",
                    "text": (
                        f"{most_capacity.units} configured units currently make this your largest property."
                        if most_capacity else
                        "Unit capacity will appear here once at least one property is configured."
                    ),
                },
            ],
            "occupancyRate": occupancy_rate,
            "projectedMonthlyRent": float(projected_monthly_rent),
        },
    }


def serialize_tenant(tenant_obj):
    return {
        "id": tenant_obj.id,
        "name": tenant_obj.full_name,
        "property": tenant_obj.property.name,
        "unit": tenant_obj.unit_number,
        "unitType": tenant_obj.property_unit.unit_type.unit_type if tenant_obj.property_unit and tenant_obj.property_unit.unit_type else "",
        "leaseType": tenant_obj.lease_type,
        "lease_end": tenant_obj.lease_end.strftime("%b %d, %Y") if tenant_obj.lease_end else "Not applicable",
        "status": tenant_obj.status,
        "risk": tenant_obj.risk_level,
        "autopay": tenant_obj.autopay_enabled,
        "balance": float(tenant_obj.current_balance),
        "billingAmount": float(tenant_obj.monthly_rent or tenant_obj.purchase_price or 0),
        "email": tenant_obj.email,
        "detailUrl": reverse("landlord-tenant-detail", args=[tenant_obj.id]),
        "editUrl": reverse("landlord-edit-tenant", args=[tenant_obj.id]),
        "deleteUrl": reverse("landlord-delete-tenant", args=[tenant_obj.id]),
    }


def build_tenant_dashboard_data(user_tenants):
    tenants = list(user_tenants.select_related("property"))
    today = timezone.localdate()
    renewal_cutoff = today + timedelta(days=45)
    active_tenants = [tenant for tenant in tenants if tenant.status != Tenant.Status.INACTIVE]
    active_count = len(active_tenants)
    autopay_count = sum(1 for tenant in active_tenants if tenant.autopay_enabled)
    autopay_rate = round((autopay_count / active_count) * 100, 1) if active_count else 0
    renewals_due = sorted(
        [
            tenant for tenant in active_tenants
            if tenant.lease_type == Tenant.LeaseType.RENT and tenant.lease_end and today <= tenant.lease_end <= renewal_cutoff
        ],
        key=lambda tenant: tenant.lease_end,
    )
    watchlist_count = sum(
        1 for tenant in active_tenants
        if tenant.status == Tenant.Status.WATCHLIST or tenant.risk_level == Tenant.RiskLevel.HIGH
    )
    good_standing_count = sum(
        1 for tenant in active_tenants if tenant.status == Tenant.Status.GOOD_STANDING
    )
    renewing_soon_count = sum(
        1 for tenant in active_tenants if tenant.status == Tenant.Status.RENEWING_SOON
    )
    low_risk_renewals = sum(
        1 for tenant in renewals_due if tenant.risk_level == Tenant.RiskLevel.LOW
    )

    return {
        "metric_set": [
            {
                "label": "Active Tenants",
                "value": active_count,
                "format": "number",
                "copy": "Current residents across your occupied units.",
                "trend_label": "Live data",
                "trend_style": "positive",
                "icon": "fa-users",
                "accent": True,
                "icon_tone": "",
            },
            {
                "label": "Autopay Enrollment",
                "value": autopay_rate,
                "format": "percent",
                "copy": "The share of active tenants set up for recurring payments.",
                "trend_label": "Live data",
                "trend_style": "positive",
                "icon": "fa-repeat",
                "accent": False,
                "icon_tone": "mint",
            },
            {
                "label": "Renewals Due",
                "value": len(renewals_due),
                "format": "number",
                "copy": "Leases ending within the next 45 days.",
                "trend_label": "45-day horizon",
                "trend_style": "positive",
                "icon": "fa-file-signature",
                "accent": False,
                "icon_tone": "gold",
            },
            {
                "label": "Watchlist Tenants",
                "value": watchlist_count,
                "format": "number",
                "copy": "Tenants needing closer attention due to status or risk profile.",
                "trend_label": "Live data",
                "trend_style": "negative",
                "icon": "fa-user-clock",
                "accent": False,
                "icon_tone": "rose",
            },
        ],
        "hero": {
            "chips": [
                {"value": f"{active_count} Active", "label": "Current leaseholders"},
                {"value": f"{autopay_rate:.1f}%", "label": "Autopay enrollment"},
                {"value": f"{len(renewals_due)} Renewals", "label": "Due within 45 days"},
            ],
            "spotlights": [
                {
                    "label": "Retention opportunity",
                    "value": f"{low_risk_renewals} tenants" if low_risk_renewals else "No low-risk renewals yet",
                    "text": (
                        "Residents with healthy payment posture are approaching renewal and are good candidates for early outreach."
                        if low_risk_renewals else
                        "As tenants approach renewal with strong payment history, they will appear here."
                    ),
                },
                {
                    "label": "Attention needed",
                    "value": f"{watchlist_count} watchlist" if watchlist_count else "No watchlist tenants",
                    "text": (
                        "These tenants need the fastest follow-up because of risk signals or lease posture."
                        if watchlist_count else
                        "Watchlist tenants will appear here once there are payment or lease risks to review."
                    ),
                },
            ],
        },
        "segments": [
            {"label": "Good Standing", "value": good_standing_count, "color": "#2f74ff"},
            {"label": "Renewing Soon", "value": renewing_soon_count, "color": "#ffb24d"},
            {"label": "Watchlist", "value": watchlist_count, "color": "#ec5f67"},
        ],
        "renewal_queue": [
            {
                "name": tenant.full_name,
                "unit": tenant.unit_number,
                "date": tenant.lease_end.strftime("%b %d, %Y"),
                "action": (
                    "Send a renewal proposal."
                    if tenant.status == Tenant.Status.RENEWING_SOON else
                    "Review this lease and confirm the next tenant conversation."
                ),
                "tone": (
                    "vacancy-risk"
                    if tenant.risk_level == Tenant.RiskLevel.HIGH else
                    "needs-attention"
                    if tenant.status == Tenant.Status.RENEWING_SOON else
                    "stable"
                ),
            }
            for tenant in renewals_due[:5]
        ],
    }


def build_tenant_workspace_data(tenant):
    unit_type = tenant.property_unit.unit_type.unit_type if tenant.property_unit and tenant.property_unit.unit_type else "Not set"
    pricing = tenant.monthly_rent if tenant.lease_type == Tenant.LeaseType.RENT else tenant.purchase_price
    return {
        "hero_chips": [
            {"value": tenant.property.name, "label": "Assigned property"},
            {"value": tenant.unit_number, "label": "Your house"},
            {"value": tenant.lease_type, "label": "Occupancy type"},
        ],
        "metrics": [
            {
                "label": "Assigned Home",
                "value": tenant.unit_number,
                "copy": f"{unit_type} at {tenant.property.name}.",
                "icon": "fa-house",
            },
            {
                "label": "Billing Amount",
                "value": float(pricing or 0),
                "format": "currency",
                "copy": "Derived from the unit pricing selected by your landlord.",
                "icon": "fa-wallet",
            },
            {
                "label": "Current Balance",
                "value": float(tenant.current_balance),
                "format": "currency",
                "copy": "Outstanding balance currently on your account.",
                "icon": "fa-scale-balanced",
            },
            {
                "label": "Autopay",
                "value": "Enabled" if tenant.autopay_enabled else "Not enabled",
                "copy": "Payment automation status for this account.",
                "icon": "fa-repeat",
            },
        ],
    }


def get_rent_billing_interval():
    return timedelta(seconds=max(getattr(settings, "RENT_BILLING_INTERVAL_SECONDS", 60), 1))


def initialize_rent_schedule(tenant):
    if tenant.lease_type != Tenant.LeaseType.RENT or not tenant.monthly_rent:
        tenant.last_rent_charge_at = None
        return
    if tenant.lease_start > timezone.localdate():
        tenant.last_rent_charge_at = None
    else:
        tenant.last_rent_charge_at = timezone.now()


def process_due_rent_bills(tenants):
    now = timezone.now()
    interval = get_rent_billing_interval()
    for tenant in tenants:
        if tenant.lease_type != Tenant.LeaseType.RENT or not tenant.monthly_rent:
            continue
        if tenant.lease_start > timezone.localdate():
            continue

        if tenant.last_rent_charge_at is None:
            tenant.last_rent_charge_at = now
            tenant.save(update_fields=["last_rent_charge_at"])
            continue

        charge_time = tenant.last_rent_charge_at
        while charge_time + interval <= now:
            charge_time += interval
            bill = Bill.objects.create(
                landlord=tenant.landlord,
                property=tenant.property,
                tenant=tenant,
                title=f"Automatic rent charge for {charge_time.strftime('%b %d, %Y %H:%M')}",
                category=Bill.Category.RENT,
                amount=tenant.monthly_rent,
                remaining_amount=tenant.monthly_rent,
                due_date=charge_time.date(),
                status=Bill.Status.UNPAID,
                notes="Generated automatically from the lease rent schedule.",
            )
            apply_credit_to_bill(bill)
        if charge_time != tenant.last_rent_charge_at:
            tenant.last_rent_charge_at = charge_time
            tenant.save(update_fields=["last_rent_charge_at"])


def build_tenant_receipts_data(tenant):
    bills = list(tenant.bills.select_related("property").order_by("-created_at"))
    payments = list(tenant.payments.select_related("property").order_by("-paid_on", "-created_at"))
    total_due = sum((bill.remaining_amount for bill in bills if bill.status != Bill.Status.PAID), Decimal("0"))
    transactions = []
    for bill in bills:
        transactions.append(
            {
                "type": "Bill",
                "category": bill.category,
                "amount": float(bill.remaining_amount),
                "originalAmount": float(bill.amount),
                "amountPaid": float(bill.amount - bill.remaining_amount),
                "date": bill.created_at.strftime("%b %d, %Y"),
                "sortDate": bill.created_at.isoformat(),
                "method": "Issued",
                "detailUrl": reverse("tenant-bill-detail", args=[bill.id]),
            }
        )
    for payment in payments:
        transactions.append(
            {
                "type": "Payment",
                "amount": float(payment.amount),
                "originalAmount": float(payment.amount),
                "amountPaid": float(payment.amount),
                "date": payment.paid_on.strftime("%b %d, %Y"),
                "sortDate": payment.paid_on.isoformat(),
                "method": payment.method,
                "detailUrl": reverse("tenant-payment-detail", args=[payment.id]),
            }
        )
    transactions.sort(key=lambda item: item["sortDate"], reverse=True)
    return {
        "transactions": transactions,
        "summary": {
            "total_due": float(total_due),
            "current_balance": float(tenant.current_balance),
        },
    }


def build_tenant_notifications(tenant):
    items = [
        {
            "title": "Account security reminder" if tenant.user and tenant.user.password_change_required else "Account secured",
            "copy": "Please update your password in Settings to secure your tenant account." if tenant.user and tenant.user.password_change_required else "Your password has already been updated from the default setup.",
            "tone": "needs-attention" if tenant.user and tenant.user.password_change_required else "stable",
        },
        {
            "title": "Billing simplified",
            "copy": "Your receipts page now shows your total amount due and current balance.",
            "tone": "stable",
        },
    ]
    if tenant.lease_type == Tenant.LeaseType.RENT and tenant.lease_end:
        items.append(
            {
                "title": "Lease timeline",
                "copy": f"Your current lease ends on {tenant.lease_end.strftime('%b %d, %Y')}. You can request an extension from the receipts page.",
                "tone": "needs-attention",
            }
        )
    if tenant.complaints.exists():
        latest = tenant.complaints.first()
        items.append(
            {
                "title": "Latest complaint status",
                "copy": f"'{latest.title}' is currently marked as {latest.status}.",
                "tone": "stable" if latest.status == Complaint.Status.RESOLVED else "needs-attention",
            }
        )
    return items


def build_tenant_analytics_data(tenant):
    complaint_count = tenant.complaints.count()
    extension_count = tenant.lease_extension_requests.count()
    return {
        "metrics": [
            {"label": "Open complaints", "value": complaint_count, "format": "number", "icon": "fa-triangle-exclamation"},
            {"label": "Extension requests", "value": extension_count, "format": "number", "icon": "fa-file-signature"},
            {"label": "Current balance", "value": float(tenant.current_balance), "format": "currency", "icon": "fa-wallet"},
            {"label": "Autopay", "value": "Enabled" if tenant.autopay_enabled else "Manual", "icon": "fa-repeat"},
        ],
        "charts": {
            "charges": [
                {"label": "Occupancy charge", "value": float(tenant.monthly_rent or tenant.purchase_price or 0), "color": "#2f74ff"},
                {"label": "Current balance", "value": float(tenant.current_balance), "color": "#1bc6a6"},
            ],
            "activity": {
                "labels": ["Complaints", "Extensions", "Notifications"],
                "values": [complaint_count, extension_count, len(build_tenant_notifications(tenant))],
            },
        },
    }


def update_bill_status(bill):
    if bill.remaining_amount <= Decimal("0"):
        bill.remaining_amount = Decimal("0")
        bill.status = Bill.Status.PAID
    elif bill.remaining_amount < bill.amount:
        bill.status = Bill.Status.PARTIALLY_PAID
    else:
        bill.status = Bill.Status.UNPAID


def apply_credit_to_bill(bill):
    if not bill.tenant or bill.remaining_amount <= Decimal("0") or bill.tenant.current_balance <= Decimal("0"):
        update_bill_status(bill)
        bill.save(update_fields=["remaining_amount", "status"])
        return Decimal("0")

    applied = min(bill.tenant.current_balance, bill.remaining_amount)
    bill.remaining_amount -= applied
    bill.tenant.current_balance -= applied
    update_bill_status(bill)
    bill.tenant.save(update_fields=["current_balance"])
    bill.save(update_fields=["remaining_amount", "status"])
    return applied


def allocate_payment_to_bills(payment):
    remaining_payment = payment.amount
    open_bills = (
        Bill.objects.filter(
            tenant=payment.tenant,
        )
        .exclude(status=Bill.Status.PAID)
        .order_by("created_at", "id")
    )

    for bill in open_bills:
        if remaining_payment <= Decimal("0"):
            break
        allocation = min(remaining_payment, bill.remaining_amount)
        bill.remaining_amount -= allocation
        remaining_payment -= allocation
        update_bill_status(bill)
        bill.save(update_fields=["remaining_amount", "status"])

    if remaining_payment > Decimal("0"):
        payment.tenant.current_balance += remaining_payment
        payment.tenant.save(update_fields=["current_balance"])

    return remaining_payment


def serialize_payment(payment_obj):
    return {
        "id": payment_obj.id,
        "tenant": payment_obj.tenant.full_name,
        "property": payment_obj.property.name,
        "unit": payment_obj.tenant.unit_number,
        "amount": float(payment_obj.amount),
        "date": payment_obj.paid_on.strftime("%b %d, %Y"),
        "status": "Paid",
        "method": payment_obj.method,
        "detailUrl": reverse("landlord-payment-detail", args=[payment_obj.id]),
    }


def build_payments_dashboard_data(user, user_tenants):
    payments = list(
        Payment.objects.filter(landlord=user).select_related("tenant", "property")
    )
    month_start = timezone.localdate().replace(day=1)
    month_payments = [item for item in payments if item.paid_on >= month_start]
    collected_this_month = sum(item.amount for item in month_payments)
    outstanding_balance = sum(
        item.remaining_amount
        for item in Bill.objects.filter(landlord=user).exclude(status=Bill.Status.PAID)
    )
    autopay_count = sum(1 for tenant in user_tenants if tenant.autopay_enabled)
    autopay_success = round((autopay_count / len(user_tenants)) * 100, 1) if user_tenants else 0
    methods = {}
    for payment in payments:
        methods[payment.method] = methods.get(payment.method, 0) + 1
    payment_methods = [
        {"label": label, "value": value, "color": color}
        for (label, color), value in zip(
            [("M-Pesa", "#2f74ff"), ("Bank Transfer", "#1bc6a6"), ("Cash", "#ffb24d"), ("Card", "#ec5f67")],
            [methods.get("M-Pesa", 0), methods.get("Bank Transfer", 0), methods.get("Cash", 0), methods.get("Card", 0)],
        )
    ]
    return {
        "metrics": {
            "collected_this_month": float(collected_this_month),
            "outstanding_balance": float(outstanding_balance),
            "overdue_accounts": Tenant.objects.filter(
                landlord=user,
                bills__status__in=[Bill.Status.UNPAID, Bill.Status.PARTIALLY_PAID],
            ).distinct().count(),
            "autopay_success": autopay_success,
        },
        "payments": [serialize_payment(item) for item in payments],
        "payment_methods": payment_methods,
    }


def serialize_bill(bill_obj):
    return {
        "id": bill_obj.id,
        "title": bill_obj.title,
        "category": bill_obj.category,
        "property": bill_obj.property.name,
        "tenant": bill_obj.tenant.full_name if bill_obj.tenant else "Property-wide",
        "amount": float(bill_obj.remaining_amount),
        "originalAmount": float(bill_obj.amount),
        "due_date": bill_obj.due_date.strftime("%b %d, %Y"),
        "status": bill_obj.status,
        "detailUrl": reverse("tenant-bill-detail", args=[bill_obj.id]) if bill_obj.tenant else "",
    }


def build_bills_dashboard_data(user):
    bills = list(Bill.objects.filter(landlord=user).select_related("property", "tenant"))
    payments = list(Payment.objects.filter(landlord=user).select_related("tenant"))
    
    tenant_payments = {}
    for payment in payments:
        if payment.tenant:
            tenant_id = payment.tenant_id
            if tenant_id not in tenant_payments:
                tenant_payments[tenant_id] = Decimal("0")
            tenant_payments[tenant_id] += payment.amount
    
    accumulated = {}
    for bill in bills:
        key = (bill.property_id, bill.tenant_id if bill.tenant else None)
        if key not in accumulated:
            accumulated[key] = {
                "property": bill.property.name,
                "tenant": bill.tenant.full_name if bill.tenant else "Property-wide",
                "tenant_id": bill.tenant_id,
                "original_amount": Decimal("0"),
                "has_unpaid": False,
            }
        accumulated[key]["original_amount"] += bill.amount
        if bill.status != Bill.Status.PAID:
            accumulated[key]["has_unpaid"] = True
    
    accumulated_bills = []
    total_amount_due = Decimal("0")
    unpaid_count = 0
    for key, entry in accumulated.items():
        original_amount = entry["original_amount"]
        total_amount_due += original_amount
        if entry["has_unpaid"]:
            unpaid_count += 1
        status = "Paid" if not entry["has_unpaid"] else ("Has Balance" if original_amount > 0 else "Unpaid")
        status_class = "high-performing" if not entry["has_unpaid"] else ("stable" if original_amount > 0 else "vacancy-risk")
        accumulated_bills.append({
            "property": entry["property"],
            "tenant": entry["tenant"],
            "amount_due": float(original_amount),
            "amount_paid": float(tenant_payments.get(entry["tenant_id"], Decimal("0"))),
            "status": status,
            "status_class": status_class,
        })
    
    accumulated_bills.sort(key=lambda x: x["amount_due"], reverse=True)
    
    return {
        "accumulated_bills": accumulated_bills,
        "total_amount_due": float(total_amount_due),
        "unpaid_count": unpaid_count,
    }


def serialize_complaint(complaint_obj):
    return {
        "title": complaint_obj.title,
        "tenant": complaint_obj.tenant.full_name,
        "property": complaint_obj.tenant.property.name,
        "unit": complaint_obj.tenant.unit_number,
        "category": complaint_obj.category,
        "status": complaint_obj.status,
        "created_at": complaint_obj.created_at.strftime("%b %d, %Y"),
    }


def build_maintenance_dashboard_data(user):
    complaints = list(
        Complaint.objects.filter(tenant__landlord=user).select_related("tenant", "tenant__property")
    )
    category_totals = {}
    for item in complaints:
        category_totals[item.category] = category_totals.get(item.category, 0) + 1
    return {
        "metrics": {
            "open_tickets": sum(1 for item in complaints if item.status != Complaint.Status.RESOLVED),
            "in_progress": sum(1 for item in complaints if item.status == Complaint.Status.IN_PROGRESS),
            "resolved": sum(1 for item in complaints if item.status == Complaint.Status.RESOLVED),
            "pending": sum(1 for item in complaints if item.status == Complaint.Status.PENDING),
        },
        "complaints": [serialize_complaint(item) for item in complaints],
        "categories": {
            "labels": list(category_totals.keys()) or ["No complaints"],
            "values": list(category_totals.values()) or [0],
        },
    }


def get_owned_property(request, property_id):
    return get_object_or_404(Property, id=property_id, landlord=request.user)


def get_tenant_profile(request):
    try:
        return Tenant.objects.select_related("property", "property_unit__unit_type", "user").get(
            user=request.user,
        )
    except Tenant.DoesNotExist:
        return None


def get_owned_tenant(request, tenant_id):
    return get_object_or_404(
        Tenant.objects.select_related("property", "property_unit__unit_type", "user"),
        id=tenant_id,
        landlord=request.user,
    )


def format_credential_segment(value):
    parts = re.findall(r"[A-Za-z0-9]+", value or "")
    return "-".join(part.capitalize() for part in parts if part)


def build_tenant_initial_password(property_name, unit_number):
    property_segment = format_credential_segment(property_name)
    unit_segment = format_credential_segment(unit_number)
    return f"{property_segment}-{unit_segment}" if property_segment and unit_segment else "SmartRent-Temp-Password"


def ensure_tenant_user_account(tenant):
    existing_user = User.objects.filter(email__iexact=tenant.email).exclude(
        id=getattr(tenant.user, "id", None)
    ).first()
    if existing_user and existing_user.role != User.Role.TENANT:
        raise ValidationError("That email is already used by a non-tenant account.")
    linked_profile = getattr(existing_user, "tenant_profile", None) if existing_user else None
    if linked_profile and linked_profile.id != tenant.id:
        raise ValidationError("That email is already linked to another tenant profile.")

    generated_password = build_tenant_initial_password(tenant.property.name, tenant.unit_number)
    user = tenant.user or existing_user
    created = user is None

    if user is None:
        user = User(
            email=tenant.email,
            role=User.Role.TENANT,
        )

    user.email = tenant.email
    user.username = tenant.email
    user.full_name = tenant.full_name
    user.role = User.Role.TENANT
    if created:
        user.password_change_required = True
        user.set_password(generated_password)
    user.save()
    tenant.user = user
    return generated_password, created


def provision_legacy_tenant_account(email):
    tenant = (
        Tenant.objects.select_related("property", "user")
        .filter(email__iexact=email, user__isnull=True)
        .first()
    )
    if not tenant:
        return None
    generated_password, _ = ensure_tenant_user_account(tenant)
    tenant.save(update_fields=["user"])
    return generated_password


def build_unit_type_formset(request, property_obj=None):
    initial = None
    if request.method != "POST":
        if property_obj is not None:
            initial = [
                {
                    "unit_type": item.unit_type,
                    "unit_count": item.unit_count,
                    "renting_price": item.renting_price,
                    "buying_price": item.buying_price,
                }
                for item in property_obj.unit_types.all()
            ]
        else:
            initial = [
                {"unit_type": "Studio", "unit_count": 4, "renting_price": 18000, "buying_price": 4200000},
                {"unit_type": "1 Bedroom", "unit_count": 8, "renting_price": 26000, "buying_price": 6200000},
            ]

    return UnitTypeFormSet(
        request.POST or None,
        prefix="unit_types",
        initial=initial,
    )


def sync_property_units(property_obj):
    existing_units = {
        unit.unit_number: unit
        for unit in property_obj.property_units.select_related("unit_type")
    }
    desired_numbers = []
    next_number = 1

    for unit_type in property_obj.unit_types.all():
        for _ in range(unit_type.unit_count):
            unit_number = f"House {next_number}"
            desired_numbers.append(unit_number)
            unit = existing_units.get(unit_number)
            if unit:
                if unit.unit_type_id != unit_type.id:
                    unit.unit_type = unit_type
                    unit.save(update_fields=["unit_type"])
            else:
                PropertyUnit.objects.create(
                    property=property_obj,
                    unit_type=unit_type,
                    unit_number=unit_number,
                )
            next_number += 1

    for unit in property_obj.property_units.exclude(unit_number__in=desired_numbers):
        if hasattr(unit, "current_tenant"):
            continue
        unit.delete()

    update_property_occupancy(property_obj)


def build_available_units_payload(user_properties):
    payload = {}
    properties = user_properties.prefetch_related("property_units__unit_type")
    for property_obj in properties:
        units_by_type = {}
        for unit in property_obj.property_units.filter(is_occupied=False).select_related("unit_type"):
            if not unit.unit_type:
                continue
            units_by_type.setdefault(unit.unit_type.unit_type, []).append(
                {
                    "id": unit.id,
                    "label": unit.unit_number,
                    "rentingPrice": float(unit.unit_type.renting_price),
                    "buyingPrice": float(unit.unit_type.buying_price),
                }
            )
        payload[str(property_obj.id)] = {
            "name": property_obj.name,
            "unitTypes": units_by_type,
        }
    return payload


def save_property_and_unit_types(property_obj, form, unit_type_formset, landlord):
    property_record = form.save(commit=False)
    total_units = sum(
        item["unit_count"]
        for item in unit_type_formset.cleaned_data
        if item and not item.get("DELETE")
    )
    property_record.landlord = landlord
    property_record.units = total_units
    if property_obj is None:
        property_record.occupied_units = 0
        property_record.monthly_revenue = 0
    property_record.save()
    property_record.unit_types.all().delete()
    for item in unit_type_formset.cleaned_data:
        if not item or item.get("DELETE"):
            continue
        PropertyUnitType.objects.create(
            property=property_record,
            unit_type=item["unit_type"],
            unit_count=item["unit_count"],
            renting_price=item["renting_price"],
            buying_price=item["buying_price"],
        )
    sync_property_units(property_record)
    return property_record


@login_required
def landlord_page(request, page="overview"):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can access this dashboard.")
    if page not in LANDLORD_PAGES:
        return HttpResponseForbidden("Unknown landlord page.")
    user_properties = Property.objects.filter(landlord=request.user)
    user_tenant_queryset = Tenant.objects.filter(landlord=request.user).select_related("property", "property_unit__unit_type")
    process_due_rent_bills(list(user_tenant_queryset))
    if page == "tenants":
        user_tenants = user_tenant_queryset
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "tenants_payload": [serialize_tenant(item) for item in user_tenants],
            "tenant_dashboard_data": build_tenant_dashboard_data(user_tenants),
        }
        return render(request, LANDLORD_TEMPLATES[page], context)
    if page == "payments":
        user_tenants = list(user_tenant_queryset)
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "payments_dashboard_data": build_payments_dashboard_data(request.user, user_tenants),
        }
        return render(request, LANDLORD_TEMPLATES[page], context)
    if page == "bills":
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "bills_dashboard_data": build_bills_dashboard_data(request.user),
        }
        return render(request, LANDLORD_TEMPLATES[page], context)
    if page == "maintenance":
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "maintenance_dashboard_data": build_maintenance_dashboard_data(request.user),
        }
        return render(request, LANDLORD_TEMPLATES[page], context)
    property_dashboard_data = build_property_dashboard_data(user_properties)
    context = {
        "page_key": page,
        "page_title": LANDLORD_PAGES[page],
        "properties_payload": [serialize_property(item) for item in user_properties],
        "property_dashboard_data": property_dashboard_data,
    }
    return render(request, LANDLORD_TEMPLATES[page], context)


@login_required
def tenant_page(request, page="overview"):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")
    if page not in TENANT_PAGES:
        return HttpResponseForbidden("Unknown tenant page.")

    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    process_due_rent_bills([tenant])
    tenant.refresh_from_db()
    context = {
        "page_key": page,
        "page_title": TENANT_PAGES[page],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "tenant_receipts_data": build_tenant_receipts_data(tenant),
        "tenant_notifications": build_tenant_notifications(tenant),
        "tenant_analytics": build_tenant_analytics_data(tenant),
    }
    return render(request, TENANT_TEMPLATES[page], context)


@login_required
def tenant_settings(request):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")

    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    process_due_rent_bills([tenant])
    tenant.refresh_from_db()
    form = TenantPasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        if user.password_change_required:
            user.password_change_required = False
            user.save(update_fields=["password_change_required"])
        update_session_auth_hash(request, user)
        messages.success(request, "Your password was updated successfully.")
        return redirect("tenant-settings")

    context = {
        "page_key": "settings",
        "page_title": TENANT_PAGES["settings"],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "password_form": form,
    }
    return render(request, TENANT_TEMPLATES["settings"], context)


@login_required
def tenant_receipts(request):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")

    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    process_due_rent_bills([tenant])
    tenant.refresh_from_db()

    form = LeaseExtensionRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        extension = form.save(commit=False)
        extension.tenant = tenant
        extension.save()
        messages.success(request, "Your lease extension request was submitted.")
        return redirect("tenant-receipts")

    context = {
        "page_key": "receipts",
        "page_title": TENANT_PAGES["receipts"],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "tenant_receipts_data": build_tenant_receipts_data(tenant),
        "tenant_notifications": build_tenant_notifications(tenant),
        "tenant_analytics": build_tenant_analytics_data(tenant),
        "lease_extension_form": form,
        "lease_extension_requests": tenant.lease_extension_requests.all(),
    }
    return render(request, TENANT_TEMPLATES["receipts"], context)


@login_required
def tenant_bill_detail(request, bill_id):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")
    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    bill = get_object_or_404(Bill.objects.select_related("property", "tenant"), id=bill_id, tenant=tenant)
    return render(
        request,
        "tenant/receipts/bill_detail.html",
        {
            "page_key": "receipts",
            "page_title": "Bill Detail",
            "tenant": tenant,
            "tenant_workspace": build_tenant_workspace_data(tenant),
            "bill": bill,
        },
    )


@login_required
def tenant_payment_detail(request, payment_id):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")
    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    payment = get_object_or_404(Payment.objects.select_related("property", "tenant"), id=payment_id, tenant=tenant)
    return render(
        request,
        "tenant/receipts/payment_detail.html",
        {
            "page_key": "receipts",
            "page_title": "Payment Detail",
            "tenant": tenant,
            "tenant_workspace": build_tenant_workspace_data(tenant),
            "payment": payment,
        },
    )


@login_required
def landlord_payment_detail(request, payment_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can access this workspace.")
    payment = get_object_or_404(
        Payment.objects.select_related("tenant", "property"),
        id=payment_id,
        landlord=request.user,
    )
    return render(
        request,
        "landlord/payments/payment_detail.html",
        {
            "page_key": "payments",
            "page_title": "Payment Detail",
            "payment": payment,
        },
    )


@login_required
def tenant_complaints(request):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")

    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    process_due_rent_bills([tenant])
    tenant.refresh_from_db()

    form = ComplaintForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        complaint = form.save(commit=False)
        complaint.tenant = tenant
        complaint.save()
        messages.success(request, "Your complaint was logged successfully.")
        return redirect("tenant-complaints")

    context = {
        "page_key": "complaints",
        "page_title": TENANT_PAGES["complaints"],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "tenant_receipts_data": build_tenant_receipts_data(tenant),
        "tenant_notifications": build_tenant_notifications(tenant),
        "tenant_analytics": build_tenant_analytics_data(tenant),
        "complaint_form": form,
        "complaints": tenant.complaints.all(),
        "complaints_payload": [
            {
                "title": item.title,
                "category": item.category,
                "description": item.description,
                "status": item.status,
                "createdAt": item.created_at.strftime("%b %d, %Y"),
            }
            for item in tenant.complaints.all()
        ],
    }
    return render(request, TENANT_TEMPLATES["complaints"], context)


@login_required
def add_property(request):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can create properties.")

    user_properties = Property.objects.filter(landlord=request.user)
    form = PropertyForm(request.POST or None)
    unit_type_formset = build_unit_type_formset(request)
    if request.method == "POST" and form.is_valid() and unit_type_formset.is_valid():
        property_obj = save_property_and_unit_types(None, form, unit_type_formset, request.user)
        messages.success(request, f"{property_obj.name} was added to your portfolio.")
        return redirect("landlord-properties")

    context = {
        "page_key": "properties",
        "form": form,
        "unit_type_formset": unit_type_formset,
        "properties_payload": [serialize_property(item) for item in user_properties],
        "property_dashboard_data": build_property_dashboard_data(user_properties),
        "page_heading": "Add a property intelligently",
        "page_description": "Set up the building once, define its unit mix and pricing, and let occupancy plus revenue be driven later by tenants and leases.",
        "submit_label": "Save Property",
        "back_url": reverse("landlord-properties"),
    }
    return render(request, "landlord/properties/add_property.html", context)


@login_required
def edit_property(request, property_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can edit properties.")

    property_obj = get_owned_property(request, property_id)
    user_properties = Property.objects.filter(landlord=request.user)
    form = PropertyForm(request.POST or None, instance=property_obj)
    unit_type_formset = build_unit_type_formset(request, property_obj)

    if request.method == "POST" and form.is_valid() and unit_type_formset.is_valid():
        updated_property = save_property_and_unit_types(property_obj, form, unit_type_formset, request.user)
        messages.success(request, f"{updated_property.name} was updated.")
        return redirect("landlord-properties")

    context = {
        "page_key": "properties",
        "form": form,
        "unit_type_formset": unit_type_formset,
        "properties_payload": [serialize_property(item) for item in user_properties],
        "property_dashboard_data": build_property_dashboard_data(user_properties),
        "page_heading": f"Edit {property_obj.name}",
        "page_description": "Update the property profile and refine its unit mix without touching tenant occupancy yet.",
        "submit_label": "Save Changes",
        "back_url": reverse("landlord-property-detail", args=[property_obj.id]),
    }
    return render(request, "landlord/properties/add_property.html", context)


@login_required
def property_detail(request, property_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can view properties.")

    property_obj = get_owned_property(request, property_id)
    user_properties = Property.objects.filter(landlord=request.user)
    context = {
        "page_key": "properties",
        "property": property_obj,
        "unit_types": property_obj.unit_types.all(),
        "properties_payload": [serialize_property(item) for item in user_properties],
        "property_dashboard_data": build_property_dashboard_data(user_properties),
    }
    return render(request, "landlord/properties/property_detail.html", context)


@login_required
@require_POST
def delete_property(request, property_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can delete properties.")

    property_obj = get_owned_property(request, property_id)
    property_name = property_obj.name
    property_obj.delete()
    messages.success(request, f"{property_name} was deleted.")
    return redirect("landlord-properties")


@login_required
def record_payment(request):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can record payments.")

    form = PaymentForm(request.POST or None, landlord=request.user)
    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.landlord = request.user
        payment.property = payment.tenant.property
        payment.save()
        allocate_payment_to_bills(payment)
        messages.success(request, f"Payment for {payment.tenant.full_name} was recorded.")
        return redirect("landlord-payments")

    context = {
        "page_key": "payments",
        "form": form,
        "page_heading": "Record a payment",
        "page_description": "Capture a payment against a tenant account and keep the collections feed current.",
        "submit_label": "Save Payment",
        "back_url": reverse("landlord-payments"),
    }
    return render(request, "landlord/payments/record_payment.html", context)


@login_required
def add_bill(request):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can add bills.")

    form = BillForm(request.POST or None, landlord=request.user)
    if request.method == "POST" and form.is_valid():
        bill = form.save(commit=False)
        bill.landlord = request.user
        if bill.tenant and bill.property_id != bill.tenant.property_id:
            form.add_error("tenant", "Selected tenant must belong to the selected property.")
        else:
            bill.remaining_amount = bill.amount
            bill.save()
            if bill.tenant:
                apply_credit_to_bill(bill)
            messages.success(request, f"{bill.title} was added.")
            return redirect("landlord-bills")

    context = {
        "page_key": "bills",
        "form": form,
        "page_heading": "Create a bill",
        "page_description": "Add service charge, water, repair, or custom bills for a property or a specific tenant.",
        "submit_label": "Save Bill",
        "back_url": reverse("landlord-bills"),
    }
    return render(request, "landlord/bills/add_bill.html", context)


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("login")


@login_required
def add_tenant(request):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can add tenants.")

    user_properties = Property.objects.filter(landlord=request.user)
    if not user_properties.exists():
        messages.warning(
            request,
            "You need to add a property before you can add tenants."
        )
        return redirect("landlord-add-property")

    form = TenantForm(request.POST or None, initial={"landlord": request.user}, landlord=request.user)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                tenant = form.save(commit=False)
                tenant.landlord = request.user
                initialize_rent_schedule(tenant)
                generated_password, _ = ensure_tenant_user_account(tenant)
                tenant.save()
                if tenant.property_unit:
                    tenant.property_unit.is_occupied = True
                    tenant.property_unit.save(update_fields=["is_occupied"])
                    update_property_occupancy(tenant.property)
        except ValidationError as error:
            form.add_error("email", error.message)
        else:
            messages.success(
                request,
                f"{tenant.full_name} was added. Tenant login: {tenant.email} / {generated_password}",
            )
            return redirect("landlord-tenants")

    context = {
        "page_key": "tenants",
        "form": form,
        "user_properties": user_properties,
        "properties_payload": [serialize_property(item) for item in user_properties],
        "property_dashboard_data": build_property_dashboard_data(user_properties),
        "page_heading": "Add a tenant intelligently",
        "page_description": "Register a new tenant, assign them to a property and unit, and configure their lease terms. Occupancy updates automatically when a tenant is active.",
        "submit_label": "Save Tenant",
        "back_url": reverse("landlord-tenants"),
        "available_units_payload": build_available_units_payload(user_properties),
    }
    return render(request, "landlord/tenants/add_tenant.html", context)


@login_required
def tenant_detail(request, tenant_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can view tenants.")

    tenant = get_owned_tenant(request, tenant_id)
    user_properties = Property.objects.filter(landlord=request.user)
    initial_password = build_tenant_initial_password(tenant.property.name, tenant.unit_number)
    context = {
        "page_key": "tenants",
        "tenant": tenant,
        "initial_password": initial_password,
        "default_password_active": bool(tenant.user and tenant.user.password_change_required),
        "tenants_payload": [
            serialize_tenant(item)
            for item in Tenant.objects.filter(landlord=request.user).select_related("property", "property_unit__unit_type")
        ],
        "tenant_dashboard_data": build_tenant_dashboard_data(
            Tenant.objects.filter(landlord=request.user).select_related("property", "property_unit__unit_type")
        ),
        "properties_payload": [serialize_property(item) for item in user_properties],
        "property_dashboard_data": build_property_dashboard_data(user_properties),
    }
    return render(request, "landlord/tenants/tenant_detail.html", context)


@login_required
def edit_tenant(request, tenant_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can edit tenants.")

    tenant = get_owned_tenant(request, tenant_id)
    user_properties = Property.objects.filter(landlord=request.user)
    original_unit = tenant.property_unit
    original_property = tenant.property
    initial = {}
    if request.method != "POST" and tenant.property_unit and tenant.property_unit.unit_type:
        initial["unit_type"] = tenant.property_unit.unit_type.unit_type

    form = TenantForm(request.POST or None, instance=tenant, landlord=request.user, initial=initial)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                updated_tenant = form.save(commit=False)
                updated_tenant.landlord = request.user
                initialize_rent_schedule(updated_tenant)
                ensure_tenant_user_account(updated_tenant)
                updated_tenant.save()

                if original_unit and original_unit.id != getattr(updated_tenant.property_unit, "id", None):
                    original_unit.is_occupied = False
                    original_unit.save(update_fields=["is_occupied"])

                if updated_tenant.property_unit:
                    updated_tenant.property_unit.is_occupied = True
                    updated_tenant.property_unit.save(update_fields=["is_occupied"])

                update_property_occupancy(original_property)
                if updated_tenant.property_id != original_property.id:
                    update_property_occupancy(updated_tenant.property)
        except ValidationError as error:
            form.add_error("email", error.message)
        else:
            messages.success(request, f"{updated_tenant.full_name} was updated.")
            return redirect("landlord-tenant-detail", tenant_id=updated_tenant.id)

    context = {
        "page_key": "tenants",
        "form": form,
        "user_properties": user_properties,
        "properties_payload": [serialize_property(item) for item in user_properties],
        "property_dashboard_data": build_property_dashboard_data(user_properties),
        "page_heading": f"Edit {tenant.full_name}",
        "page_description": "Update tenant details, assignment, and lease information without breaking the linked tenant account.",
        "submit_label": "Save Changes",
        "back_url": reverse("landlord-tenant-detail", args=[tenant.id]),
        "available_units_payload": build_available_units_payload(user_properties),
    }
    return render(request, "landlord/tenants/add_tenant.html", context)


@login_required
@require_POST
def delete_tenant(request, tenant_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can delete tenants.")

    tenant = get_owned_tenant(request, tenant_id)
    tenant_name = tenant.full_name
    property_obj = tenant.property
    unit = tenant.property_unit
    user = tenant.user

    with transaction.atomic():
        tenant.delete()
        if unit:
            unit.is_occupied = False
            unit.save(update_fields=["is_occupied"])
        update_property_occupancy(property_obj)
        if user:
            user.delete()

    messages.success(request, f"{tenant_name} was deleted.")
    return redirect("landlord-tenants")
