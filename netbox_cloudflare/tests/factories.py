# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real-instance factories for the test suite (NO MOCKS). Build genuine netbox_dns Zone and
netbox_pf Alias rows the Cloudflare models FK.

A netbox_dns Zone needs a NameServer for its SOA MNAME plus an SOA RName; its View, TTL and the
numeric SOA fields auto-fill from plugin defaults in Zone.clean_fields (run by Zone.save()).

A netbox_pf Alias needs a unique `name` and a `type` (AliasTypeChoices); `content` holds the IP/
network members (one per line)."""

from netbox_dns.models import NameServer, Zone
from netbox_pf.choices import AliasTypeChoices
from netbox_pf.models import Alias


def make_zone(name="example.com"):
    """A real netbox_dns Zone, with the minimal SOA inputs the model requires."""
    ns = NameServer.objects.create(name=f"ns1.{name}")
    return Zone.objects.create(name=name, soa_mname=ns, soa_rname=f"hostmaster.{name}")


def make_alias(name="exempt", content="198.51.100.0/24"):
    """A real netbox_pf Alias (a named network list); `name` is unique, `type` is required."""
    return Alias.objects.create(name=name, type=AliasTypeChoices.NETWORK, content=content)


def make_monitor(name="wp-https", **kwargs):
    """A real CloudflareMonitor. An https monitor requires a path + expected_codes (clean())."""
    from ..models import CloudflareMonitor

    defaults = {
        "account": "omg",
        "type": "https",
        "path": "/",
        "expected_codes": "200",
    }
    return CloudflareMonitor.objects.create(name=name, **{**defaults, **kwargs})


def make_pool(name="omg-origin", monitor=None, **kwargs):
    from ..models import CloudflareLBPool

    return CloudflareLBPool.objects.create(
        name=name, account="omg", monitor=monitor, **kwargs
    )
