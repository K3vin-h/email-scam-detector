from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailrecord",
            name="reasons",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
