from django import forms

from .models import Property


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
        fields = [
            "name",
            "location",
            "units",
            "occupied_units",
            "monthly_revenue",
            "status",
            "trend",
        ]
    

    def clean(self):
        cleaned_data = super().clean()
        units = cleaned_data.get("units") or 0
        occupied_units = cleaned_data.get("occupied_units") or 0
        if occupied_units > units:
            self.add_error("occupied_units", "Occupied units cannot be greater than total units.")
        return cleaned_data
