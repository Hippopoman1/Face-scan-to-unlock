# Generated by Django 5.1.1 on 2025-01-28 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesscontrol',
            name='swit',
            field=models.CharField(blank=True, default=0, max_length=2),
        ),
    ]
