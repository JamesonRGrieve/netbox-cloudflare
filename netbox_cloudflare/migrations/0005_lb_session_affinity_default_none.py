# SPDX-License-Identifier: AGPL-3.0-or-later
"""Revert CF LB session affinity default back to "none" + flip cookie rows to none.

Session affinity is a load-balancing stickiness knob, not a failover/HA control: pinning
a client to a single origin fights proper failover. It was briefly made the fleet default
(0004) to mask a flap-induced WooCommerce session loss, but that was the wrong knob — the
real fix is upstream (stop the origin flap / share the session store). Revert: default back
to "none", and flip any remaining "cookie" rows to "none".
"""
from django.db import migrations, models


def forwards_cookie_to_none(apps, schema_editor):
    LB = apps.get_model("netbox_cloudflare", "CloudflareLoadBalancer")
    LB.objects.filter(session_affinity="cookie").update(session_affinity="none")


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_cloudflare", "0004_lb_session_affinity_cookie_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cloudflareloadbalancer",
            name="session_affinity",
            field=models.CharField(default="none", max_length=16),
        ),
        migrations.RunPython(forwards_cookie_to_none, backwards_noop),
    ]
