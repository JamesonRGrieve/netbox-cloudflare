# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored initial migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_cloudflare --check --dry-run   (dev/ephemeral NetBox)
#
# Dependencies:
#   * extras 0001_initial — the TaggableManager through-table (extras.TaggedItem/extras.Tag).
#   * ipam   0001_initial — the ipam.Prefix table, target of the CloudflareWAFRule.ip_prefixes M2M.
#   * netbox_dns 0030 (the plugin's LATEST migration) — the Zone table FK-ed by CloudflareRecord
#     (PROTECT) and CloudflareWAFRule (CASCADE). Depending on the leaf guarantees the Zone table
#     plus every later alteration exists before these CreateModels run.
# `0001_initial` resolves through Django's `replaces` aliasing to the squashed extras/ipam
# migrations that ship with NetBox 4.6.
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("extras", "0001_initial"),
        ("ipam", "0001_initial"),
        ("netbox_dns", "0030_dnsseckeytemplate_comments_dnsseckeytemplate_owner_and_more"),
    ]
    operations = [
        migrations.CreateModel(
            name="CloudflareTunnel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("account", models.CharField(max_length=100)),
                ("tunnel_id", models.CharField(blank=True, max_length=64)),
                ("comment", models.CharField(blank=True, max_length=255)),
                (
                    "tags",
                    taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={"verbose_name": "Cloudflare Tunnel", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CloudflareIngress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
                    ),
                ),
                ("hostname", models.CharField(blank=True, max_length=255)),
                ("path", models.CharField(blank=True, max_length=255)),
                ("service", models.CharField(max_length=255)),
                ("order", models.PositiveIntegerField(default=100)),
                ("origin_request", models.JSONField(blank=True, null=True)),
                (
                    "tunnel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ingress_rules",
                        to="netbox_cloudflare.cloudflaretunnel",
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={"verbose_name": "Cloudflare Ingress Rule", "ordering": ["tunnel", "order"]},
        ),
        migrations.CreateModel(
            name="CloudflareRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("type", models.CharField(max_length=16)),
                ("content", models.CharField(blank=True, max_length=255)),
                ("proxied", models.BooleanField(default=True)),
                ("ttl", models.PositiveIntegerField(default=1)),
                ("ddns_enabled", models.BooleanField(default=False)),
                ("ddns_source", models.CharField(blank=True, max_length=255)),
                (
                    "zone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cloudflare_records",
                        to="netbox_dns.zone",
                    ),
                ),
                (
                    "tunnel",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="records",
                        to="netbox_cloudflare.cloudflaretunnel",
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={"verbose_name": "Cloudflare Record", "ordering": ["zone", "name", "type"]},
        ),
        migrations.CreateModel(
            name="CloudflareWAFRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
                    ),
                ),
                ("phase", models.CharField(default="http_request_firewall_custom", max_length=40)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("expression", models.TextField()),
                ("action", models.CharField(max_length=20)),
                ("order", models.PositiveIntegerField(default=100)),
                ("enabled", models.BooleanField(default=True)),
                ("ratelimit_threshold", models.PositiveIntegerField(blank=True, null=True)),
                ("ratelimit_period", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "zone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="waf_rules",
                        to="netbox_dns.zone",
                    ),
                ),
                (
                    "ip_prefixes",
                    models.ManyToManyField(
                        blank=True, related_name="cloudflare_waf_rules", to="ipam.prefix"
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={"verbose_name": "Cloudflare WAF Rule", "ordering": ["zone", "order"]},
        ),
        migrations.AddConstraint(
            model_name="cloudflaretunnel",
            constraint=models.UniqueConstraint(
                fields=("name",), name="netbox_cloudflare_tunnel_name"
            ),
        ),
        migrations.AddConstraint(
            model_name="cloudflareingress",
            constraint=models.UniqueConstraint(
                fields=("tunnel", "order"), name="netbox_cloudflare_ingress_tunnel_order"
            ),
        ),
        migrations.AddConstraint(
            model_name="cloudflarerecord",
            constraint=models.UniqueConstraint(
                fields=("zone", "name", "type", "content"),
                name="netbox_cloudflare_record_zone_name_type_content",
            ),
        ),
        migrations.AddConstraint(
            model_name="cloudflarewafrule",
            constraint=models.UniqueConstraint(
                fields=("zone", "order"), name="netbox_cloudflare_waf_rule_zone_order"
            ),
        ),
    ]
