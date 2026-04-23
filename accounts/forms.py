from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.forms import formset_factory

from .models import Bill, Complaint, LeaseExtensionRequest, Payment, Property, PropertyUnit, Tenant


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
            "autopay_enabled",
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
            "autopay_enabled": forms.CheckboxInput(attrs={"class": "toggle-checkbox"}),
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


class LeaseExtensionRequestForm(forms.ModelForm):
    class Meta:
        model = LeaseExtensionRequest
        fields = ["requested_end_date", "reason"]
        widgets = {
            "requested_end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Explain why you are requesting a lease extension."}),
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
