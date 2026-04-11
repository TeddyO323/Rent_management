from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .forms import LandlordLoginForm, PropertyForm
from .models import Property, User

LANDLORD_PAGES = {
    "overview": "Overview",
    "properties": "Properties",
    "tenants": "Tenants",
    "payments": "Rent Payments",
    "maintenance": "Maintenance",
    "analytics": "Analytics",
    "notifications": "Notifications",
    "settings": "Settings",
}


def home(request):
    if request.user.is_authenticated:
        return redirect("landlord-dashboard")
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("landlord-dashboard")

    form = LandlordLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=email, password=password)

        if user is None:
            form.add_error(None, "Invalid email or password.")
        elif user.role != User.Role.LANDLORD:
            return HttpResponseForbidden("This login is restricted to landlord accounts.")
        else:
            login(request, user)
            messages.success(request, f"Welcome back, {user.full_name}.")
            return redirect("landlord-dashboard")

    return render(request, "accounts/login.html", {"form": form})


def serialize_property(property_obj):
    return {
        "name": property_obj.name,
        "location": property_obj.location,
        "units": property_obj.units,
        "occupiedUnits": property_obj.occupied_units,
        "revenue": float(property_obj.monthly_revenue),
        "occupancy": property_obj.occupancy,
        "status": property_obj.status,
        "trend": float(property_obj.trend),
    }


@login_required
def landlord_page(request, page="overview"):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can access this dashboard.")
    if page not in LANDLORD_PAGES:
        return HttpResponseForbidden("Unknown landlord page.")
    user_properties = Property.objects.filter(landlord=request.user)
    context = {
        "page_key": page,
        "page_title": LANDLORD_PAGES[page],
        "properties_payload": [serialize_property(item) for item in user_properties],
    }
    return render(request, "landlord/overview.html", context)


@login_required
def add_property(request):
    if request.user.role != User.Role.LANDLORD:
        return HttpResponseForbidden("Only landlord accounts can create properties.")

    user_properties = Property.objects.filter(landlord=request.user)
    form = PropertyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        property_obj = form.save(commit=False)
        property_obj.landlord = request.user
        property_obj.save()
        messages.success(request, f"{property_obj.name} was added to your portfolio.")
        return redirect("landlord-properties")

    context = {
        "form": form,
        "properties_payload": [serialize_property(item) for item in user_properties],
    }
    return render(request, "landlord/add_property.html", context)


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("login")
