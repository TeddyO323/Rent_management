from datetime import datetime, timedelta
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

from .forms import BillForm, ComplaintForm, ComplaintStatusForm, LandlordLoginForm, LandlordSettingsAutomationForm, LandlordSettingsProfileForm, LeaseExtensionDecisionForm, LeaseExtensionRequestForm, MaintenanceExpenseForm, PaymentForm, PropertyForm, TenantAutopayForm, TenantForm, TenantPasswordChangeForm, TenantPaymentForm, TenantProfileForm, UnitTypeFormSet
from .models import Bill, Complaint, LandlordSettings, LeaseExtensionRequest, MaintenanceExpense, Notification, Payment, PaymentAllocation, Property, PropertyUnit, PropertyUnitType, Tenant, User

LANDLORD_PAGES = {
    "overview": "Overview",
    "properties": "Properties",
    "tenants": "Tenants",
    "payments": "Payments",
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


def get_or_create_landlord_settings(user):
    defaults = {
        "business_name": user.full_name or user.email,
        "support_email": user.email,
    }
    settings_obj, _ = LandlordSettings.objects.get_or_create(
        landlord=user,
        defaults=defaults,
    )
    return settings_obj


def notification_tone(priority):
    if priority == Notification.Priority.HIGH:
        return "needs-attention"
    if priority == Notification.Priority.MEDIUM:
        return "stable"
    return "high-performing"


def create_notification(
    recipient,
    *,
    title,
    message,
    category,
    priority=Notification.Priority.MEDIUM,
    tenant=None,
    property_obj=None,
    link_url="",
    dedupe_key="",
):
    if recipient is None:
        return None
    notification = None
    if dedupe_key:
        notification = Notification.objects.filter(
            recipient=recipient,
            dedupe_key=dedupe_key,
        ).first()
    if notification:
        updates = []
        for field, value in {
            "title": title,
            "message": message,
            "category": category,
            "priority": priority,
            "tenant": tenant,
            "property": property_obj,
            "link_url": link_url,
        }.items():
            if getattr(notification, field) != value:
                setattr(notification, field, value)
                updates.append(field)
        if updates:
            notification.save(update_fields=updates)
        return notification
    return Notification.objects.create(
        recipient=recipient,
        tenant=tenant,
        property=property_obj,
        category=category,
        priority=priority,
        title=title,
        message=message,
        link_url=link_url,
        dedupe_key=dedupe_key,
    )


def mark_notification_read(notification):
    if notification.is_read:
        return
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at"])


def serialize_notification(notification):
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "category": notification.category,
        "priority": notification.priority,
        "tone": notification_tone(notification.priority),
        "isRead": notification.is_read,
        "createdAt": timezone.localtime(notification.created_at).strftime("%b %d, %Y %I:%M %p"),
        "linkUrl": notification.link_url,
        "tenantName": notification.tenant.full_name if notification.tenant else "",
        "propertyName": notification.property.name if notification.property else "",
    }


def build_notification_rules(settings_obj):
    return [
        {
            "title": "Rent reminder cadence",
            "detail": f"Rent reminder notices go out {settings_obj.rent_reminder_days} day(s) before the due date.",
            "status": "Active" if settings_obj.rent_reminder_days else "Off",
        },
        {
            "title": "Overdue follow-up",
            "detail": f"Unpaid balances are escalated after {settings_obj.overdue_follow_up_days} day(s) overdue.",
            "status": "Active" if settings_obj.overdue_follow_up_days else "Off",
        },
        {
            "title": "Maintenance escalation",
            "detail": f"High-priority maintenance issues escalate after {settings_obj.maintenance_escalation_hours} hour(s).",
            "status": "Active" if settings_obj.maintenance_escalation_enabled else "Off",
        },
        {
            "title": "Owner digest",
            "detail": "Weekly owner-facing portfolio digest covering collections, occupancy, and maintenance load.",
            "status": "Active" if settings_obj.owner_digest_enabled else "Off",
        },
    ]


def build_landlord_notifications_page_data(user):
    notifications = Notification.objects.filter(
        recipient=user,
    ).select_related("tenant", "property")
    items = list(notifications)
    recent_tenant_updates = list(
        Notification.objects.filter(
            recipient__role=User.Role.TENANT,
            tenant__landlord=user,
        )
        .exclude(recipient=user)
        .select_related("recipient", "tenant", "property")
        .order_by("-created_at")[:8]
    )
    settings_obj = get_or_create_landlord_settings(user)
    return {
        "summary": {
            "total": len(items),
            "unread": sum(1 for item in items if not item.is_read),
            "highPriority": sum(1 for item in items if item.priority == Notification.Priority.HIGH and not item.is_read),
            "resolved": sum(1 for item in items if item.is_read),
        },
        "items": [serialize_notification(item) for item in items],
        "rules": build_notification_rules(settings_obj),
        "communicationFeed": [
            {
                **serialize_notification(item),
                "audience": item.tenant.full_name if item.tenant else item.recipient.full_name,
            }
            for item in recent_tenant_updates
        ],
    }


def build_tenant_notifications_page_data(tenant):
    notifications = list(
        Notification.objects.filter(
            recipient=tenant.user,
        ).select_related("tenant", "property")
    )
    return {
        "summary": {
            "total": len(notifications),
            "unread": sum(1 for item in notifications if not item.is_read),
            "highPriority": sum(1 for item in notifications if item.priority == Notification.Priority.HIGH and not item.is_read),
            "read": sum(1 for item in notifications if item.is_read),
        },
        "items": [serialize_notification(item) for item in notifications],
    }


def ensure_tenant_system_notifications(tenant):
    if not tenant.user:
        return
    if tenant.user.password_change_required:
        create_notification(
            tenant.user,
            tenant=tenant,
            property_obj=tenant.property,
            title="Change your password",
            message="Please update the default password from Settings to secure your tenant account.",
            category=Notification.Category.ACCOUNT,
            priority=Notification.Priority.HIGH,
            link_url=reverse("tenant-settings"),
            dedupe_key=f"tenant-password-change-{tenant.id}",
        )
    next_due_date = get_next_rent_due_date(tenant)
    if next_due_date:
        reminder_days = get_or_create_landlord_settings(tenant.landlord).rent_reminder_days
        days_until_due = (next_due_date - timezone.localdate()).days
        if 0 <= days_until_due <= reminder_days:
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Rent due soon",
                message=(
                    f"Your next rent payment is due on {next_due_date.strftime('%b %d, %Y')}. "
                    f"That is in {days_until_due} day{'s' if days_until_due != 1 else ''}."
                ),
                category=Notification.Category.PAYMENTS,
                priority=Notification.Priority.HIGH,
                link_url=reverse("tenant-receipts"),
                dedupe_key=f"tenant-rent-reminder-{tenant.id}-{next_due_date.isoformat()}",
            )
    if tenant.lease_type == Tenant.LeaseType.RENT and tenant.lease_end:
        days_to_lease_end = (tenant.lease_end - timezone.localdate()).days
        if 0 <= days_to_lease_end <= 45:
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Lease ending soon",
                message=f"Your current lease ends on {tenant.lease_end.strftime('%b %d, %Y')}. You can request an extension from Receipts & Payments.",
                category=Notification.Category.LEASE,
                priority=Notification.Priority.MEDIUM,
                link_url=reverse("tenant-receipts"),
                dedupe_key=f"tenant-lease-ending-{tenant.id}-{tenant.lease_end.isoformat()}",
            )


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


def serialize_extension_request(extension_request):
    return {
        "id": extension_request.id,
        "tenant": extension_request.tenant.full_name,
        "property": extension_request.tenant.property.name,
        "unit": extension_request.tenant.unit_number,
        "currentLeaseEnd": extension_request.tenant.lease_end.strftime("%b %d, %Y") if extension_request.tenant.lease_end else "Not set",
        "requestedEnd": extension_request.requested_end_date.strftime("%b %d, %Y"),
        "status": extension_request.status,
        "reason": extension_request.reason,
        "landlordNotes": extension_request.landlord_notes,
        "createdAt": extension_request.created_at.strftime("%b %d, %Y"),
        "detailUrl": reverse("landlord-extension-request-detail", args=[extension_request.id]),
    }


