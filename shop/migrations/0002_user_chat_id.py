# Generated by Django 5.1.7 on 2025-03-29 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='chat_id',
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
    ]
