# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bring CloudflareWAFRuleZone + the WAF rule `zones` M2M in line with models.py.

0003 created the through-table's `tags` as a plain M2M to extras.Tag (its own join table) and
never declared `CloudflareWAFRule.zones`. Django cannot AlterField between a plain M2M and
taggit's TaggableManager, so the stray join table is dropped and `tags` re-added as the
TaggableManager (rows live in extras.TaggedItem, no schema). `zones` rides the existing
through-table, so adding it is state-only."""

import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("extras", "0138_customfieldchoiceset_choice_colors"),
        ("netbox_cloudflare", "0006_record_unmanaged"),
        ("netbox_dns", "0031_record_netbox_dns_record_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cloudflarewafrule",
            name="zones",
            field=models.ManyToManyField(
                blank=True,
                help_text="Zones (netbox_dns) this rule applies to.",
                related_name="waf_rules",
                through="netbox_cloudflare.CloudflareWAFRuleZone",
                to="netbox_dns.zone",
            ),
        ),
        migrations.AlterField(
            model_name="cloudflarewafrulezone",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
        ),
        migrations.RemoveField(model_name="cloudflarewafrulezone", name="tags"),
        migrations.AddField(
            model_name="cloudflarewafrulezone",
            name="tags",
            field=taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
        ),
    ]