def build_landlord_overview_data(user, user_properties, user_tenants):
    properties = list(user_properties.prefetch_related("unit_types"))
    property_dashboard_data = build_property_dashboard_data(user_properties)
    confirmed_payments = Payment.objects.filter(landlord=user, status=Payment.Status.CONFIRMED)
    pending_cash_payments = Payment.objects.filter(
        landlord=user,
        status=Payment.Status.PENDING,
    ).select_related("tenant", "property")
    unresolved_complaints = Complaint.objects.filter(
        tenant__landlord=user,
    ).exclude(status__in=[Complaint.Status.RESOLVED, Complaint.Status.REJECTED])
    pending_cash_count = pending_cash_payments.count()
    overdue_accounts = Tenant.objects.filter(
        landlord=user,
        bills__status__in=[Bill.Status.UNPAID, Bill.Status.PARTIALLY_PAID],
    ).distinct().count()
    pending_extensions = LeaseExtensionRequest.objects.filter(
        tenant__landlord=user,
        status__in=[LeaseExtensionRequest.Status.PENDING, LeaseExtensionRequest.Status.UNDER_REVIEW],
    ).select_related("tenant", "tenant__property")
    current_month_start = timezone.localdate().replace(day=1)
    monthly_collection = sum(item.amount for item in confirmed_payments if item.paid_on >= current_month_start)
    total_units = property_dashboard_data["metricSet"][1]["value"]
    occupied_units = property_dashboard_data["metricSet"][2]["value"]
    vacancy_count = max(total_units - occupied_units, 0)

    months = []
    today = timezone.localdate()
    for offset in range(5, -1, -1):
        month_anchor = today.replace(day=1) - timedelta(days=offset * 30)
        month_start = month_anchor.replace(day=1)
        months.append((month_start.strftime("%b"), month_start))
    rent_chart = {"labels": [], "expected": [], "collected": []}
    recurring_rent = sum((tenant.monthly_rent or Decimal("0")) for tenant in user_tenants if tenant.lease_type == Tenant.LeaseType.RENT)
    for label, month_start in months:
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        month_payments = sum(
            payment.amount
            for payment in confirmed_payments
            if month_start <= payment.paid_on < month_end
        )
        rent_chart["labels"].append(label)
        rent_chart["expected"].append(float(recurring_rent / Decimal("1000000")) if recurring_rent else 0)
        rent_chart["collected"].append(float(month_payments / Decimal("1000000")) if month_payments else 0)

    featured_properties = sorted(properties, key=lambda item: (item.occupancy, item.occupied_units), reverse=True)[:3]
    alerts = []
    if pending_extensions.exists():
        latest_extension = pending_extensions.first()
        alerts.append({
            "title": "Lease extension requests waiting",
            "copy": f"{pending_extensions.count()} request(s) need review, including {latest_extension.tenant.full_name} at {latest_extension.tenant.property.name}.",
            "tone": "warning",
            "time": "Needs review",
            "actionUrl": reverse("landlord-extension-request-detail", args=[latest_extension.id]),
            "actionLabel": "Review request",
        })
    if pending_cash_count:
        alerts.append({
            "title": "Cash approvals are pending",
            "copy": f"{pending_cash_count} tenant-submitted cash payment(s) still need landlord approval.",
            "tone": "info",
            "time": "Payments queue",
            "actionUrl": reverse("landlord-payments"),
            "actionLabel": "Open payments",
        })
    if unresolved_complaints.exists():
        latest_complaint = unresolved_complaints.select_related("tenant", "tenant__property").first()
        alerts.append({
            "title": "Maintenance needs attention",
            "copy": f"{unresolved_complaints.count()} unresolved complaint(s), including '{latest_complaint.title}' from {latest_complaint.tenant.full_name}.",
            "tone": "warning",
            "time": "Maintenance",
            "actionUrl": reverse("landlord-complaint-detail", args=[latest_complaint.id]),
            "actionLabel": "Open complaint",
        })
    if overdue_accounts:
        alerts.append({
            "title": "Overdue balances are open",
            "copy": f"{overdue_accounts} tenant account(s) still carry unpaid or partially paid bills.",
            "tone": "warning",
            "time": "Collections",
            "actionUrl": reverse("landlord-bills"),
            "actionLabel": "Review bills",
        })
    if vacancy_count:
        at_risk_property = min(properties, key=lambda item: item.occupancy, default=None)
        alerts.append({
            "title": "Vacancy pressure remains",
            "copy": (
                f"{vacancy_count} units are vacant across the portfolio. {at_risk_property.name} needs the most leasing attention."
                if at_risk_property else
                f"{vacancy_count} units are vacant across the portfolio."
            ),
            "tone": "info",
            "time": "Leasing",
            "actionUrl": reverse("landlord-properties"),
            "actionLabel": "Open properties",
        })

    if not alerts:
        alerts.append({
            "title": "Portfolio is steady",
            "copy": "No urgent approvals, overdue balances, or complaint escalations need action right now.",
            "tone": "success",
            "time": "All clear",
            "actionUrl": reverse("landlord-tenants"),
            "actionLabel": "Review tenants",
        })

    quick_actions = [
        {
            "title": "Lease extension queue",
            "count": pending_extensions.count(),
            "copy": "Tenant renewal requests that still need a landlord decision.",
            "url": reverse("landlord-tenants"),
            "button": "Open tenant queue",
            "tone": "needs-attention" if pending_extensions.exists() else "stable",
        },
        {
            "title": "Cash approvals",
            "count": pending_cash_count,
            "copy": "Submitted cash payments waiting for approval before they clear balances.",
            "url": reverse("landlord-payments"),
            "button": "Review payments",
            "tone": "needs-attention" if pending_cash_count else "stable",
        },
        {
            "title": "Maintenance follow-up",
            "count": unresolved_complaints.count(),
            "copy": "Open complaints still waiting for landlord or management action.",
            "url": reverse("landlord-maintenance"),
            "button": "Open maintenance",
            "tone": "needs-attention" if unresolved_complaints.exists() else "stable",
        },
        {
            "title": "Overdue bill review",
            "count": overdue_accounts,
            "copy": "Tenant accounts that still need billing follow-up or collection action.",
            "url": reverse("landlord-bills"),
            "button": "Open bills",
            "tone": "needs-attention" if overdue_accounts else "stable",
        },
    ]

    return {
        "hero": {
            "chips": [
                {"value": f"{len(properties)} Properties", "label": "Tracked in SmartRent"},
                {"value": f"{occupied_units}/{total_units} Units", "label": "Currently occupied"},
                {"value": f"{len(alerts)} Priorities", "label": "Live actions to review"},
            ],
            "spotlights": [
                {
                    "label": "Collection pace",
                    "value": f"KSh {int(monthly_collection):,}",
                    "text": "Confirmed payments recorded this month across rent, utilities, and other approved charges.",
                },
                {
                    "label": "Next review queue",
                    "value": f"{pending_extensions.count()} extension request(s)",
                    "text": "Lease extension decisions can now be reviewed and approved from the landlord workspace.",
                },
            ],
        },
        "metrics": [
            {
                "label": "Monthly Collection",
                "value": float(monthly_collection),
                "format": "currency",
                "copy": "Confirmed payments recorded in the current month.",
                "trendLabel": "Live data",
                "trendStyle": "positive",
                "icon": "fa-coins",
                "accent": True,
                "iconTone": "",
            },
            {
                "label": "Occupancy Rate",
                "value": property_dashboard_data["hero"]["occupancyRate"],
                "format": "percent",
                "copy": "Derived from the configured unit inventory and active occupancies.",
                "trendLabel": "Live data",
                "trendStyle": "positive",
                "icon": "fa-door-open",
                "accent": False,
                "iconTone": "mint",
            },
            {
                "label": "Open Maintenance Tickets",
                "value": unresolved_complaints.count(),
                "format": "number",
                "copy": "Complaints that are still pending or in progress.",
                "trendLabel": "Live data",
                "trendStyle": "negative" if unresolved_complaints.exists() else "positive",
                "icon": "fa-screwdriver-wrench",
                "accent": False,
                "iconTone": "gold",
            },
            {
                "label": "Overdue Accounts",
                "value": overdue_accounts,
                "format": "number",
                "copy": "Tenant accounts that still carry unpaid balances.",
                "trendLabel": "Bills-driven",
                "trendStyle": "negative" if overdue_accounts else "positive",
                "icon": "fa-triangle-exclamation",
                "accent": False,
                "iconTone": "rose",
            },
        ],
        "rentChart": rent_chart,
        "occupancyBreakdown": property_dashboard_data["occupancyBreakdown"],
        "quickActions": quick_actions,
        "featuredProperties": [
            {
                "name": property_obj.name,
                "location": property_obj.location,
                "status": property_obj.status,
                "units": property_obj.units,
                "occupiedUnits": property_obj.occupied_units,
                "occupancy": property_obj.occupancy,
            }
            for property_obj in featured_properties
        ],
        "alerts": alerts[:4],
        "extensionQueue": [
            {
                "tenant": item.tenant.full_name,
                "property": item.tenant.property.name,
                "unit": item.tenant.unit_number,
                "requestedEnd": item.requested_end_date.strftime("%b %d, %Y"),
                "status": item.status,
                "detailUrl": reverse("landlord-extension-request-detail", args=[item.id]),
            }
            for item in pending_extensions[:5]
        ],
        "cashApprovals": [
            {
                "tenant": item.tenant.full_name,
                "property": item.property.name,
                "amount": float(item.amount),
                "date": item.paid_on.strftime("%b %d, %Y"),
                "detailUrl": reverse("landlord-payment-detail", args=[item.id]),
            }
            for item in pending_cash_payments[:5]
        ],
    }


