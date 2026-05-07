from datetime import timedelta
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.forms import formset_factory
from django.utils import timezone

from .models import Bill, Complaint, LandlordSettings, LeaseExtensionRequest, MaintenanceExpense, Payment, Property, PropertyUnit, Tenant


class LandlordLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "landlord.demo@smartrent.local",
                "autocomplete": "email",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        )
    )


class LandlordSettingsProfileForm(forms.ModelForm):
    class Meta:
        model = LandlordSettings
        fields = ["business_name", "support_email", "support_phone"]
        widgets = {
            "business_name": forms.TextInput(attrs={"placeholder": "SmartRent Management"}),
            "support_email": forms.EmailInput(attrs={"placeholder": "support@smartrent.local"}),
            "support_phone": forms.TextInput(attrs={"placeholder": "+254 700 123 456"}),
        }


class LandlordSettingsAutomationForm(forms.ModelForm):
    class Meta:
        model = LandlordSettings
        fields = [
            "owner_digest_enabled",
            "weekly_report_enabled",
            "maintenance_escalation_enabled",
            "autopay_nudges_enabled",
            "rent_reminder_days",
            "overdue_follow_up_days",
            "maintenance_escalation_hours",
        ]
        widgets = {
            "owner_digest_enabled": forms.CheckboxInput(attrs={"class": "toggle-checkbox"}),
            "weekly_report_enabled": forms.CheckboxInput(attrs={"class": "toggle-checkbox"}),
            "maintenance_escalation_enabled": forms.CheckboxInput(attrs={"class": "toggle-checkbox"}),
            "autopay_nudges_enabled": forms.CheckboxInput(attrs={"class": "toggle-checkbox"}),
            "rent_reminder_days": forms.NumberInput(attrs={"min": 1, "max": 30}),
            "overdue_follow_up_days": forms.NumberInput(attrs={"min": 1, "max": 30}),
            "maintenance_escalation_hours": forms.NumberInput(attrs={"min": 1, "max": 168}),
        }


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ["name", "location", "status", "trend"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Riverpoint Residences"}),
            "location": forms.TextInput(attrs={"placeholder": "Westlands, Nairobi"}),
            "status": forms.Select(),
            "trend": forms.NumberInput(attrs={"step": "0.1", "placeholder": "4.8"}),
        }


class PropertyUnitTypeForm(forms.Form):
    unit_type = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "2 Bedroom"}),
    )
    unit_count = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"min": 1, "placeholder": "12"}),
    )
    renting_price = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "45000"}),
    )
    buying_price = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "9500000"}),
    )


BaseUnitTypeFormSet = formset_factory(
    PropertyUnitTypeForm,
    extra=1,
    can_delete=True,
)


class UnitTypeFormSet(BaseUnitTypeFormSet):
    def clean(self):
        super().clean()
        active_forms = 0

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            if any(
                form.cleaned_data.get(field)
                for field in ("unit_type", "unit_count", "renting_price", "buying_price")
            ):
                active_forms += 1

        if active_forms == 0:
            raise forms.ValidationError("Add at least one unit type for this property.")


