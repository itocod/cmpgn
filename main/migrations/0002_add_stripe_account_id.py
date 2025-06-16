from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),  # Make sure this matches your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='stripe_account_id',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
