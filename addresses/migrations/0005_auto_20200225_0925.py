# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2020-02-25 14:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('addresses', '0004_deliveryfrequency'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deliveryfrequency',
            old_name='delivert_start',
            new_name='delivery_start',
        ),
    ]
