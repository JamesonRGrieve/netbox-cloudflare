# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model tests against a real DB (no mocks): creation, str/url/color, uniqueness constraints,
the CloudflareRecord.clean() one-driver rule, the ip_alias FK to netbox_pf.Alias, and the FK
delete behaviors (zone PROTECT on records, zone CASCADE on WAF rules, tunnel CASCADE on ingress,
tunnel SET_NULL on records, ip_alias PROTECT on WAF rules). Real netbox_dns Zone + netbox_pf Alias
instances back everything."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase

from netbox_cloudflare.choices import (
    CloudflareRecordTypeChoices,
    CloudflareWAFActionChoices,
    CloudflareWAFPhaseChoices,
)
from netbox_cloudflare.models import (
    CloudflareIngress,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
)

from .factories import make_alias, make_zone


class CloudflareTunnelModelTest(TestCase):
    def test_create_str_url(self):
        t = CloudflareTunnel.objects.create(name="house", account="acct-1", tunnel_id="uuid-1")
        self.assertEqual(str(t), "house")
        self.assertIn("/plugins/cloudflare/tunnels/", t.get_absolute_url())

    def test_name_unique(self):
        CloudflareTunnel.objects.create(name="omg", account="acct-1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareTunnel.objects.create(name="omg", account="acct-2")


class CloudflareIngressModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tunnel = CloudflareTunnel.objects.create(name="t", account="a", tunnel_id="u")

    def test_create_str_url(self):
        i = CloudflareIngress.objects.create(
            tunnel=self.tunnel, hostname="app.example.com", service="http://10.0.0.1:80", order=1
        )
        self.assertIn("app.example.com", str(i))
        self.assertIn("/plugins/cloudflare/ingress-rules/", i.get_absolute_url())

    def test_catchall_blank_hostname(self):
        i = CloudflareIngress.objects.create(
            tunnel=self.tunnel, service="http_status:404", order=999
        )
        self.assertIn("catch-all", str(i))

    def test_unique_tunnel_order(self):
        CloudflareIngress.objects.create(tunnel=self.tunnel, service="http://10.0.0.1:80", order=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareIngress.objects.create(
                tunnel=self.tunnel, service="http://10.0.0.2:80", order=1
            )

    def test_cascade_from_tunnel(self):
        i = CloudflareIngress.objects.create(
            tunnel=self.tunnel, service="http://10.0.0.1:80", order=2
        )
        pk = i.pk
        self.tunnel.delete()
        self.assertFalse(CloudflareIngress.objects.filter(pk=pk).exists())


class CloudflareRecordModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zone = make_zone("example.com")
        cls.tunnel = CloudflareTunnel.objects.create(name="t", account="a", tunnel_id="u")

    def test_create_str_url_color_defaults(self):
        r = CloudflareRecord.objects.create(
            zone=self.zone,
            name="www",
            type=CloudflareRecordTypeChoices.A,
            content="203.0.113.10",
        )
        self.assertIn("www", str(r))
        self.assertIn("/plugins/cloudflare/records/", r.get_absolute_url())
        self.assertTrue(r.proxied)
        self.assertEqual(r.ttl, 1)
        self.assertEqual(r.get_type_color(), "blue")

    def test_clean_static_content_ok(self):
        r = CloudflareRecord(
            zone=self.zone, name="a", type=CloudflareRecordTypeChoices.A, content="203.0.113.1"
        )
        r.clean()  # no exception

    def test_clean_tunnel_ok(self):
        r = CloudflareRecord(
            zone=self.zone, name="b", type=CloudflareRecordTypeChoices.CNAME, tunnel=self.tunnel
        )
        r.clean()

    def test_clean_ddns_ok(self):
        r = CloudflareRecord(
            zone=self.zone,
            name="c",
            type=CloudflareRecordTypeChoices.A,
            ddns_enabled=True,
            ddns_source="wan0",
        )
        r.clean()

    def test_clean_no_driver_rejected(self):
        r = CloudflareRecord(zone=self.zone, name="d", type=CloudflareRecordTypeChoices.A)
        with self.assertRaises(ValidationError):
            r.clean()

    def test_clean_two_drivers_rejected(self):
        r = CloudflareRecord(
            zone=self.zone,
            name="e",
            type=CloudflareRecordTypeChoices.A,
            content="203.0.113.1",
            tunnel=self.tunnel,
        )
        with self.assertRaises(ValidationError):
            r.clean()

    def test_clean_ddns_requires_source(self):
        r = CloudflareRecord(
            zone=self.zone, name="f", type=CloudflareRecordTypeChoices.A, ddns_enabled=True
        )
        with self.assertRaises(ValidationError):
            r.clean()

    def test_protect_zone(self):
        protected = make_zone("protected.example")
        CloudflareRecord.objects.create(
            zone=protected, name="keep", type=CloudflareRecordTypeChoices.A, content="203.0.113.9"
        )
        with self.assertRaises(ProtectedError), transaction.atomic():
            protected.delete()

    def test_tunnel_set_null_on_delete(self):
        r = CloudflareRecord.objects.create(
            zone=self.zone, name="g", type=CloudflareRecordTypeChoices.CNAME, tunnel=self.tunnel
        )
        self.tunnel.delete()
        r.refresh_from_db()
        self.assertIsNone(r.tunnel_id)


class CloudflareWAFRuleModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zone = make_zone("waf.example")

    def test_create_str_url_colors(self):
        rule = CloudflareWAFRule.objects.create(
            zone=self.zone,
            phase=CloudflareWAFPhaseChoices.CUSTOM,
            expression='(ip.src in $exempt)',
            action=CloudflareWAFActionChoices.BLOCK,
            order=1,
        )
        self.assertIn("waf.example", str(rule))
        self.assertIn("/plugins/cloudflare/waf-rules/", rule.get_absolute_url())
        self.assertEqual(rule.get_action_color(), "red")
        self.assertEqual(rule.get_phase_color(), "blue")
        self.assertTrue(rule.enabled)

    def test_unique_zone_order(self):
        CloudflareWAFRule.objects.create(
            zone=self.zone, expression="x", action=CloudflareWAFActionChoices.LOG, order=5
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareWAFRule.objects.create(
                zone=self.zone, expression="y", action=CloudflareWAFActionChoices.BLOCK, order=5
            )

    def test_cascade_from_zone(self):
        zone = make_zone("cascade.example")
        rule = CloudflareWAFRule.objects.create(
            zone=zone, expression="z", action=CloudflareWAFActionChoices.BLOCK, order=1
        )
        pk = rule.pk
        zone.delete()
        self.assertFalse(CloudflareWAFRule.objects.filter(pk=pk).exists())

    def test_ip_alias_fk(self):
        alias = make_alias("exempt", "198.51.100.0/24\n203.0.113.0/24")
        rule = CloudflareWAFRule.objects.create(
            zone=self.zone,
            expression="m",
            action=CloudflareWAFActionChoices.SKIP,
            order=10,
            ip_alias=alias,
        )
        self.assertEqual(rule.ip_alias, alias)
        self.assertIn(rule, alias.cloudflare_waf_rules.all())

    def test_ip_alias_protect_on_delete(self):
        alias = make_alias("protected-alias", "198.51.100.0/24")
        CloudflareWAFRule.objects.create(
            zone=self.zone,
            expression="p",
            action=CloudflareWAFActionChoices.BLOCK,
            order=11,
            ip_alias=alias,
        )
        with self.assertRaises(ProtectedError), transaction.atomic():
            alias.delete()
