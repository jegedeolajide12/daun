# Generated by Django 5.1.2 on 2025-05-17 11:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0033_task_assessment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='assessment',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assessment_task', to='pages.assessment'),
        ),
    ]
