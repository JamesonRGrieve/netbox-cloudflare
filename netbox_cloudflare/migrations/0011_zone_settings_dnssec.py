# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_cloudflare', '0010_record_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudflarezonesettings',
            name='dnssec',
            field=models.BooleanField(default=False),
        ),
    ]
