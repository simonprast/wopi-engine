# Generated by Django 3.1.2 on 2021-05-06 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('insurancesubmission', '0013_auto_20210429_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='page_index',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
