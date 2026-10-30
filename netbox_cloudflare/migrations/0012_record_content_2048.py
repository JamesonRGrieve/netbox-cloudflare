# SPDX-License-Identifier: AGPL-3.0-or-later
# Widens CloudflareRecord.content from 255 to Cloudflare's 2048-char limit, so a DKIM TXT (two
# quoted strings, ~410 chars for RSA-2048) fits. A varchar widening: no row changes, and every
# existing value still fits a rollback to 0011 as long as none longer than 255 was stored since.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_cloudflare', '0011_zone_settings_dnssec'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cloudflarerecord',
            name='content',
            field=models.CharField(blank=True, max_length=2048),
        ),
    ]
