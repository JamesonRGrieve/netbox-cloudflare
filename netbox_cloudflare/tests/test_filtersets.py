# SPDX-License-Identifier: AGPL-3.0-or-later
"""FilterSet tests against a real DB (no mocks): explicit FK `_id` scoping + choice/bool filters
across every model. Real netbox_dns Zone + netbox_pf Alias instances back the FKs.

The load-balancer `pool_id` filter is the one worth pinning: default pools are reached through
the ordered through-model, not a direct FK, so the test asserts a fallback-only pool does NOT
match it."""

from django.test import TestCase

from netbox_cloudflare.choices import (
    CloudflareRecordTypeChoices,
    CloudflareWAFActionChoices,
    CloudflareWAFPhaseChoices,
)
from netbox_cloudflare.filtersets import (
    CloudflareIngressFilterSet,
    CloudflareLBDefaultPoolFilterSet,
    CloudflareLBOriginFilterSet,
    CloudflareLBPoolFilterSet,
    CloudflareLoadBalancerFilterSet,
    CloudflareMonitorFilterSet,
    CloudflareRecordFilterSet,
    CloudflareTunnelFilterSet,
    CloudflareWAFRuleFilterSet,
)
from netbox_cloudflare.models import (
    CloudflareIngress,
    CloudflareLBDefaultPool,
    CloudflareLBOrigin,
    CloudflareLBPool,
    CloudflareLoadBalancer,
    CloudflareMonitor,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
)

from .factories import make_alias, make_monitor, make_pool, make_zone


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


class CloudflareLoadBalancingFilterSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zone = make_zone("tolleytire.com")
        cls.other_zone = make_zone("parkerplumbing.ca")
        cls.https = make_monitor("wp-https-f")
        cls.tcp = make_monitor("mail-tcp-f", type="tcp", path="", expected_codes="")

        cls.omg = make_pool("omg-origin-f", monitor=cls.https)
        cls.house = make_pool("house-origin-f", monitor=cls.https)
        cls.orphan = make_pool("orphan-f", enabled=False)

        CloudflareLBOrigin.objects.create(pool=cls.omg, name="omg-wan", address="203.0.113.100")
        CloudflareLBOrigin.objects.create(pool=cls.house, name="house-wan", address="198.18.0.100")

        cls.lb = CloudflareLoadBalancer.objects.create(zone=cls.zone, name="tolleytire.com")
        cls.other_lb = CloudflareLoadBalancer.objects.create(
            zone=cls.other_zone, name="parkerplumbing.ca", fallback_pool=cls.orphan
        )
        CloudflareLBDefaultPool.objects.create(load_balancer=cls.lb, pool=cls.omg, order=1)
        CloudflareLBDefaultPool.objects.create(load_balancer=cls.lb, pool=cls.house, order=2)

    def test_monitor_type(self):
        self.assertEqual(
            CloudflareMonitorFilterSet(
                {"type": ["tcp"]}, CloudflareMonitor.objects.all()
            ).qs.count(),
            1,
        )

    def test_pool_by_monitor(self):
        self.assertEqual(
            CloudflareLBPoolFilterSet(
                {"monitor_id": [self.https.pk]}, CloudflareLBPool.objects.all()
            ).qs.count(),
            2,
        )

    def test_pool_enabled(self):
        self.assertEqual(
            CloudflareLBPoolFilterSet(
                {"enabled": False}, CloudflareLBPool.objects.all()
            ).qs.count(),
            1,
        )

    def test_origin_by_pool(self):
        self.assertEqual(
            CloudflareLBOriginFilterSet(
                {"pool_id": [self.omg.pk]}, CloudflareLBOrigin.objects.all()
            ).qs.count(),
            1,
        )

    def test_lb_by_zone(self):
        self.assertEqual(
            CloudflareLoadBalancerFilterSet(
                {"zone_id": [self.zone.pk]}, CloudflareLoadBalancer.objects.all()
            ).qs.count(),
            1,
        )

    def test_lb_by_default_pool_traverses_the_through_model(self):
        self.assertEqual(
            CloudflareLoadBalancerFilterSet(
                {"pool_id": [self.house.pk]}, CloudflareLoadBalancer.objects.all()
            ).qs.count(),
            1,
        )
        # The fallback pool is NOT a default pool, so it must not match.
        self.assertEqual(
            CloudflareLoadBalancerFilterSet(
                {"pool_id": [self.orphan.pk]}, CloudflareLoadBalancer.objects.all()
            ).qs.count(),
            0,
        )

    def test_lb_by_fallback_pool(self):
        self.assertEqual(
            CloudflareLoadBalancerFilterSet(
                {"fallback_pool_id": [self.orphan.pk]}, CloudflareLoadBalancer.objects.all()
            ).qs.count(),
            1,
        )

    def test_default_pool_by_lb(self):
        self.assertEqual(
            CloudflareLBDefaultPoolFilterSet(
                {"load_balancer_id": [self.lb.pk]}, CloudflareLBDefaultPool.objects.all()
            ).qs.count(),
            2,
        )

    def test_search_lb_by_zone_name(self):
        self.assertEqual(
            CloudflareLoadBalancerFilterSet(
                {"q": "parkerplumbing"}, CloudflareLoadBalancer.objects.all()
            ).qs.count(),
            1,
        )
