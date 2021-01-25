# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2020-02-27 16:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addresses', '0006_address_delivery_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryfrequency',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='deliveryfrequency',
            name='delivered',
            field=models.BooleanField(default=False),
        ),
    ]