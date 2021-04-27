# Generated by Django 3.1.2 on 2021-04-15 15:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('id', '0006_idtoken_uploaded'),
    ]

    operations = [
        migrations.AlterField(
            model_name='idtoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