class TenantForm(forms.ModelForm):
    unit_type = forms.ChoiceField(
        choices=(),
        required=True,
        widget=forms.Select(),
    )
    property_unit = forms.ModelChoiceField(
        queryset=PropertyUnit.objects.none(),
        required=True,
        empty_label="Select available house",
        widget=forms.Select(),
    )

    class Meta:
        model = Tenant
        fields = [
            "property",
            "full_name",
            "email",
            "phone",
            "id_number",
            "lease_start",
            "lease_end",
            "lease_type",
            "security_deposit",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "occupation",
            "status",
            "risk_level",
            "notes",
        ]
        widgets = {
            "property": forms.Select(attrs={"placeholder": "Select property"}),
            "unit_type": forms.Select(),
            "property_unit": forms.Select(),
            "full_name": forms.TextInput(attrs={"placeholder": "Brian Mwangi"}),
            "email": forms.EmailInput(attrs={"placeholder": "brian.mwangi@example.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "+254 700 123 456"}),
            "id_number": forms.TextInput(attrs={"placeholder": "National ID or Passport number"}),
            "lease_start": forms.DateInput(attrs={"type": "date"}),
            "lease_end": forms.DateInput(attrs={"type": "date"}),
            "lease_type": forms.Select(),
            "security_deposit": forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "90000"}),
            "emergency_contact_name": forms.TextInput(attrs={"placeholder": "Jane Mwangi"}),
            "emergency_contact_phone": forms.TextInput(attrs={"placeholder": "+254 711 234 567"}),
            "emergency_contact_relationship": forms.TextInput(attrs={"placeholder": "Spouse, Parent, Sibling..."}),
            "occupation": forms.TextInput(attrs={"placeholder": "Software Engineer"}),
            "status": forms.Select(),
            "risk_level": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Additional notes about this tenant..."}),
        }

    def __init__(self, *args, landlord=None, **kwargs):
        super().__init__(*args, **kwargs)
        property_queryset = Property.objects.filter(landlord=landlord) if landlord else Property.objects.none()
        self.fields["property"].queryset = property_queryset

        selected_property_id = (
            self.data.get("property")
            or self.initial.get("property")
            or getattr(self.instance, "property_id", None)
        )
        selected_unit_type = (
            self.data.get("unit_type")
            or self.initial.get("unit_type")
            or getattr(getattr(self.instance, "property_unit", None), "unit_type", None)
        )
        if hasattr(selected_unit_type, "unit_type"):
            selected_unit_type = selected_unit_type.unit_type

        unit_queryset = PropertyUnit.objects.filter(
            property__landlord=landlord,
        ).filter(Q(is_occupied=False) | Q(id=getattr(self.instance, "property_unit_id", None)))

        if selected_property_id:
            unit_queryset = unit_queryset.filter(property_id=selected_property_id)

        unit_type_values = [
            value
            for value in unit_queryset.order_by("unit_type__unit_type")
            .values_list("unit_type__unit_type", flat=True)
            .distinct()
            if value
        ]
        self.fields["unit_type"].choices = [("", "Select unit type")] + [
            (value, value) for value in unit_type_values
        ]

        if selected_unit_type:
            unit_queryset = unit_queryset.filter(unit_type__unit_type=selected_unit_type)

        self.fields["property_unit"].queryset = unit_queryset.select_related("property", "unit_type").order_by("id")

    def clean(self):
        cleaned_data = super().clean()
        property_obj = cleaned_data.get("property")
        property_unit = cleaned_data.get("property_unit")
        unit_type = cleaned_data.get("unit_type")
        lease_type = cleaned_data.get("lease_type")
        lease_end = cleaned_data.get("lease_end")

        if property_unit and property_obj and property_unit.property_id != property_obj.id:
            self.add_error("property_unit", "Select a house that belongs to the chosen property.")

        if property_unit and unit_type:
            actual_unit_type = property_unit.unit_type.unit_type if property_unit.unit_type else ""
            if actual_unit_type != unit_type:
                self.add_error("property_unit", "Select a house that matches the chosen unit type.")

        if property_unit and property_unit.is_occupied and property_unit.pk != getattr(self.instance, "property_unit_id", None):
            self.add_error("property_unit", "That house is no longer available. Please select another one.")

        if lease_type == Tenant.LeaseType.RENT and not lease_end:
            self.add_error("lease_end", "Lease end date is required for rental tenants.")

        cleaned_data["unit_number"] = property_unit.unit_number if property_unit else ""
        return cleaned_data

    def save(self, commit=True):
        tenant = super().save(commit=False)
        property_unit = self.cleaned_data.get("property_unit")
        if property_unit:
            tenant.property_unit = property_unit
            tenant.unit_number = property_unit.unit_number
            tenant.property = property_unit.property
            if tenant.lease_type == Tenant.LeaseType.RENT:
                tenant.monthly_rent = property_unit.unit_type.renting_price if property_unit.unit_type else None
                tenant.purchase_price = None
            else:
                tenant.monthly_rent = None
                tenant.purchase_price = property_unit.unit_type.buying_price if property_unit.unit_type else None
                tenant.lease_end = None
        if commit:
            tenant.save()
        return tenant


class TenantPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Current password",
            }
        )
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "New password",
            }
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Confirm new password",
            }
        )
    )


class TenantAutopayForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            "autopay_enabled",
            "autopay_bank_name",
            "autopay_account_holder",
            "autopay_account_number",
            "autopay_card_number",
            "autopay_card_expiry",
        ]
        widgets = {
            "autopay_enabled": forms.CheckboxInput(attrs={"class": "toggle-checkbox"}),
            "autopay_bank_name": forms.TextInput(attrs={"placeholder": "Equity Bank or Co-operative Bank"}),
            "autopay_account_holder": forms.TextInput(attrs={"placeholder": "Card or account holder name"}),
            "autopay_account_number": forms.TextInput(attrs={"placeholder": "Account number or wallet reference"}),
            "autopay_card_number": forms.TextInput(attrs={"placeholder": "4111 1111 1111 1111"}),
            "autopay_card_expiry": forms.TextInput(attrs={"placeholder": "08/29"}),
        }


class TenantProfileForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            "full_name",
            "phone",
            "id_number",
            "occupation",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Your full name"}),
            "phone": forms.TextInput(attrs={"placeholder": "+254 700 123 456"}),
            "id_number": forms.TextInput(attrs={"placeholder": "National ID or Passport number"}),
            "occupation": forms.TextInput(attrs={"placeholder": "Occupation"}),
            "emergency_contact_name": forms.TextInput(attrs={"placeholder": "Emergency contact name"}),
            "emergency_contact_phone": forms.TextInput(attrs={"placeholder": "+254 711 234 567"}),
            "emergency_contact_relationship": forms.TextInput(attrs={"placeholder": "Parent, sibling, spouse..."}),
        }


class LeaseExtensionRequestForm(forms.ModelForm):
    class Meta:
        model = LeaseExtensionRequest
        fields = ["requested_end_date", "reason"]
        widgets = {
            "requested_end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Explain why you are requesting a lease extension."}),
        }


class LeaseExtensionDecisionForm(forms.ModelForm):
    class Meta:
        model = LeaseExtensionRequest
        fields = ["status", "landlord_notes"]
        widgets = {
            "status": forms.Select(),
            "landlord_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Explain the decision or the next step for the tenant.",
                }
            ),
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["title", "category", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Broken bedroom window"}),
            "category": forms.Select(),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the issue, when it started, and how urgent it feels."}),
        }


class ComplaintStatusForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["status", "landlord_notes"]
        widgets = {
            "status": forms.Select(),
            "landlord_notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share resolution notes, next steps, or the reason for rejection.",
                }
            ),
        }


class MaintenanceExpenseForm(forms.ModelForm):
    class Meta:
        model = MaintenanceExpense
        fields = ["title", "amount", "cost_bearer", "notes"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Window replacement parts"}),
            "amount": forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "6500"}),
            "cost_bearer": forms.Select(),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional note about why this cost belongs to the tenant, management, or landlord.",
                }
            ),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["tenant", "property", "method", "amount", "paid_on", "notes"]
        widgets = {
            "tenant": forms.Select(),
            "property": forms.Select(),
            "method": forms.Select(),
            "amount": forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "35000"}),
            "paid_on": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Reference number or extra payment notes"}),
        }

    def __init__(self, *args, landlord=None, **kwargs):
        super().__init__(*args, **kwargs)
        if landlord:
            properties = Property.objects.filter(landlord=landlord)
            tenants = Tenant.objects.filter(landlord=landlord).select_related("property")
            self.fields["property"].queryset = properties
            self.fields["tenant"].queryset = tenants
        self.fields["method"].choices = [
            (Payment.Method.MPESA, Payment.Method.MPESA),
            (Payment.Method.CARD, Payment.Method.CARD),
            (Payment.Method.CASH, Payment.Method.CASH),
        ]


