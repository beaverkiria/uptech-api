# Generated by Django 3.2.3 on 2021-05-29 23:44

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_product_name_gin_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='analogue_ids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.BigIntegerField(), default=list, size=None),
        ),
        migrations.AddField(
            model_name='product',
            name='contraindications',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='convenience',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='detail_page_url',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='effectiveness',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='medsis_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='safety',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='score',
            field=models.DecimalField(decimal_places=1, max_digits=3, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='side_effects',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='tolerance',
            field=models.IntegerField(null=True),
        ),
    ]
