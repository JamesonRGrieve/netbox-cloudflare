# SPDX-License-Identifier: AGPL-3.0-or-later
"""Migrate CloudflareWAFRule.zone FK → zones M2M with CloudflareWAFRuleZone through-table.

Steps:
  1. Create the through-table CloudflareWAFRuleZone.
  2. Copy existing FK relationships into the through-table (preserving the per-zone enabled state).
  3. Remove the old FK column + its unique constraint.
"""
from django.db import migrations, models
import django.db.models.deletion


def forwards_copy_fk_to_m2m(apps, schema_editor):
    """Copy each WAFRule's zone FK into a CloudflareWAFRuleZone row."""
    WAFRule = apps.get_model("netbox_cloudflare", "CloudflareWAFRule")
    WAFRuleZone = apps.get_model("netbox_cloudflare", "CloudflareWAFRuleZone")
    for rule in WAFRule.objects.filter(zone__isnull=False):
        WAFRuleZone.objects.get_or_create(
            rule=rule,
            zone=rule.zone,
            defaults={"enabled": None},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_cloudflare", "0002_load_balancing"),
        ("netbox_dns", "0030_dnsseckeytemplate_comments_dnsseckeytemplate_owner_and_more"),
        ("extras", "0001_initial"),
    ]

    operations = [
        # 1. Create the through-table
        migrations.CreateModel(
            name="CloudflareWAFRuleZone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, null=True),
                ),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=None),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        blank=True,
                        null=True,
                        default=None,
                        help_text="Override the rule's default enabled state for this zone. Null = inherit.",
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="zone_assignments",
                        to="netbox_cloudflare.cloudflarewafrule",
                    ),
                ),
                (
                    "zone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="waf_rule_assignments",
                        to="netbox_dns.zone",
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(blank=True, related_name="+", to="extras.tag"),
                ),
            ],
            options={
                "verbose_name": "WAF Rule Zone Assignment",
                "ordering": ["rule", "zone"],
            },
        ),
        migrations.AddConstraint(
            model_name="cloudflarewafrulezone",
            constraint=models.UniqueConstraint(
                fields=["rule", "zone"],
                name="netbox_cloudflare_waf_rule_zone_unique",
            ),
        ),
        # 2. Copy FK data to M2M
        migrations.RunPython(forwards_copy_fk_to_m2m, migrations.RunPython.noop),
        # 3. Remove old FK + constraint
        migrations.RemoveConstraint(
            model_name="cloudflarewafrule",
            name="netbox_cloudflare_waf_rule_zone_order",
        ),
        migrations.RemoveField(
            model_name="cloudflarewafrule",
            name="zone",
        ),
        # 4. Update ordering
        migrations.AlterModelOptions(
            name="cloudflarewafrule",
            options={"ordering": ["order"], "verbose_name": "Cloudflare WAF Rule"},
        ),
    ]
