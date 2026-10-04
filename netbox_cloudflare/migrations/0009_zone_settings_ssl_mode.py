# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_cloudflare', '0008_zone_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudflarezonesettings',
            name='ssl_mode',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
