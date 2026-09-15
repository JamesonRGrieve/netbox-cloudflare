# SPDX-License-Identifier: AGPL-3.0-or-later
"""Add CloudflareRecord.unmanaged — records documented in NetBox but owned externally
(e.g. Stalwart's automatic DNS management). The tofu cloudflare apply excludes unmanaged
records so it neither creates nor fights the external manager, while NetBox stays the
complete source of truth."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_cloudflare", "0005_lb_session_affinity_default_none"),
    ]

    operations = [
        migrations.AddField(
            model_name="cloudflarerecord",
            name="unmanaged",
            field=models.BooleanField(default=False),
        ),
    ]
