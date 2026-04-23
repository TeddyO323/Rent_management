from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_propertyunit_tenant_property_unit"),
    ]

    operations = [
        migrations.RenameField(
            model_name="propertyunittype",
            old_name="monthly_price",
            new_name="renting_price",
        ),
        migrations.AddField(
            model_name="propertyunittype",
            name="buying_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="lease_end",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="lease_type",
            field=models.CharField(
                choices=[("Rent", "Rent"), ("Purchase", "Purchase")],
                default="Rent",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="tenant",
            name="monthly_rent",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="tenant",
            name="purchase_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
