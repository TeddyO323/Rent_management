from django.db import migrations, models
import django.db.models.deletion


def create_property_units(apps, schema_editor):
    Property = apps.get_model("accounts", "Property")
    PropertyUnit = apps.get_model("accounts", "PropertyUnit")

    for property_obj in Property.objects.all():
        next_number = 1
        for unit_type in property_obj.unit_types.all():
            for _ in range(unit_type.unit_count):
                PropertyUnit.objects.create(
                    property=property_obj,
                    unit_type=unit_type,
                    unit_number=f"House {next_number}",
                )
                next_number += 1


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_add_tenant"),
    ]

    operations = [
        migrations.CreateModel(
            name="PropertyUnit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("unit_number", models.CharField(max_length=50)),
                ("is_occupied", models.BooleanField(default=False)),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="property_units", to="accounts.property")),
                ("unit_type", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="property_units", to="accounts.propertyunittype")),
            ],
            options={
                "ordering": ["id"],
                "constraints": [
                    models.UniqueConstraint(fields=("property", "unit_number"), name="unique_property_unit_number"),
                ],
            },
        ),
        migrations.AddField(
            model_name="tenant",
            name="property_unit",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="current_tenant", to="accounts.propertyunit"),
        ),
        migrations.RunPython(create_property_units, migrations.RunPython.noop),
    ]