def build_landlord_analytics_data(user, user_properties, user_tenants):
    property_dashboard_data = build_property_dashboard_data(user_properties)
    payments = list(Payment.objects.filter(landlord=user, status=Payment.Status.CONFIRMED).select_related("tenant", "property"))
    bills = list(Bill.objects.filter(landlord=user).select_related("tenant", "property"))
    complaints = list(Complaint.objects.filter(tenant__landlord=user).select_related("tenant", "tenant__property"))
    active_tenants = [tenant for tenant in user_tenants if tenant.status != Tenant.Status.INACTIVE]
    autopay_count = sum(1 for tenant in active_tenants if tenant.autopay_enabled)
    autopay_rate = round((autopay_count / len(active_tenants)) * 100, 1) if active_tenants else 0

    total_billed = sum((bill.amount for bill in bills), Decimal("0"))
    total_paid = sum((payment.amount for payment in payments), Decimal("0"))
    arrears_balance = sum((bill.remaining_amount for bill in bills if bill.status != Bill.Status.PAID), Decimal("0"))
    collection_rate = round(float((total_paid / total_billed) * 100), 1) if total_billed else 0
    arrears_ratio = round(float((arrears_balance / total_billed) * 100), 1) if total_billed else 0

    months = []
    today = timezone.localdate()
    for offset in range(5, -1, -1):
        month_anchor = today.replace(day=1) - timedelta(days=offset * 30)
        month_start = month_anchor.replace(day=1)
        months.append((month_start.strftime("%b"), month_start))
    revenue_chart = {"labels": [], "expected": [], "collected": []}
    recurring_rent = sum((tenant.monthly_rent or Decimal("0")) for tenant in user_tenants if tenant.lease_type == Tenant.LeaseType.RENT)
    for label, month_start in months:
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        month_payments = sum(payment.amount for payment in payments if month_start <= payment.paid_on < month_end)
        revenue_chart["labels"].append(label)
        revenue_chart["expected"].append(float(recurring_rent / Decimal("1000000")) if recurring_rent else 0)
        revenue_chart["collected"].append(float(month_payments / Decimal("1000000")) if month_payments else 0)

    category_totals = {}
    for item in complaints:
        category_totals[item.category] = category_totals.get(item.category, 0) + 1

    occupancy_breakdown = property_dashboard_data["occupancyBreakdown"]
    benchmark_cards = [
        {
            "title": "Collections performance",
            "detail": "Share of all billed value that has already been recovered through confirmed payments.",
            "value": f"{collection_rate:.1f}%",
        },
        {
            "title": "Autopay adoption",
            "detail": "Active tenants who have already enabled recurring rent payments.",
            "value": f"{autopay_rate:.1f}%",
        },
        {
            "title": "Arrears exposure",
            "detail": "Outstanding balance as a share of the full billed amount across the portfolio.",
            "value": f"{arrears_ratio:.1f}%",
        },
    ]

    strongest_property = max(user_properties, key=lambda item: item.occupancy, default=None)
    weakest_property = min(user_properties, key=lambda item: item.occupancy, default=None)
    insight_title = "Portfolio recommendation"
    insight_copy = "Start adding properties and tenant activity to unlock portfolio recommendations."
    if weakest_property and strongest_property and weakest_property.id != strongest_property.id:
        insight_title = f"{weakest_property.name} needs the next operating push"
        insight_copy = (
            f"{weakest_property.name} is your weakest occupancy signal at {weakest_property.occupancy}% while "
            f"{strongest_property.name} is leading at {strongest_property.occupancy}%. Focus leasing follow-up and "
            "arrears review on the weakest property first."
        )
    elif strongest_property:
        insight_title = f"{strongest_property.name} is setting the pace"
        insight_copy = (
            f"{strongest_property.name} is currently leading the portfolio at {strongest_property.occupancy}% occupancy. "
            "Use that property’s collection and tenant posture as the benchmark for the rest of the portfolio."
        )

    return {
        "metrics": [
            {
                "label": "Collection Rate",
                "value": collection_rate,
                "format": "percent",
                "copy": "Confirmed payments as a share of the total billed portfolio value.",
                "trendLabel": "Live data",
                "trendStyle": "positive" if collection_rate >= 70 else "negative",
                "icon": "fa-chart-line",
                "accent": True,
                "iconTone": "",
            },
            {
                "label": "Autopay Adoption",
                "value": autopay_rate,
                "format": "percent",
                "copy": "How many active tenants are already enrolled in automatic rent collection.",
                "trendLabel": "Tenant-driven",
                "trendStyle": "positive" if autopay_rate >= 50 else "negative",
                "icon": "fa-bullseye",
                "accent": False,
                "iconTone": "mint",
            },
            {
                "label": "Arrears Ratio",
                "value": arrears_ratio,
                "format": "percent",
                "copy": "Outstanding balance compared with all billed value in the portfolio.",
                "trendLabel": "Bills-driven",
                "trendStyle": "negative" if arrears_ratio > 20 else "positive",
                "icon": "fa-wave-square",
                "accent": False,
                "iconTone": "gold",
            },
            {
                "label": "Portfolio Occupancy",
                "value": property_dashboard_data["hero"]["occupancyRate"],
                "format": "percent",
                "copy": "Configured unit occupancy across all tracked properties.",
                "trendLabel": "Live data",
                "trendStyle": "positive" if property_dashboard_data["hero"]["occupancyRate"] >= 80 else "negative",
                "icon": "fa-door-open",
                "accent": False,
                "iconTone": "rose",
            },
        ],
        "revenueChart": revenue_chart,
        "maintenanceCategories": {
            "labels": list(category_totals.keys()) or ["No complaints"],
            "values": list(category_totals.values()) or [0],
        },
        "occupancyBreakdown": occupancy_breakdown,
        "benchmarkCards": benchmark_cards,
        "insight": {
            "title": insight_title,
            "copy": insight_copy,
        },
    }


