# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2020-02-25 17:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_charge'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoxSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=120)),
                ('billing', models.CharField(blank=True, max_length=120, null=True)),
                ('paid', models.BooleanField(default=False)),
                ('canceled_at', models.CharField(blank=True, max_length=120, null=True)),
                ('plan', models.TextField(blank=True, null=True)),
                ('usage_type', models.CharField(blank=True, max_length=120, null=True)),
                ('interval', models.CharField(blank=True, max_length=120, null=True)),
                ('currency', models.CharField(blank=True, max_length=120, null=True)),
                ('amount', models.CharField(blank=True, max_length=120, null=True)),
                ('billing_cycle_anchor', models.DateTimeField(blank=True, null=True)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(blank=True, max_length=120, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('billing_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='billing.BillingProfile')),
            ],
        ),
    ]