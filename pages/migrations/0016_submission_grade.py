# Generated by Django 5.1.2 on 2025-05-13 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0015_remove_submission_file_submissionfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='grade',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
