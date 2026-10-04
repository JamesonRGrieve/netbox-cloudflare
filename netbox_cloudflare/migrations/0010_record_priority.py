# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_cloudflare', '0009_zone_settings_ssl_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudflarerecord',
            name='priority',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