def build_landlord_settings_dashboard_data(user, settings_obj):
    active_tenants = Tenant.objects.filter(landlord=user).exclude(status=Tenant.Status.INACTIVE)
    active_automations = sum(
        1
        for value in [
            settings_obj.owner_digest_enabled,
            settings_obj.weekly_report_enabled,
            settings_obj.maintenance_escalation_enabled,
            settings_obj.autopay_nudges_enabled,
        ]
        if value
    )
    integrations = [
        {
            "name": "M-Pesa Collections",
            "detail": "Primary recurring payment rail for tenant collections and tenant-submitted transactions.",
            "status": "Connected",
        },
        {
            "name": "Email Delivery",
            "detail": f"Support email is currently set to {settings_obj.support_email or user.email}.",
            "status": "Configured" if (settings_obj.support_email or user.email) else "Needs setup",
        },
        {
            "name": "Reminder Engine",
            "detail": f"Rent reminders run {settings_obj.rent_reminder_days} day(s) before due date and overdue follow-up begins after {settings_obj.overdue_follow_up_days} day(s).",
            "status": "Configured",
        },
        {
            "name": "Maintenance Escalation",
            "detail": f"Issue escalation is {'enabled' if settings_obj.maintenance_escalation_enabled else 'disabled'} at {settings_obj.maintenance_escalation_hours} hour(s).",
            "status": "Live" if settings_obj.maintenance_escalation_enabled else "Paused",
        },
    ]
    access_roles = [
        {
            "role": "Landlord",
            "permission": "Full portfolio control, approvals, analytics, and settings.",
            "members": 1,
        },
        {
            "role": "Tenants",
            "permission": "Self-service access to receipts, complaints, and profile details.",
            "members": active_tenants.count(),
        },
    ]
    return {
        "metrics": {
            "integrations": len(integrations),
            "active_automations": active_automations,
            "permission_roles": len(access_roles),
            "scheduled_reports": 1 if settings_obj.weekly_report_enabled else 0,
        },
        "settingsCards": [
            {
                "title": "Owner digest emails",
                "description": "Send portfolio summary emails using the current support and report settings.",
                "enabled": settings_obj.owner_digest_enabled,
            },
            {
                "title": "Weekly reporting",
                "description": "Keep weekly portfolio reports and digests active for management review.",
                "enabled": settings_obj.weekly_report_enabled,
            },
            {
                "title": "Maintenance escalation",
                "description": "Escalate unresolved maintenance issues using the configured SLA window.",
                "enabled": settings_obj.maintenance_escalation_enabled,
            },
            {
                "title": "Autopay nudges",
                "description": "Encourage manual tenants to move onto recurring rent collection.",
                "enabled": settings_obj.autopay_nudges_enabled,
            },
        ],
        "integrations": integrations,
        "accessRoles": access_roles,
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
                "value": float(tenant.current_balance + tenant.rent_credit_balance),
                "format": "currency",
                "copy": "Credit sitting on your account, including any prepaid rent waiting for the next due date.",
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


def get_rent_schedule_anchor(tenant):
    if not tenant.lease_start:
        return None
    naive = datetime.combine(tenant.lease_start, datetime.min.time())
    return timezone.make_aware(naive, timezone.get_current_timezone())


def get_next_rent_due_date(tenant):
    if tenant.lease_type != Tenant.LeaseType.RENT or not tenant.monthly_rent:
        return None
    anchor = tenant.last_rent_charge_at or get_rent_schedule_anchor(tenant)
    if anchor is None:
        return None
    return timezone.localtime(anchor + get_rent_billing_interval()).date()


def get_rent_due_notice(tenant):
    next_due_date = get_next_rent_due_date(tenant)
    if not next_due_date:
        return None
    days_until_due = (next_due_date - timezone.localdate()).days
    if 0 <= days_until_due <= 5:
        return {
            "title": "Rent reminder",
            "copy": (
                f"Your next rent payment is due on {next_due_date.strftime('%b %d, %Y')}. "
                f"That is in {days_until_due} day{'s' if days_until_due != 1 else ''}. "
                "You can pay now and SmartRent will apply it on the due date."
            ),
        }
    return None


def initialize_rent_schedule(tenant):
    if tenant.lease_type != Tenant.LeaseType.RENT or not tenant.monthly_rent:
        tenant.last_rent_charge_at = None
        return
    tenant.last_rent_charge_at = get_rent_schedule_anchor(tenant)


def process_due_rent_bills(tenants):
    now = timezone.now()
    interval = get_rent_billing_interval()
    for tenant in tenants:
        if tenant.lease_type != Tenant.LeaseType.RENT or not tenant.monthly_rent:
            continue
        if tenant.lease_start > timezone.localdate():
            continue

        if tenant.last_rent_charge_at is None:
            tenant.last_rent_charge_at = get_rent_schedule_anchor(tenant) or now
            tenant.save(update_fields=["last_rent_charge_at"])

        charge_time = tenant.last_rent_charge_at
        while charge_time + interval <= now:
            charge_time += interval
            if tenant.lease_end and charge_time.date() > tenant.lease_end:
                break
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
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="New rent bill added",
                message=f"A rent bill for {tenant.property.name} was created and is due on {bill.due_date.strftime('%b %d, %Y')}.",
                category=Notification.Category.PAYMENTS,
                priority=Notification.Priority.HIGH,
                link_url=reverse("tenant-bill-detail", args=[bill.id]) if tenant.user else "",
            )
            create_notification(
                tenant.landlord,
                tenant=tenant,
                property_obj=tenant.property,
                title="Automatic rent charge created",
                message=f"{tenant.full_name} was billed {bill.amount} for rent at {tenant.property.name}.",
                category=Notification.Category.PAYMENTS,
                priority=Notification.Priority.MEDIUM,
                link_url=reverse("landlord-bills"),
            )
            process_rent_autopay(tenant, Bill.objects.filter(id=bill.id))
        if charge_time != tenant.last_rent_charge_at:
            tenant.last_rent_charge_at = charge_time
            tenant.save(update_fields=["last_rent_charge_at"])


def build_tenant_receipts_data(tenant):
    bills = list(tenant.bills.select_related("property").order_by("-created_at"))
    payments = list(tenant.payments.select_related("property").order_by("-paid_on", "-created_at"))
    total_due = sum((bill.remaining_amount for bill in bills if bill.status != Bill.Status.PAID), Decimal("0"))
    total_credit = tenant.current_balance + tenant.rent_credit_balance
    transactions = []
    for bill in bills:
        transactions.append(
            {
                "type": "Bill",
                "title": bill.title,
                "category": bill.category,
                "amount": float(bill.remaining_amount),
                "originalAmount": float(bill.amount),
                "amountPaid": float(bill.amount - bill.remaining_amount),
                "balance": float(bill.remaining_amount),
                "date": bill.created_at.strftime("%b %d, %Y"),
                "sortDate": bill.created_at.isoformat(),
                "method": "Issued",
                "status": bill.status,
                "statusLabel": bill.status,
                "descriptor": bill.category,
                "detailUrl": reverse("tenant-bill-detail", args=[bill.id]),
            }
        )
    for payment in payments:
        transactions.append(
            {
                "type": "Payment",
                "title": f"{payment.scope} payment",
                "amount": float(payment.amount),
                "originalAmount": float(payment.amount),
                "amountPaid": float(payment.amount),
                "balance": 0.0,
                "date": payment.paid_on.strftime("%b %d, %Y"),
                "sortDate": payment.paid_on.isoformat(),
                "method": payment.method,
                "status": payment.status,
                "statusLabel": payment.status,
                "scope": payment.scope,
                "descriptor": payment.scope,
                "detailUrl": reverse("tenant-payment-detail", args=[payment.id]),
            }
        )
    transactions.sort(key=lambda item: item["sortDate"], reverse=True)
    return {
        "transactions": transactions,
        "summary": {
            "total_due": float(total_due),
            "current_balance": float(total_credit),
            "rent_credit_balance": float(tenant.rent_credit_balance),
        },
        "next_due_date": get_next_rent_due_date(tenant).strftime("%b %d, %Y") if get_next_rent_due_date(tenant) else "",
    }


def build_tenant_complaints_payload(tenant):
    complaints = list(tenant.complaints.all())
    summary = {
        "total": len(complaints),
        "pending": sum(1 for item in complaints if item.status == Complaint.Status.PENDING),
        "inProgress": sum(1 for item in complaints if item.status == Complaint.Status.IN_PROGRESS),
        "resolved": sum(1 for item in complaints if item.status == Complaint.Status.RESOLVED),
    }
    items = [
        {
            "id": item.id,
            "title": item.title,
            "category": item.category,
            "description": item.description,
            "status": item.status,
            "landlordNotes": item.landlord_notes,
            "createdAt": item.created_at.strftime("%b %d, %Y"),
            "detailUrl": reverse("tenant-complaint-detail", args=[item.id]),
        }
        for item in complaints
    ]
    return {
        "summary": summary,
        "items": items,
    }


def build_tenant_notifications(tenant):
    ensure_tenant_system_notifications(tenant)
    notifications = Notification.objects.filter(
        recipient=tenant.user,
    ).order_by("is_read", "-created_at")[:8]
    return [
        {
            "title": item.title,
            "copy": item.message,
            "tone": notification_tone(item.priority),
            "createdAt": timezone.localtime(item.created_at).strftime("%b %d, %Y %I:%M %p"),
            "linkUrl": item.link_url,
        }
        for item in notifications
    ]


