# Generated by Django 5.1.2 on 2025-05-10 15:22

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0006_assignment'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='assignment',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='pages.task'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='pages.topic'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
