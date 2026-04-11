from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Create demo landlord and tenant accounts for local development."

    def handle(self, *args, **options):
        demo_accounts = [
            {
                "email": "landlord.demo@smartrent.local",
                "password": "DemoPass123!",
                "full_name": "Demo Landlord",
                "role": User.Role.LANDLORD,
            },
            {
                "email": "tenant.demo@smartrent.local",
                "password": "DemoPass123!",
                "full_name": "Demo Tenant",
                "role": User.Role.TENANT,
            },
        ]

        for payload in demo_accounts:
            user, created = User.objects.get_or_create(
                email=payload["email"],
                defaults={
                    "full_name": payload["full_name"],
                    "role": payload["role"],
                },
            )

            user.full_name = payload["full_name"]
            user.role = payload["role"]
            user.set_password(payload["password"])
            user.save()

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} {payload['role'].lower()} account: {payload['email']}"
                )
            )