def build_tenant_analytics_data(tenant):
    complaint_count = tenant.complaints.count()
    extension_count = tenant.lease_extension_requests.count()
    return {
        "metrics": [
            {"label": "Open complaints", "value": complaint_count, "format": "number", "icon": "fa-triangle-exclamation"},
            {"label": "Extension requests", "value": extension_count, "format": "number", "icon": "fa-file-signature"},
            {"label": "Current balance", "value": float(tenant.current_balance + tenant.rent_credit_balance), "format": "currency", "icon": "fa-wallet"},
            {"label": "Autopay", "value": "Enabled" if tenant.autopay_enabled else "Manual", "icon": "fa-repeat"},
        ],
        "charts": {
            "charges": [
                {"label": "Occupancy charge", "value": float(tenant.monthly_rent or tenant.purchase_price or 0), "color": "#2f74ff"},
                {"label": "Current balance", "value": float(tenant.current_balance + tenant.rent_credit_balance), "color": "#1bc6a6"},
            ],
            "activity": {
                "labels": ["Complaints", "Extensions", "Notifications"],
                "values": [complaint_count, extension_count, Notification.objects.filter(recipient=tenant.user).count() if tenant.user else 0],
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
    if not bill.tenant or bill.remaining_amount <= Decimal("0"):
        update_bill_status(bill)
        bill.save(update_fields=["remaining_amount", "status"])
        return Decimal("0")

    applied = Decimal("0")

    if bill.category == Bill.Category.RENT and bill.tenant.rent_credit_balance > Decimal("0"):
        rent_applied = min(bill.tenant.rent_credit_balance, bill.remaining_amount)
        bill.remaining_amount -= rent_applied
        bill.tenant.rent_credit_balance -= rent_applied
        applied += rent_applied

    if bill.category != Bill.Category.RENT and bill.remaining_amount > Decimal("0") and bill.tenant.current_balance > Decimal("0"):
        general_applied = min(bill.tenant.current_balance, bill.remaining_amount)
        bill.remaining_amount -= general_applied
        bill.tenant.current_balance -= general_applied
        applied += general_applied

    update_bill_status(bill)
    bill.tenant.save(update_fields=["current_balance", "rent_credit_balance"])
    bill.save(update_fields=["remaining_amount", "status"])
    return applied


def store_payment_credit(tenant, amount, payment):
    if amount <= Decimal("0"):
        return
    if payment.scope == Payment.Scope.RENT or (payment.bill and payment.bill.category == Bill.Category.RENT):
        tenant.rent_credit_balance += amount
        tenant.save(update_fields=["rent_credit_balance"])
    else:
        tenant.current_balance += amount
        tenant.save(update_fields=["current_balance"])


def allocate_payment_to_bills(payment, open_bills=None):
    if payment.allocations.exists():
        return Decimal("0")

    remaining_payment = payment.amount
    if open_bills is None:
        open_bills = Bill.objects.filter(tenant=payment.tenant)
    open_bills = open_bills.exclude(status=Bill.Status.PAID).order_by("created_at", "id")

    for bill in open_bills:
        if remaining_payment <= Decimal("0"):
            break
        allocation = min(remaining_payment, bill.remaining_amount)
        if allocation <= Decimal("0"):
            continue
        PaymentAllocation.objects.create(
            payment=payment,
            bill=bill,
            amount=allocation,
        )
        bill.remaining_amount -= allocation
        remaining_payment -= allocation
        update_bill_status(bill)
        bill.save(update_fields=["remaining_amount", "status"])

    if remaining_payment > Decimal("0"):
        store_payment_credit(payment.tenant, remaining_payment, payment)

    return remaining_payment


def get_payment_bill_queryset(payment):
    if payment.scope == Payment.Scope.BILL and payment.bill_id:
        return Bill.objects.filter(id=payment.bill_id, tenant=payment.tenant)
    if payment.scope == Payment.Scope.BILL and payment.selected_bill_ids:
        bill_ids = [int(item) for item in payment.selected_bill_ids.split(",") if item.strip().isdigit()]
        return Bill.objects.filter(id__in=bill_ids, tenant=payment.tenant).order_by("due_date", "created_at")
    if payment.scope == Payment.Scope.RENT:
        return Bill.objects.filter(tenant=payment.tenant, category=Bill.Category.RENT)
    return Bill.objects.filter(tenant=payment.tenant)


def finalize_payment(payment):
    if payment.status != Payment.Status.CONFIRMED:
        return Decimal("0")
    remaining = allocate_payment_to_bills(payment, get_payment_bill_queryset(payment))
    create_notification(
        payment.tenant.user,
        tenant=payment.tenant,
        property_obj=payment.property,
        title="Payment confirmed",
        message=f"Your {payment.method} payment of KSh {payment.amount} was confirmed for {payment.property.name}.",
        category=Notification.Category.PAYMENTS,
        priority=Notification.Priority.MEDIUM,
        link_url=reverse("tenant-payment-detail", args=[payment.id]) if payment.tenant.user else "",
    )
    create_notification(
        payment.landlord,
        tenant=payment.tenant,
        property_obj=payment.property,
        title="Tenant payment confirmed",
        message=f"{payment.tenant.full_name} paid KSh {payment.amount} by {payment.method}.",
        category=Notification.Category.PAYMENTS,
        priority=Notification.Priority.MEDIUM,
        link_url=reverse("landlord-payment-detail", args=[payment.id]),
    )
    return remaining


def process_rent_autopay(tenant, bill_queryset=None):
    if (
        tenant.lease_type != Tenant.LeaseType.RENT
        or not tenant.autopay_enabled
        or not tenant.monthly_rent
    ):
        return 0

    rent_bills = bill_queryset or Bill.objects.filter(tenant=tenant, category=Bill.Category.RENT)
    rent_bills = rent_bills.exclude(status=Bill.Status.PAID).order_by("created_at", "id")
    processed = 0

    for bill in rent_bills:
        if bill.remaining_amount <= Decimal("0"):
            continue
        payment = Payment.objects.create(
            landlord=tenant.landlord,
            property=tenant.property,
            tenant=tenant,
            scope=Payment.Scope.RENT,
            method=Payment.Method.CARD,
            status=Payment.Status.CONFIRMED,
            amount=bill.remaining_amount,
            paid_on=timezone.localdate(),
            notes="Collected automatically in test mode from the saved tenant autopay details.",
        )
        allocate_payment_to_bills(payment, Bill.objects.filter(id=bill.id))
        create_notification(
            tenant.user,
            tenant=tenant,
            property_obj=tenant.property,
            title="Autopay collected your rent",
            message=f"Your saved card details were used to pay the rent bill for {bill.due_date.strftime('%b %d, %Y')}.",
            category=Notification.Category.PAYMENTS,
            priority=Notification.Priority.MEDIUM,
            link_url=reverse("tenant-payment-detail", args=[payment.id]) if tenant.user else "",
        )
        create_notification(
            tenant.landlord,
            tenant=tenant,
            property_obj=tenant.property,
            title="Autopay collection succeeded",
            message=f"Autopay collected KSh {payment.amount} from {tenant.full_name} for {tenant.property.name}.",
            category=Notification.Category.PAYMENTS,
            priority=Notification.Priority.LOW,
            link_url=reverse("landlord-payment-detail", args=[payment.id]),
        )
        processed += 1

    return processed


def serialize_payment(payment_obj):
    return {
        "id": payment_obj.id,
        "tenant": payment_obj.tenant.full_name,
        "property": payment_obj.property.name,
        "unit": payment_obj.tenant.unit_number,
        "amount": float(payment_obj.amount),
        "date": payment_obj.paid_on.strftime("%b %d, %Y"),
        "status": payment_obj.status,
        "category": payment_obj.scope,
        "method": payment_obj.method,
        "approveUrl": reverse("landlord-approve-payment", args=[payment_obj.id]) if payment_obj.status == Payment.Status.PENDING else "",
        "detailUrl": reverse("landlord-payment-detail", args=[payment_obj.id]),
    }


def build_payments_dashboard_data(user, user_tenants):
    payments = list(
        Payment.objects.filter(landlord=user).select_related("tenant", "property", "bill")
    )
    confirmed_payments = [item for item in payments if item.status == Payment.Status.CONFIRMED]
    month_start = timezone.localdate().replace(day=1)
    month_payments = [item for item in confirmed_payments if item.paid_on >= month_start]
    collected_this_month = sum(item.amount for item in month_payments)
    outstanding_balance = sum(
        item.remaining_amount
        for item in Bill.objects.filter(landlord=user).exclude(status=Bill.Status.PAID)
    )
    autopay_count = sum(1 for tenant in user_tenants if tenant.autopay_enabled)
    autopay_success = round((autopay_count / len(user_tenants)) * 100, 1) if user_tenants else 0
    methods = {}
    for payment in confirmed_payments:
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
            "pending_cash": sum(1 for item in payments if item.status == Payment.Status.PENDING),
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

    accumulated = {}
    for bill in bills:
        key = (bill.property_id, bill.tenant_id if bill.tenant else None)
        if key not in accumulated:
            accumulated[key] = {
                "bill_id": bill.id,
                "property": bill.property.name,
                "tenant": bill.tenant.full_name if bill.tenant else "Property-wide",
                "tenant_id": bill.tenant_id,
                "balance": Decimal("0"),
                "amount_paid": Decimal("0"),
                "original_amount": Decimal("0"),
                "categories": set(),
            }
        accumulated[key]["original_amount"] += bill.amount
        accumulated[key]["amount_paid"] += (bill.amount - bill.remaining_amount)
        accumulated[key]["balance"] += bill.remaining_amount
        accumulated[key]["categories"].add(bill.category)

    accumulated_bills = []
    total_amount_due = Decimal("0")
    unpaid_count = sum(1 for bill in bills if bill.status != Bill.Status.PAID)
    for entry in accumulated.values():
        balance = entry["balance"]
        amount_paid = entry["amount_paid"]
        original_amount = entry["original_amount"]
        total_amount_due += balance
        if balance <= Decimal("0"):
            status = "Paid"
            status_class = "high-performing"
        elif amount_paid > Decimal("0"):
            status = "Partially Paid"
            status_class = "stable"
        else:
            status = "Unpaid"
            status_class = "vacancy-risk"
        accumulated_bills.append({
            "property": entry["property"],
            "tenant": entry["tenant"],
            "amount_due": float(balance),
            "amount_paid": float(amount_paid),
            "original_amount": float(original_amount),
            "categories": sorted(entry["categories"]),
            "status": status,
            "status_class": status_class,
            "detail_url": reverse("landlord-bill-detail", args=[entry["bill_id"]]),
        })

    accumulated_bills.sort(key=lambda x: x["amount_due"], reverse=True)

    properties = sorted({item["property"] for item in accumulated_bills})
    statuses = ["Unpaid", "Partially Paid", "Paid"]
    categories = sorted({category for item in accumulated_bills for category in item["categories"]})

    return {
        "accumulated_bills": accumulated_bills,
        "total_amount_due": float(total_amount_due),
        "unpaid_count": unpaid_count,
        "filters": {
            "properties": properties,
            "statuses": statuses,
            "categories": categories,
        },
    }


def build_landlord_bill_detail_data(bill):
    allocations = list(
        bill.allocations.select_related("payment", "payment__tenant", "payment__property")
    )
    return {
        "original_amount": bill.amount,
        "amount_paid": bill.amount - bill.remaining_amount,
        "remaining_amount": bill.remaining_amount,
        "allocations": allocations,
    }


def serialize_complaint(complaint_obj):
    return {
        "id": complaint_obj.id,
        "title": complaint_obj.title,
        "tenant": complaint_obj.tenant.full_name,
        "property": complaint_obj.tenant.property.name,
        "unit": complaint_obj.tenant.unit_number,
        "category": complaint_obj.category,
        "status": complaint_obj.status,
        "description": complaint_obj.description,
        "landlordNotes": complaint_obj.landlord_notes,
        "created_at": complaint_obj.created_at.strftime("%b %d, %Y"),
        "detailUrl": reverse("landlord-complaint-detail", args=[complaint_obj.id]),
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
            "open_tickets": sum(1 for item in complaints if item.status not in [Complaint.Status.RESOLVED, Complaint.Status.REJECTED]),
            "in_progress": sum(1 for item in complaints if item.status == Complaint.Status.IN_PROGRESS),
            "resolved": sum(1 for item in complaints if item.status == Complaint.Status.RESOLVED),
            "pending": sum(1 for item in complaints if item.status == Complaint.Status.PENDING),
            "rejected": sum(1 for item in complaints if item.status == Complaint.Status.REJECTED),
        },
        "complaints": [serialize_complaint(item) for item in complaints],
        "categories": {
            "labels": list(category_totals.keys()) or ["No complaints"],
            "values": list(category_totals.values()) or [0],
        },
    }


def get_owned_property(request, property_id):
    return get_object_or_404(Property, id=property_id, landlord=request.user)


def get_owned_complaint(request, complaint_id):
    return get_object_or_404(
        Complaint.objects.select_related("tenant", "tenant__property", "tenant__property_unit"),
        id=complaint_id,
        tenant__landlord=request.user,
    )


def get_owned_extension_request(request, extension_request_id):
    return get_object_or_404(
        LeaseExtensionRequest.objects.select_related("tenant", "tenant__property"),
        id=extension_request_id,
        tenant__landlord=request.user,
    )


def get_owned_bill(request, bill_id):
    return get_object_or_404(
        Bill.objects.select_related("tenant", "property"),
        id=bill_id,
        landlord=request.user,
    )


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
    for tenant in user_tenant_queryset:
        ensure_tenant_system_notifications(tenant)
    if page == "tenants":
        user_tenants = user_tenant_queryset
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "tenants_payload": [serialize_tenant(item) for item in user_tenants],
            "tenant_dashboard_data": build_tenant_dashboard_data(user_tenants),
            "extension_requests": [
                serialize_extension_request(item)
                for item in LeaseExtensionRequest.objects.filter(
                    tenant__landlord=request.user
                ).select_related("tenant", "tenant__property")
            ],
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
    if page == "analytics":
        user_tenants = list(user_tenant_queryset)
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "analytics_dashboard_data": build_landlord_analytics_data(request.user, user_properties, user_tenants),
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
    if page == "overview":
        user_tenants = list(user_tenant_queryset)
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "overview_dashboard_data": build_landlord_overview_data(request.user, user_properties, user_tenants),
        }
        return render(request, LANDLORD_TEMPLATES[page], context)
    if page == "notifications":
        context = {
            "page_key": page,
            "page_title": LANDLORD_PAGES[page],
            "notifications_dashboard_data": build_landlord_notifications_page_data(request.user),
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
def landlord_settings(request):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can access this workspace.")

    settings_obj = get_or_create_landlord_settings(request.user)
    action = request.POST.get("form_action")
    if request.method == "POST" and not action:
        action = "profile"

    profile_form = LandlordSettingsProfileForm(
        request.POST if action == "profile" else None,
        instance=settings_obj,
    )
    automation_form = LandlordSettingsAutomationForm(
        request.POST if action == "automation" else None,
        instance=settings_obj,
    )

    if request.method == "POST":
        if action == "profile" and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Landlord profile settings were updated.")
            return redirect("landlord-settings")
        if action == "automation" and automation_form.is_valid():
            automation_form.save()
            messages.success(request, "Automation and reminder settings were updated.")
            return redirect("landlord-settings")

    context = {
        "page_key": "settings",
        "page_title": LANDLORD_PAGES["settings"],
        "profile_form": profile_form,
        "automation_form": automation_form,
        "landlord_settings_data": build_landlord_settings_dashboard_data(request.user, settings_obj),
    }
    return render(request, LANDLORD_TEMPLATES["settings"], context)


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
    ensure_tenant_system_notifications(tenant)
    if page == "notifications":
        context = {
            "page_key": page,
            "page_title": TENANT_PAGES[page],
            "tenant": tenant,
            "tenant_workspace": build_tenant_workspace_data(tenant),
            "tenant_notifications_data": build_tenant_notifications_page_data(tenant),
        }
        return render(request, TENANT_TEMPLATES[page], context)
    context = {
        "page_key": page,
        "page_title": TENANT_PAGES[page],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "tenant_receipts_data": build_tenant_receipts_data(tenant),
        "tenant_notifications": build_tenant_notifications(tenant),
        "tenant_analytics": build_tenant_analytics_data(tenant),
        "rent_due_notice": get_rent_due_notice(tenant),
        "next_rent_due_date": get_next_rent_due_date(tenant),
    }
    return render(request, TENANT_TEMPLATES[page], context)


@login_required
def tenant_profile(request):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")

    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    process_due_rent_bills([tenant])
    tenant.refresh_from_db()

    profile_form = TenantProfileForm(request.POST or None, instance=tenant)
    if request.method == "POST" and profile_form.is_valid():
        tenant = profile_form.save()
        if tenant.user:
            tenant.user.full_name = tenant.full_name
            tenant.user.save(update_fields=["full_name"])
        messages.success(request, "Your tenant profile was updated successfully.")
        return redirect("tenant-profile")

    context = {
        "page_key": "profile",
        "page_title": TENANT_PAGES["profile"],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "tenant_receipts_data": build_tenant_receipts_data(tenant),
        "tenant_notifications": build_tenant_notifications(tenant),
        "tenant_analytics": build_tenant_analytics_data(tenant),
        "profile_form": profile_form,
    }
    return render(request, TENANT_TEMPLATES["profile"], context)


@login_required
def tenant_settings(request):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")

    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    process_due_rent_bills([tenant])
    tenant.refresh_from_db()
    ensure_tenant_system_notifications(tenant)
    action = request.POST.get("form_action")
    if request.method == "POST" and not action:
        action = "password" if "old_password" in request.POST else "autopay"
    password_form = TenantPasswordChangeForm(
        user=request.user,
        data=request.POST if action == "password" else None,
    )
    autopay_form = TenantAutopayForm(
        request.POST if action == "autopay" else None,
        instance=tenant,
    )

    if request.method == "POST":
        if action == "password" and password_form.is_valid():
            user = password_form.save()
            if user.password_change_required:
                user.password_change_required = False
                user.save(update_fields=["password_change_required"])
            Notification.objects.filter(
                recipient=user,
                dedupe_key=f"tenant-password-change-{tenant.id}",
            ).update(is_read=True, read_at=timezone.now())
            create_notification(
                user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Password updated",
                message="Your tenant account password was updated successfully.",
                category=Notification.Category.ACCOUNT,
                priority=Notification.Priority.LOW,
                link_url=reverse("tenant-settings"),
            )
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was updated successfully.")
            return redirect("tenant-settings")
        if action == "autopay" and autopay_form.is_valid():
            tenant = autopay_form.save()
            if tenant.autopay_enabled:
                create_notification(
                    tenant.user,
                    tenant=tenant,
                    property_obj=tenant.property,
                    title="Autopay enabled",
                    message="Rent autopay is now enabled and future rent bills can be collected automatically in test mode.",
                    category=Notification.Category.PAYMENTS,
                    priority=Notification.Priority.LOW,
                    link_url=reverse("tenant-settings"),
                )
                processed = process_rent_autopay(tenant)
                if processed:
                    messages.success(
                        request,
                        f"Autopay was enabled and {processed} rent bill(s) were paid automatically in test mode.",
                    )
                else:
                    messages.success(
                        request,
                        "Autopay was enabled. Future rent bills will be paid automatically in test mode.",
                    )
            else:
                create_notification(
                    tenant.user,
                    tenant=tenant,
                    property_obj=tenant.property,
                    title="Autopay disabled",
                    message="Future rent bills will stay manual until you enable autopay again.",
                    category=Notification.Category.PAYMENTS,
                    priority=Notification.Priority.LOW,
                    link_url=reverse("tenant-settings"),
                )
                messages.success(request, "Autopay was disabled for future rent bills.")
            return redirect("tenant-settings")

    context = {
        "page_key": "settings",
        "page_title": TENANT_PAGES["settings"],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "password_form": password_form,
        "autopay_form": autopay_form,
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
    ensure_tenant_system_notifications(tenant)

    action = request.POST.get("form_action")
    if request.method == "POST" and not action:
        action = "extension" if "requested_end_date" in request.POST else "payment"
    lease_extension_form = LeaseExtensionRequestForm(
        request.POST if action == "extension" else None
    )
    payment_form = TenantPaymentForm(
        request.POST if action == "payment" else None,
        tenant=tenant,
    )

    if request.method == "POST":
        if action == "extension" and lease_extension_form.is_valid():
            extension = lease_extension_form.save(commit=False)
            extension.tenant = tenant
            extension.save()
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Lease extension submitted",
                message=f"Your request to extend the lease to {extension.requested_end_date.strftime('%b %d, %Y')} was submitted.",
                category=Notification.Category.LEASE,
                priority=Notification.Priority.MEDIUM,
                link_url=reverse("tenant-receipts"),
            )
            create_notification(
                tenant.landlord,
                tenant=tenant,
                property_obj=tenant.property,
                title="Lease extension request submitted",
                message=f"{tenant.full_name} requested a lease extension to {extension.requested_end_date.strftime('%b %d, %Y')}.",
                category=Notification.Category.LEASE,
                priority=Notification.Priority.HIGH,
                link_url=reverse("landlord-extension-request-detail", args=[extension.id]),
            )
            messages.success(request, "Your lease extension request was submitted.")
            return redirect("tenant-receipts")
        if action == "payment" and payment_form.is_valid():
            selected_bills = payment_form.cleaned_data.get("selected_bills", [])
            payment = Payment(
                landlord=tenant.landlord,
                property=tenant.property,
                tenant=tenant,
                bill=selected_bills[0] if len(selected_bills) == 1 else None,
                selected_bill_ids=",".join(str(item.id) for item in selected_bills),
                scope=payment_form.cleaned_data["payment_target"],
                method=payment_form.cleaned_data["method"],
                amount=payment_form.cleaned_data["calculated_amount"],
                rent_periods=payment_form.cleaned_data.get("rent_periods") or 0,
                paid_on=timezone.localdate(),
            )
            if payment.method == Payment.Method.CASH:
                payment.status = Payment.Status.PENDING
                payment.notes = "Submitted by tenant as a cash payment. Awaiting landlord approval."
                payment.save()
                create_notification(
                    tenant.user,
                    tenant=tenant,
                    property_obj=tenant.property,
                    title="Cash payment submitted",
                    message=f"Your cash payment of KSh {payment.amount} is pending landlord approval.",
                    category=Notification.Category.PAYMENTS,
                    priority=Notification.Priority.MEDIUM,
                    link_url=reverse("tenant-payment-detail", args=[payment.id]) if tenant.user else "",
                )
                create_notification(
                    tenant.landlord,
                    tenant=tenant,
                    property_obj=tenant.property,
                    title="Cash payment awaiting approval",
                    message=f"{tenant.full_name} submitted a cash payment of KSh {payment.amount}.",
                    category=Notification.Category.PAYMENTS,
                    priority=Notification.Priority.HIGH,
                    link_url=reverse("landlord-payment-detail", args=[payment.id]),
                )
                success_message = "Your cash payment was submitted and is now waiting for landlord approval."
            elif payment.method == Payment.Method.MPESA:
                payment.status = Payment.Status.CONFIRMED
                payment.notes = "M-Pesa prompt simulated and confirmed automatically in test mode."
                payment.save()
                success_message = "Check your phone for the M-Pesa prompt. SmartRent has confirmed the payment automatically in test mode."
            else:
                payment.status = Payment.Status.CONFIRMED
                payment.notes = "Card payment confirmed automatically in test mode using the saved bank or card details."
                payment.save()
                success_message = "Your card payment was confirmed in test mode using the saved bank or card details."
            if payment.status == Payment.Status.CONFIRMED:
                finalize_payment(payment)
            messages.success(request, success_message)
            return redirect("tenant-receipts")

    context = {
        "page_key": "receipts",
        "page_title": TENANT_PAGES["receipts"],
        "tenant": tenant,
        "tenant_workspace": build_tenant_workspace_data(tenant),
        "tenant_receipts_data": build_tenant_receipts_data(tenant),
        "tenant_notifications": build_tenant_notifications(tenant),
        "tenant_analytics": build_tenant_analytics_data(tenant),
        "lease_extension_form": lease_extension_form,
        "lease_extension_requests": tenant.lease_extension_requests.all(),
        "tenant_payment_form": payment_form,
        "max_rent_periods": payment_form.get_max_rent_periods(),
        "open_bill_choices": [
            {
                "id": item.id,
                "title": item.title,
                "category": item.category,
                "amount": float(item.remaining_amount),
                "dueDate": item.due_date.strftime("%b %d, %Y"),
            }
            for item in tenant.bills.exclude(status=Bill.Status.PAID).order_by("due_date", "created_at")
        ],
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
            "payment_allocations": payment.allocations.select_related("bill").all(),
        },
    )


@login_required
def landlord_bill_detail(request, bill_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can access this workspace.")
    bill = get_owned_bill(request, bill_id)
    return render(
        request,
        "landlord/bills/bill_detail.html",
        {
            "page_key": "bills",
            "page_title": "Bill Detail",
            "bill": bill,
            "bill_detail_data": build_landlord_bill_detail_data(bill),
        },
    )


@login_required
def landlord_extension_request_detail(request, extension_request_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can access this workspace.")
    extension_request = get_owned_extension_request(request, extension_request_id)
    form = LeaseExtensionDecisionForm(request.POST or None, instance=extension_request)

    if request.method == "POST" and form.is_valid():
        extension_request = form.save(commit=False)
        extension_request.reviewed_at = timezone.now()
        extension_request.save(update_fields=["status", "landlord_notes", "reviewed_at"])
        tenant = extension_request.tenant
        if extension_request.status == LeaseExtensionRequest.Status.APPROVED:
            tenant.lease_end = extension_request.requested_end_date
            if tenant.status == Tenant.Status.RENEWING_SOON:
                tenant.status = Tenant.Status.GOOD_STANDING
            tenant.save(update_fields=["lease_end", "status"])
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Lease extension approved",
                message=f"Your lease extension to {extension_request.requested_end_date.strftime('%b %d, %Y')} was approved.",
                category=Notification.Category.LEASE,
                priority=Notification.Priority.MEDIUM,
                link_url=reverse("tenant-receipts") if tenant.user else "",
            )
            messages.success(request, f"Lease extension for {tenant.full_name} was approved.")
        elif extension_request.status == LeaseExtensionRequest.Status.DECLINED:
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Lease extension declined",
                message=f"Your lease extension request was declined. {extension_request.landlord_notes}".strip(),
                category=Notification.Category.LEASE,
                priority=Notification.Priority.HIGH,
                link_url=reverse("tenant-receipts") if tenant.user else "",
            )
            messages.success(request, f"Lease extension for {tenant.full_name} was declined.")
        else:
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Lease extension under review",
                message="Your landlord updated the lease extension request and it is still under review.",
                category=Notification.Category.LEASE,
                priority=Notification.Priority.MEDIUM,
                link_url=reverse("tenant-receipts") if tenant.user else "",
            )
            messages.success(request, f"Lease extension for {tenant.full_name} was updated.")
        return redirect("landlord-extension-request-detail", extension_request_id=extension_request.id)

    return render(
        request,
        "landlord/tenants/extension_request_detail.html",
        {
            "page_key": "tenants",
            "page_title": "Lease Extension Request",
            "extension_request": extension_request,
            "form": form,
        },
    )


