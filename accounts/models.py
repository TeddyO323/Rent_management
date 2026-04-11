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
    units = models.PositiveIntegerField()
    occupied_units = models.PositiveIntegerField()
    monthly_revenue = models.DecimalField(max_digits=12, decimal_places=2)
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
