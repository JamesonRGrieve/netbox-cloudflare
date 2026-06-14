# SPDX-License-Identifier: AGPL-3.0-or-later
"""FilterSet tests against a real DB (no mocks): explicit FK `_id` scoping + choice/bool filters
across the four models. Real netbox_dns Zone + netbox_pf Alias instances back the FKs."""

from django.test import TestCase

from netbox_cloudflare.choices import (
    CloudflareRecordTypeChoices,
    CloudflareWAFActionChoices,
    CloudflareWAFPhaseChoices,
)
from netbox_cloudflare.filtersets import (
    CloudflareIngressFilterSet,
    CloudflareRecordFilterSet,
    CloudflareTunnelFilterSet,
    CloudflareWAFRuleFilterSet,
)
from netbox_cloudflare.models import (
    CloudflareIngress,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
)

from .factories import make_alias, make_zone


class CloudflareTunnelFilterSetTest(TestCase):
    queryset = CloudflareTunnel.objects.all()

    @classmethod
    def setUpTestData(cls):
        CloudflareTunnel.objects.create(name="house", account="acct-1", tunnel_id="u1")
        CloudflareTunnel.objects.create(name="omg", account="acct-2", tunnel_id="u2")

    def test_account(self):
        self.assertEqual(
            CloudflareTunnelFilterSet({"account": ["acct-1"]}, self.queryset).qs.count(), 1
        )

    def test_search(self):
        self.assertEqual(CloudflareTunnelFilterSet({"q": "omg"}, self.queryset).qs.count(), 1)


class CloudflareIngressFilterSetTest(TestCase):
    queryset = CloudflareIngress.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.t1 = CloudflareTunnel.objects.create(name="t1", account="a", tunnel_id="u1")
        cls.t2 = CloudflareTunnel.objects.create(name="t2", account="a", tunnel_id="u2")
        CloudflareIngress.objects.create(tunnel=cls.t1, hostname="a.example", service="http://10.0.0.1:80", order=1)
        CloudflareIngress.objects.create(tunnel=cls.t1, hostname="b.example", service="http://10.0.0.2:80", order=2)
        CloudflareIngress.objects.create(tunnel=cls.t2, hostname="c.example", service="http://10.0.0.3:80", order=1)

    def test_tunnel_id(self):
        self.assertEqual(
            CloudflareIngressFilterSet({"tunnel_id": [self.t1.pk]}, self.queryset).qs.count(), 2
        )

    def test_search(self):
        self.assertEqual(CloudflareIngressFilterSet({"q": "b.example"}, self.queryset).qs.count(), 1)


class CloudflareRecordFilterSetTest(TestCase):
    queryset = CloudflareRecord.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.z1 = make_zone("z1.example")
        cls.z2 = make_zone("z2.example")
        cls.tunnel = CloudflareTunnel.objects.create(name="t", account="a", tunnel_id="u")
        CloudflareRecord.objects.create(zone=cls.z1, name="www", type=CloudflareRecordTypeChoices.A, content="203.0.113.1")
        CloudflareRecord.objects.create(zone=cls.z1, name="mail", type=CloudflareRecordTypeChoices.MX, content="mx.z1.example")
        CloudflareRecord.objects.create(
            zone=cls.z2, name="dyn", type=CloudflareRecordTypeChoices.A, ddns_enabled=True, ddns_source="wan0"
        )
        CloudflareRecord.objects.create(zone=cls.z2, name="tun", type=CloudflareRecordTypeChoices.CNAME, tunnel=cls.tunnel)

    def test_zone_id(self):
        self.assertEqual(
            CloudflareRecordFilterSet({"zone_id": [self.z1.pk]}, self.queryset).qs.count(), 2
        )

    def test_type(self):
        self.assertEqual(
            CloudflareRecordFilterSet(
                {"type": [CloudflareRecordTypeChoices.A]}, self.queryset
            ).qs.count(),
            2,
        )

    def test_tunnel_id(self):
        self.assertEqual(
            CloudflareRecordFilterSet({"tunnel_id": [self.tunnel.pk]}, self.queryset).qs.count(), 1
        )

    def test_ddns_enabled(self):
        self.assertEqual(
            CloudflareRecordFilterSet({"ddns_enabled": True}, self.queryset).qs.count(), 1
        )


class CloudflareWAFRuleFilterSetTest(TestCase):
    queryset = CloudflareWAFRule.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.z1 = make_zone("w1.example")
        cls.z2 = make_zone("w2.example")
        cls.alias = make_alias("exempt", "198.51.100.0/24")
        CloudflareWAFRule.objects.create(
            zone=cls.z1, phase=CloudflareWAFPhaseChoices.CUSTOM, expression="a", action=CloudflareWAFActionChoices.BLOCK, order=1, ip_alias=cls.alias
        )
        CloudflareWAFRule.objects.create(
            zone=cls.z1, phase=CloudflareWAFPhaseChoices.RATELIMIT, expression="b", action=CloudflareWAFActionChoices.LOG, order=2
        )
        CloudflareWAFRule.objects.create(
            zone=cls.z2, phase=CloudflareWAFPhaseChoices.CUSTOM, expression="c", action=CloudflareWAFActionChoices.BLOCK, order=1
        )

    def test_zone_id(self):
        self.assertEqual(
            CloudflareWAFRuleFilterSet({"zone_id": [self.z1.pk]}, self.queryset).qs.count(), 2
        )

    def test_phase(self):
        self.assertEqual(
            CloudflareWAFRuleFilterSet(
                {"phase": [CloudflareWAFPhaseChoices.RATELIMIT]}, self.queryset
            ).qs.count(),
            1,
        )

    def test_action(self):
        self.assertEqual(
            CloudflareWAFRuleFilterSet(
                {"action": [CloudflareWAFActionChoices.BLOCK]}, self.queryset
            ).qs.count(),
            2,
        )

    def test_ip_alias_id(self):
        self.assertEqual(
            CloudflareWAFRuleFilterSet({"ip_alias_id": [self.alias.pk]}, self.queryset).qs.count(), 1
        )