@login_required
def complaint_detail(request, complaint_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can access this workspace.")

    complaint = get_owned_complaint(request, complaint_id)
    action = request.POST.get("form_action")
    if request.method == "POST" and not action:
        action = "status" if "status" in request.POST else "expense"
    status_form = ComplaintStatusForm(
        request.POST if action == "status" else None,
        instance=complaint,
    )
    expense_form = MaintenanceExpenseForm(
        request.POST if action == "expense" else None,
    )

    if request.method == "POST":
        if action == "status" and status_form.is_valid():
            complaint = status_form.save()
            create_notification(
                complaint.tenant.user,
                tenant=complaint.tenant,
                property_obj=complaint.tenant.property,
                title="Complaint status updated",
                message=f"'{complaint.title}' is now marked as {complaint.status}. {complaint.landlord_notes}".strip(),
                category=Notification.Category.MAINTENANCE,
                priority=Notification.Priority.MEDIUM if complaint.status != Complaint.Status.REJECTED else Notification.Priority.HIGH,
                link_url=reverse("tenant-complaint-detail", args=[complaint.id]) if complaint.tenant.user else "",
            )
            messages.success(request, f"Complaint status for {complaint.tenant.full_name} was updated.")
            return redirect("landlord-complaint-detail", complaint_id=complaint.id)
        if action == "expense" and expense_form.is_valid():
            expense = expense_form.save(commit=False)
            expense.complaint = complaint
            expense.landlord = request.user
            expense.save()
            if expense.cost_bearer == MaintenanceExpense.CostBearer.TENANT:
                bill = Bill.objects.create(
                    landlord=request.user,
                    property=complaint.tenant.property,
                    tenant=complaint.tenant,
                    title=f"Maintenance expense: {expense.title}",
                    category=Bill.Category.REPAIRS,
                    amount=expense.amount,
                    remaining_amount=expense.amount,
                    due_date=timezone.localdate(),
                    status=Bill.Status.UNPAID,
                    notes=f"Linked to complaint: {complaint.title}",
                )
                apply_credit_to_bill(bill)
                expense.bill = bill
                expense.save(update_fields=["bill"])
                create_notification(
                    complaint.tenant.user,
                    tenant=complaint.tenant,
                    property_obj=complaint.tenant.property,
                    title="Repair bill added",
                    message=f"A repair bill of KSh {bill.amount} was added for '{complaint.title}'.",
                    category=Notification.Category.PAYMENTS,
                    priority=Notification.Priority.HIGH,
                    link_url=reverse("tenant-bill-detail", args=[bill.id]) if complaint.tenant.user else "",
                )
                messages.success(
                    request,
                    "Expense saved and a tenant repair bill was created because the tenant is responsible for this cost.",
                )
            else:
                messages.success(request, "Expense saved to the internal maintenance record.")
            return redirect("landlord-complaint-detail", complaint_id=complaint.id)

    return render(
        request,
        "landlord/maintenance/complaint_detail.html",
        {
            "page_key": "maintenance",
            "page_title": "Complaint Detail",
            "complaint": complaint,
            "status_form": status_form,
            "expense_form": expense_form,
            "expense_records": complaint.expenses.select_related("bill").all(),
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
    ensure_tenant_system_notifications(tenant)

    form = ComplaintForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        complaint = form.save(commit=False)
        complaint.tenant = tenant
        complaint.save()
        create_notification(
            tenant.user,
            tenant=tenant,
            property_obj=tenant.property,
            title="Complaint logged",
            message=f"Your complaint '{complaint.title}' was submitted and is currently pending review.",
            category=Notification.Category.MAINTENANCE,
            priority=Notification.Priority.MEDIUM,
            link_url=reverse("tenant-complaint-detail", args=[complaint.id]) if tenant.user else "",
        )
        create_notification(
            tenant.landlord,
            tenant=tenant,
            property_obj=tenant.property,
            title="New complaint submitted",
            message=f"{tenant.full_name} logged a new complaint: {complaint.title}.",
            category=Notification.Category.MAINTENANCE,
            priority=Notification.Priority.HIGH,
            link_url=reverse("landlord-complaint-detail", args=[complaint.id]),
        )
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
        "complaints_payload": build_tenant_complaints_payload(tenant),
    }
    return render(request, TENANT_TEMPLATES["complaints"], context)


@login_required
def tenant_complaint_detail(request, complaint_id):
    if request.user.role != User.Role.TENANT:
        return HttpResponseForbidden("Only tenant accounts can access this workspace.")
    tenant = get_tenant_profile(request)
    if tenant is None:
        return HttpResponseForbidden("This tenant account is not linked to a tenant profile yet.")
    complaint = get_object_or_404(
        Complaint.objects.select_related("tenant", "tenant__property"),
        id=complaint_id,
        tenant=tenant,
    )
    linked_bills = Bill.objects.filter(
        maintenance_expense__complaint=complaint,
        tenant=tenant,
    ).order_by("-created_at")
    return render(
        request,
        "tenant/complaints/detail.html",
        {
            "page_key": "complaints",
            "page_title": "Complaint Detail",
            "tenant": tenant,
            "tenant_workspace": build_tenant_workspace_data(tenant),
            "complaint": complaint,
            "linked_bills": linked_bills,
        },
    )


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
        payment.scope = Payment.Scope.ALL
        payment.status = Payment.Status.CONFIRMED
        payment.save()
        finalize_payment(payment)
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
@require_POST
def approve_payment(request, payment_id):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can approve payments.")

    payment = get_object_or_404(
        Payment.objects.select_related("tenant", "property", "bill"),
        id=payment_id,
        landlord=request.user,
    )
    if payment.status != Payment.Status.PENDING:
        messages.info(request, "That payment has already been processed.")
        return redirect("landlord-payments")

    payment.status = Payment.Status.CONFIRMED
    payment.notes = f"{payment.notes} Approved by landlord.".strip()
    payment.save(update_fields=["status", "notes"])
    finalize_payment(payment)
    messages.success(request, f"Payment for {payment.tenant.full_name} was approved.")
    return redirect("landlord-payments")


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
                create_notification(
                    bill.tenant.user,
                    tenant=bill.tenant,
                    property_obj=bill.property,
                    title="New bill added",
                    message=f"{bill.title} for KSh {bill.amount} was added to your account.",
                    category=Notification.Category.PAYMENTS,
                    priority=Notification.Priority.HIGH,
                    link_url=reverse("tenant-bill-detail", args=[bill.id]) if bill.tenant.user else "",
                )
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
@require_POST
def mark_notification_read_view(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )
    mark_notification_read(notification)
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(get_dashboard_redirect_name(request.user))


@login_required
@require_POST
def mark_all_notifications_read_view(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(get_dashboard_redirect_name(request.user))


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
            create_notification(
                tenant.user,
                tenant=tenant,
                property_obj=tenant.property,
                title="Your tenant account is ready",
                message=f"You can now sign in with {tenant.email}. Please change the default password from Settings after login.",
                category=Notification.Category.ACCOUNT,
                priority=Notification.Priority.HIGH,
                link_url=reverse("tenant-settings") if tenant.user else "",
            )
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
