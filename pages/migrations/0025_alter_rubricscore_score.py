# Generated by Django 5.1.2 on 2025-05-15 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0024_rubricscore'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rubricscore',
            name='score',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
