# SPDX-License-Identifier: AGPL-3.0-or-later
"""Default CF Load Balancer session affinity to cookie + migrate existing 'none' rows.

Cookie session affinity pins each client to a single edge origin. Without it, a
client whose requests bounce between origins (LB failover, or health flapping)
lands on an origin that has no record of its session — each edge keeps its OWN
session store (per-node Redis) — producing WooCommerce's "Sorry, your session has
expired" mid-checkout (reported on bigheartsfirstaid.com, 2026-09-15).

Cookie is now the model default for every managed LB. Existing rows seeded with the
old "none" default are flipped to "cookie" here so the whole fleet converges without
per-row edits; a row later set to a different real mode (ip_cookie/header) is kept.
"""
from django.db import migrations, models


def forwards_none_to_cookie(apps, schema_editor):
    """Flip every LB still on the old 'none' default to 'cookie'."""
    LB = apps.get_model("netbox_cloudflare", "CloudflareLoadBalancer")
    LB.objects.filter(session_affinity="none").update(session_affinity="cookie")


def backwards_noop(apps, schema_editor):
    """Irreversible data flip: we can't distinguish rows that were originally 'none'
    from rows explicitly set to 'cookie', so leave the data untouched on reverse."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_cloudflare", "0003_waf_rule_m2m_zones"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cloudflareloadbalancer",
            name="session_affinity",
            field=models.CharField(default="cookie", max_length=16),
        ),
        migrations.RunPython(forwards_none_to_cookie, backwards_noop),
    ]
