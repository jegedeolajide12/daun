# Generated by Django 5.1.2 on 2025-05-31 03:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0038_alter_course_price_tier_alter_course_slug_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='image',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='text',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='video',
            name='owner',
        ),
        migrations.CreateModel(
            name='TopicVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('url', models.URLField(blank=True, null=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='videos')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='pages.topic')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.DeleteModel(
            name='Content',
        ),
        migrations.DeleteModel(
            name='File',
        ),
        migrations.DeleteModel(
            name='Image',
        ),
        migrations.DeleteModel(
            name='Text',
        ),
        migrations.DeleteModel(
            name='Video',
        ),
        migrations.AddConstraint(
            model_name='topicvideo',
            constraint=models.UniqueConstraint(fields=('topic',), name='unique_video_per_topic'),
        ),
    ]
