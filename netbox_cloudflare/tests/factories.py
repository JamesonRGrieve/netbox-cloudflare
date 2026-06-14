# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real-instance factories for the test suite (NO MOCKS). Build genuine netbox_dns Zone and
core ipam Prefix rows the four Cloudflare models FK / M2M.

A netbox_dns Zone needs a NameServer for its SOA MNAME plus an SOA RName; its View, TTL and the
numeric SOA fields auto-fill from plugin defaults in Zone.clean_fields (run by Zone.save())."""

from ipam.models import Prefix
from netbox_dns.models import NameServer, Zone


def make_zone(name="example.com"):
    """A real netbox_dns Zone, with the minimal SOA inputs the model requires."""
    ns = NameServer.objects.create(name=f"ns1.{name}")
    return Zone.objects.create(name=name, soa_mname=ns, soa_rname=f"hostmaster.{name}")


def make_prefix(prefix="192.0.2.0/24"):
    """A real core ipam Prefix (only `prefix` is required)."""
    return Prefix.objects.create(prefix=prefix)
