# Generated by Django 5.1.5 on 2025-02-17 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0002_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='score',
            name='basicCredits',
            field=models.IntegerField(default=0),
        ),
    ]
