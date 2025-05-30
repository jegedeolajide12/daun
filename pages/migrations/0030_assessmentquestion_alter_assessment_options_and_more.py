# Generated by Django 5.1.2 on 2025-05-17 08:46

import django.db.models.deletion
import pages.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0029_rename_mcqassessment_assessment_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssessmentQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(help_text='Enter the question text in full', verbose_name='Question Text')),
                ('explanation', models.TextField(blank=True, help_text='Explanation to be shown after answering', null=True, verbose_name='Explanation')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this question is active for use', verbose_name='Is Active')),
                ('order', pages.fields.OrderField(blank=True)),
            ],
            options={
                'verbose_name': 'Assessment Question',
                'verbose_name_plural': 'Assessment Questions',
                'ordering': ['order'],
            },
        ),
        migrations.AlterModelOptions(
            name='assessment',
            options={'verbose_name': 'Assessment', 'verbose_name_plural': 'Assessments'},
        ),
        migrations.RemoveConstraint(
            model_name='mcqoption',
            name='unique_option_order_per_assessment',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='difficulty',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='explanation',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='order',
        ),
        migrations.RemoveField(
            model_name='assessment',
            name='question',
        ),
        migrations.RemoveField(
            model_name='mcqoption',
            name='assessment',
        ),
        migrations.AddField(
            model_name='assessment',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_assessments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='assessmentquestion',
            name='assessment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='pages.assessment'),
        ),
        migrations.AddField(
            model_name='mcqoption',
            name='question',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='options', to='pages.assessmentquestion'),
        ),
        migrations.AddConstraint(
            model_name='mcqoption',
            constraint=models.UniqueConstraint(fields=('question', 'order'), name='unique_option_order_per_assessment'),
        ),
    ]
