# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_cloudflare --check --dry-run  (dev/ephemeral NetBox)
#
# Add Cloudflare Load Balancing: Monitor -> LBPool -> LBOrigin, plus a zone-scoped LoadBalancer
# whose ordered default-pool list (LBDefaultPool) is the failover priority under steering=off.
# Additive; existing models unchanged.
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_cloudflare", "0001_initial"),
        ("netbox_dns", "0030_dnsseckeytemplate_comments_dnsseckeytemplate_owner_and_more"),
        ("extras", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="CloudflareMonitor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("account", models.CharField(max_length=100)),
                ("type", models.CharField(default="https", max_length=16)),
                ("method", models.CharField(blank=True, default="GET", max_length=8)),
                ("path", models.CharField(blank=True, max_length=255)),
                ("port", models.PositiveIntegerField(blank=True, null=True)),
                ("expected_codes", models.CharField(blank=True, max_length=32)),
                ("expected_body", models.CharField(blank=True, max_length=255)),
                ("header", models.JSONField(blank=True, null=True)),
                ("probe_zone", models.CharField(blank=True, max_length=255)),
                ("interval", models.PositiveIntegerField(default=60)),
                ("timeout", models.PositiveIntegerField(default=5)),
                ("retries", models.PositiveIntegerField(default=2)),
                ("consecutive_up", models.PositiveIntegerField(blank=True, null=True)),
                ("consecutive_down", models.PositiveIntegerField(blank=True, null=True)),
                ("follow_redirects", models.BooleanField(default=False)),
                ("allow_insecure", models.BooleanField(default=False)),
                ("description", models.CharField(blank=True, max_length=200)),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={"verbose_name": "Cloudflare Monitor", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CloudflareLBPool",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("account", models.CharField(max_length=100)),
                ("enabled", models.BooleanField(default=True)),
                ("minimum_origins", models.PositiveIntegerField(default=1)),
                ("notification_email", models.CharField(blank=True, max_length=255)),
                ("description", models.CharField(blank=True, max_length=200)),
                ("monitor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pools", to="netbox_cloudflare.cloudflaremonitor")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={"verbose_name": "Cloudflare LB Pool", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CloudflareLBOrigin",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("name", models.CharField(max_length=100)),
                ("address", models.CharField(max_length=255)),
                ("enabled", models.BooleanField(default=True)),
                ("weight", models.DecimalField(decimal_places=3, default=1, max_digits=4)),
                ("header", models.JSONField(blank=True, null=True)),
                ("pool", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="origins", to="netbox_cloudflare.cloudflarelbpool")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={"verbose_name": "Cloudflare LB Origin", "ordering": ["pool", "name"]},
        ),
        migrations.CreateModel(
            name="CloudflareLoadBalancer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("name", models.CharField(max_length=255)),
                ("steering_policy", models.CharField(default="off", max_length=32)),
                ("session_affinity", models.CharField(default="none", max_length=16)),
                ("proxied", models.BooleanField(default=True)),
                ("enabled", models.BooleanField(default=True)),
                ("ttl", models.PositiveIntegerField(blank=True, null=True)),
                ("description", models.CharField(blank=True, max_length=200)),
                ("fallback_pool", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="fallback_for", to="netbox_cloudflare.cloudflarelbpool")),
                ("zone", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="load_balancers", to="netbox_dns.zone")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={"verbose_name": "Cloudflare Load Balancer", "ordering": ["zone", "name"]},
        ),
        migrations.CreateModel(
            name="CloudflareLBDefaultPool",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("order", models.PositiveIntegerField(default=100)),
                ("load_balancer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pool_assignments", to="netbox_cloudflare.cloudflareloadbalancer")),
                ("pool", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pool_assignments", to="netbox_cloudflare.cloudflarelbpool")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={"verbose_name": "Cloudflare LB Default Pool", "ordering": ["load_balancer", "order"]},
        ),
        migrations.AddField(
            model_name="cloudflareloadbalancer",
            name="default_pools",
            field=models.ManyToManyField(related_name="load_balancers", through="netbox_cloudflare.CloudflareLBDefaultPool", to="netbox_cloudflare.cloudflarelbpool"),
        ),
        migrations.AddConstraint(
            model_name="cloudflaremonitor",
            constraint=models.UniqueConstraint(fields=("name",), name="netbox_cloudflare_monitor_name"),
        ),
        migrations.AddConstraint(
            model_name="cloudflarelbpool",
            constraint=models.UniqueConstraint(fields=("name",), name="netbox_cloudflare_lb_pool_name"),
        ),
        migrations.AddConstraint(
            model_name="cloudflarelborigin",
            constraint=models.UniqueConstraint(fields=("pool", "name"), name="netbox_cloudflare_lb_origin_pool_name"),
        ),
        migrations.AddConstraint(
            model_name="cloudflareloadbalancer",
            constraint=models.UniqueConstraint(fields=("zone", "name"), name="netbox_cloudflare_lb_zone_name"),
        ),
        migrations.AddConstraint(
            model_name="cloudflarelbdefaultpool",
            constraint=models.UniqueConstraint(fields=("load_balancer", "order"), name="netbox_cloudflare_lb_default_pool_order"),
        ),
        migrations.AddConstraint(
            model_name="cloudflarelbdefaultpool",
            constraint=models.UniqueConstraint(fields=("load_balancer", "pool"), name="netbox_cloudflare_lb_default_pool_unique"),
        ),
    ]
