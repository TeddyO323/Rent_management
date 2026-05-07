from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be provided.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.LANDLORD)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        LANDLORD = "LANDLORD", "Landlord"
        TENANT = "TENANT", "Tenant"

    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.LANDLORD)
    full_name = models.CharField(max_length=255, blank=True)
    password_change_required = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if not self.full_name:
            self.full_name = self.get_full_name() or self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.role})"


class LandlordSettings(models.Model):
    landlord = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="landlord_settings",
    )
    business_name = models.CharField(max_length=255, blank=True)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=32, blank=True)
    owner_digest_enabled = models.BooleanField(default=True)
    weekly_report_enabled = models.BooleanField(default=True)
    maintenance_escalation_enabled = models.BooleanField(default=True)
    autopay_nudges_enabled = models.BooleanField(default=False)
    rent_reminder_days = models.PositiveSmallIntegerField(default=5)
    overdue_follow_up_days = models.PositiveSmallIntegerField(default=2)
    maintenance_escalation_hours = models.PositiveSmallIntegerField(default=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Landlord settings"
        verbose_name_plural = "Landlord settings"

    def __str__(self):
        return self.business_name or self.landlord.full_name or self.landlord.email


class Property(models.Model):
    class Status(models.TextChoices):
        HIGH_PERFORMING = "High Performing", "High Performing"
        STABLE = "Stable", "Stable"
        NEEDS_ATTENTION = "Needs Attention", "Needs Attention"
        VACANCY_RISK = "Vacancy Risk", "Vacancy Risk"

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="properties",
    )
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    units = models.PositiveIntegerField(default=0)
    occupied_units = models.PositiveIntegerField(default=0)
    monthly_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    occupancy = models.PositiveIntegerField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.STABLE)
    trend = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "name"]

    def save(self, *args, **kwargs):
        if self.units:
            calculated = round((self.occupied_units / self.units) * 100)
            self.occupancy = max(0, min(100, calculated))
        else:
            self.occupancy = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PropertyUnitType(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="unit_types",
    )
    unit_type = models.CharField(max_length=120)
    unit_count = models.PositiveIntegerField()
    renting_price = models.DecimalField(max_digits=12, decimal_places=2)
    buying_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.property.name} - {self.unit_type}"


class PropertyUnit(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="property_units",
    )
    unit_type = models.ForeignKey(
        PropertyUnitType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="property_units",
    )
    unit_number = models.CharField(max_length=50)
    is_occupied = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "unit_number"],
                name="unique_property_unit_number",
            )
        ]

    def __str__(self):
        return f"{self.property.name} - {self.unit_number}"


class Tenant(models.Model):
    class LeaseType(models.TextChoices):
        RENT = "Rent", "Rent"
        PURCHASE = "Purchase", "Purchase"

    class Status(models.TextChoices):
        GOOD_STANDING = "Good Standing", "Good Standing"
        RENEWING_SOON = "Renewing Soon", "Renewing Soon"
        WATCHLIST = "Watchlist", "Watchlist"
        INACTIVE = "Inactive", "Inactive"

    class RiskLevel(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenants",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tenant_profile",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="tenants",
    )
    property_unit = models.OneToOneField(
        PropertyUnit,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="current_tenant",
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    id_number = models.CharField(max_length=50, blank=True)
    unit_number = models.CharField(max_length=20)
    lease_start = models.DateField()
    lease_end = models.DateField(null=True, blank=True)
    lease_type = models.CharField(
        max_length=20,
        choices=LeaseType.choices,
        default=LeaseType.RENT,
    )
    last_rent_charge_at = models.DateTimeField(null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    autopay_enabled = models.BooleanField(default=False)
    autopay_bank_name = models.CharField(max_length=120, blank=True)
    autopay_account_holder = models.CharField(max_length=255, blank=True)
    autopay_account_number = models.CharField(max_length=64, blank=True)
    autopay_card_number = models.CharField(max_length=32, blank=True)
    autopay_card_expiry = models.CharField(max_length=10, blank=True)
    rent_credit_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.GOOD_STANDING,
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW,
    )
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "full_name"]

    def __str__(self):
        return f"{self.full_name} - {self.property.name} ({self.unit_number})"


class LeaseExtensionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        UNDER_REVIEW = "Under Review", "Under Review"
        APPROVED = "Approved", "Approved"
        DECLINED = "Declined", "Declined"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="lease_extension_requests",
    )
    requested_end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    landlord_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tenant.full_name} - {self.requested_end_date}"


class Complaint(models.Model):
    class Category(models.TextChoices):
        ELECTRICITY = "Electricity", "Electricity"
        PLUMBING = "Plumbing", "Plumbing"
        WINDOWS = "Windows", "Windows"
        SECURITY = "Security", "Security"
        CLEANING = "Cleaning", "Cleaning"
        OTHER = "Other", "Other"

    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        IN_PROGRESS = "In Progress", "In Progress"
        RESOLVED = "Resolved", "Resolved"
        REJECTED = "Rejected", "Rejected"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="complaints",
    )
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=Category.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    landlord_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tenant.full_name} - {self.title}"


class Notification(models.Model):
    class Category(models.TextChoices):
        PAYMENTS = "Payments & Bills", "Payments & Bills"
        LEASE = "Lease & Occupancy", "Lease & Occupancy"
        MAINTENANCE = "Maintenance & Account", "Maintenance & Account"
        ACCOUNT = "Account", "Account"

    class Priority(models.TextChoices):
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications_received",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    category = models.CharField(max_length=40, choices=Category.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link_url = models.CharField(max_length=255, blank=True)
    dedupe_key = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_read", "-created_at", "-id"]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"


class MaintenanceExpense(models.Model):
    class CostBearer(models.TextChoices):
        TENANT = "Tenant", "Tenant"
        MANAGEMENT = "Management", "Management"
        LANDLORD = "Landlord", "Landlord"

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="maintenance_expenses",
    )
    bill = models.OneToOneField(
        "Bill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_expense",
    )
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_bearer = models.CharField(max_length=20, choices=CostBearer.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.complaint.title} - {self.title}"


class Bill(models.Model):
    class Category(models.TextChoices):
        RENT = "Rent", "Rent"
        SERVICE_CHARGE = "Service Charge", "Service Charge"
        WATER = "Water Bill", "Water Bill"
        REPAIRS = "Repair Bill", "Repair Bill"
        OTHER = "Other", "Other"

    class Status(models.TextChoices):
        UNPAID = "Unpaid", "Unpaid"
        PARTIALLY_PAID = "Partially Paid", "Partially Paid"
        PAID = "Paid", "Paid"

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bills",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="bills",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bills",
    )
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk is None and self.remaining_amount in (None, 0):
            self.remaining_amount = self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.amount}"


class Payment(models.Model):
    class Method(models.TextChoices):
        MPESA = "M-Pesa", "M-Pesa"
        BANK = "Bank Transfer", "Bank Transfer"
        CASH = "Cash", "Cash"
        CARD = "Card", "Card"

    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        CONFIRMED = "Confirmed", "Confirmed"
        REJECTED = "Rejected", "Rejected"

    class Scope(models.TextChoices):
        BILL = "Bill", "Specific Bill"
        RENT = "Rent", "Rent"
        ALL = "All", "All Open Bills"

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    bill = models.ForeignKey(
        Bill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    selected_bill_ids = models.TextField(blank=True)
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.ALL)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    rent_periods = models.PositiveIntegerField(default=0)
    paid_on = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-created_at"]

    def __str__(self):
        return f"{self.tenant.full_name} - {self.amount} on {self.paid_on}"


class PaymentAllocation(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "bill"],
                name="unique_payment_bill_allocation",
            )
        ]

    def __str__(self):
        return f"{self.payment} -> {self.bill} ({self.amount})"