class TenantPaymentForm(forms.Form):
    payment_target = forms.ChoiceField(
        choices=[
            (Payment.Scope.BILL, "Specific bill"),
            (Payment.Scope.RENT, "Rent"),
            (Payment.Scope.ALL, "All open bills"),
        ],
        widget=forms.Select(),
    )
    bill = forms.ModelChoiceField(
        queryset=Bill.objects.none(),
        required=False,
        empty_label="Select a bill",
        widget=forms.Select(),
    )
    selected_bill_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    rent_periods = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={"min": 1, "placeholder": "1"}),
    )
    method = forms.ChoiceField(
        choices=[
            (Payment.Method.MPESA, "M-Pesa"),
            (Payment.Method.CARD, "Card"),
            (Payment.Method.CASH, "Cash"),
        ],
        widget=forms.Select(),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        if tenant:
            self.fields["bill"].queryset = tenant.bills.exclude(status=Bill.Status.PAID).order_by("due_date", "created_at")
            self.fields["method"].initial = Payment.Method.MPESA

    def clean(self):
        cleaned_data = super().clean()
        tenant = self.tenant
        if tenant is None:
            raise forms.ValidationError("Tenant account is required to submit a payment.")

        target = cleaned_data.get("payment_target")
        bill = cleaned_data.get("bill")
        selected_bill_ids = cleaned_data.get("selected_bill_ids") or ""
        rent_periods = cleaned_data.get("rent_periods") or 0
        method = cleaned_data.get("method")
        selected_bills = self.get_selected_bills(selected_bill_ids)
        if target == Payment.Scope.BILL and bill and not selected_bills:
            selected_bills = [bill]

        if target == Payment.Scope.BILL and not selected_bills:
            self.add_error("bill", "Add at least one bill to the payment list.")

        if bill and bill.tenant_id != tenant.id:
            self.add_error("bill", "That bill does not belong to your account.")

        if target == Payment.Scope.RENT:
            if tenant.lease_type != Tenant.LeaseType.RENT or not tenant.monthly_rent:
                self.add_error("payment_target", "Only rental tenants can pay rent from this form.")
            if rent_periods < 1:
                self.add_error("rent_periods", "Choose how many rent periods you want to pay.")
            max_periods = self.get_max_rent_periods()
            if max_periods < 1:
                self.add_error("payment_target", "There are no remaining rent periods available before your lease end date.")
            elif rent_periods > max_periods:
                self.add_error("rent_periods", f"You can only pay up to {max_periods} rent period(s) before the lease end date.")

        if method == Payment.Method.CARD and not self.has_saved_card_details():
            self.add_error("method", "Set up your bank or card details in Settings before paying by card.")

        cleaned_data["selected_bills"] = selected_bills
        cleaned_data["calculated_amount"] = self.calculate_amount(cleaned_data)
        if cleaned_data["calculated_amount"] <= Decimal("0"):
            self.add_error("payment_target", "There is nothing payable for the option you selected right now.")
        return cleaned_data

    def get_selected_bills(self, selected_bill_ids):
        if not selected_bill_ids or self.tenant is None:
            return []
        valid_ids = []
        for raw_id in selected_bill_ids.split(","):
            raw_id = raw_id.strip()
            if raw_id.isdigit():
                valid_ids.append(int(raw_id))
        if not valid_ids:
            return []
        bills = list(
            Bill.objects.filter(
                tenant=self.tenant,
                id__in=valid_ids,
            ).exclude(status=Bill.Status.PAID).order_by("due_date", "created_at")
        )
        return bills

    def has_saved_card_details(self):
        tenant = self.tenant
        if tenant is None:
            return False
        return bool(
            tenant.autopay_account_holder
            and (
                (tenant.autopay_card_number and tenant.autopay_card_expiry)
                or tenant.autopay_account_number
            )
        )

    def get_next_due_date(self):
        tenant = self.tenant
        if tenant is None or tenant.lease_type != Tenant.LeaseType.RENT or not tenant.monthly_rent:
            return None
        anchor = tenant.last_rent_charge_at
        if anchor is None:
            return tenant.lease_start + timedelta(days=30)
        return timezone.localtime(anchor).date() + timedelta(days=30)

    def get_max_rent_periods(self):
        tenant = self.tenant
        if tenant is None or tenant.lease_type != Tenant.LeaseType.RENT or not tenant.lease_end:
            return 0
        next_due = self.get_next_due_date()
        if not next_due or next_due > tenant.lease_end:
            return 0
        periods = 0
        current_due = next_due
        while current_due <= tenant.lease_end:
            periods += 1
            current_due += timedelta(days=30)
        return periods

    def calculate_amount(self, cleaned_data):
        tenant = self.tenant
        if tenant is None:
            return 0
        target = cleaned_data.get("payment_target")
        bill = cleaned_data.get("bill")
        rent_periods = cleaned_data.get("rent_periods") or 0

        if target == Payment.Scope.BILL:
            return sum((item.remaining_amount for item in cleaned_data.get("selected_bills", [])), start=Decimal("0"))
        if target == Payment.Scope.RENT and tenant.monthly_rent:
            return tenant.monthly_rent * rent_periods
        if target == Payment.Scope.ALL:
            return sum(
                (item.remaining_amount for item in tenant.bills.exclude(status=Bill.Status.PAID)),
                start=Decimal("0"),
            )
        return 0


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ["property", "tenant", "title", "category", "amount", "due_date", "status", "notes"]
        widgets = {
            "property": forms.Select(),
            "tenant": forms.Select(),
            "title": forms.TextInput(attrs={"placeholder": "April service charge"}),
            "category": forms.Select(),
            "amount": forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "6500"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "status": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Any extra billing notes"}),
        }

    def __init__(self, *args, landlord=None, **kwargs):
        super().__init__(*args, **kwargs)
        if landlord:
            properties = Property.objects.filter(landlord=landlord)
            tenants = Tenant.objects.filter(landlord=landlord).select_related("property")
            self.fields["property"].queryset = properties
            self.fields["tenant"].queryset = tenants
            self.fields["tenant"].required = False
        self.fields["category"].choices = [
            choice for choice in self.fields["category"].choices
            if choice[0] != Bill.Category.RENT
        ]
