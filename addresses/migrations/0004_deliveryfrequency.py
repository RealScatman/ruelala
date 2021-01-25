# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2020-02-25 13:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_charge'),
        ('addresses', '0003_auto_20200224_1444'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryFrequency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_frequency', models.CharField(choices=[('every-week', 'Every Week'), ('every-other-week', 'Every Other Week')], default='Every Week', max_length=120)),
                ('delivert_start', models.DateTimeField(blank=True, null=True)),
                ('billing_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='billing.BillingProfile')),
            ],
        ),
    ]
