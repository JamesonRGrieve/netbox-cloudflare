# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests against a real DB + real API client (no mocks).

Composes the explicit CRUD mixins (not the GraphQL-inclusive APIViewTestCase) since the plugin
ships no GraphQL type yet. Records carry exactly one target driver so CloudflareRecord.clean()
passes on create; one WAF rule references a netbox_pf.Alias via ip_alias; ingress rules use
distinct orders so the (tunnel, order) constraint never trips inside the create batch."""

from decimal import Decimal

from utilities.testing import APIViewTestCases

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
    CloudflareZoneSettings,
)

from .factories import make_alias, make_monitor, make_pool, make_waf_rule, make_zone


class _Namespace:
    view_namespace = "plugins-api:netbox_cloudflare"


# A tuple of bases, not a TestCase subclass: the test loader would otherwise collect the shared
# base itself and run every CRUD test against model=None.
_CRUD = (
    _Namespace,
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
)


class CloudflareTunnelAPITest(*_CRUD):
    model = CloudflareTunnel
    brief_fields = ["account", "display", "id", "name", "tunnel_id", "url"]
    bulk_update_data = {"account": "bulk-acct"}

    @classmethod
    def setUpTestData(cls):
        CloudflareTunnel.objects.bulk_create(
            [
                CloudflareTunnel(name="ex0", account="a", tunnel_id="u0"),
                CloudflareTunnel(name="ex1", account="a", tunnel_id="u1"),
                CloudflareTunnel(name="ex2", account="a", tunnel_id="u2"),
            ]
        )
        cls.create_data = [
            {"name": "house", "account": "acct-1", "tunnel_id": "uuid-1"},
            {"name": "omg", "account": "acct-1", "tunnel_id": "uuid-2"},
            {"name": "shop", "account": "acct-2"},
        ]


class CloudflareIngressAPITest(*_CRUD):
    model = CloudflareIngress
    brief_fields = ["display", "hostname", "id", "order", "service", "tunnel", "url"]
    bulk_update_data = {"path": "/v2"}

    @classmethod
    def setUpTestData(cls):
        tunnel = CloudflareTunnel.objects.create(name="t", account="a", tunnel_id="u")
        CloudflareIngress.objects.bulk_create(
            [
                CloudflareIngress(tunnel=tunnel, hostname="a.example", service="http://10.0.0.1:80", order=1),
                CloudflareIngress(tunnel=tunnel, hostname="b.example", service="http://10.0.0.2:80", order=2),
                CloudflareIngress(tunnel=tunnel, service="http_status:404", order=3),
            ]
        )
        cls.create_data = [
            {"tunnel": tunnel.pk, "hostname": "c.example", "service": "http://10.0.0.3:80", "order": 10},
            {"tunnel": tunnel.pk, "hostname": "d.example", "service": "http://10.0.0.4:80", "order": 20},
            {"tunnel": tunnel.pk, "service": "http_status:404", "order": 30},
        ]


class CloudflareRecordAPITest(*_CRUD):
    model = CloudflareRecord
    brief_fields = ["display", "id", "name", "type", "url", "zone"]
    bulk_update_data = {"proxied": False}

    @classmethod
    def setUpTestData(cls):
        zone = make_zone("api.example")
        tunnel = CloudflareTunnel.objects.create(name="t", account="a", tunnel_id="u")
        CloudflareRecord.objects.bulk_create(
            [
                CloudflareRecord(zone=zone, name="ex0", type="A", content="203.0.113.1"),
                CloudflareRecord(zone=zone, name="ex1", type="A", content="203.0.113.2"),
                CloudflareRecord(zone=zone, name="ex2", type="A", content="203.0.113.3"),
            ]
        )
        cls.create_data = [
            {"zone": zone.pk, "name": "static", "type": "A", "content": "203.0.113.10"},
            {"zone": zone.pk, "name": "tun", "type": "CNAME", "tunnel": tunnel.pk},
            {
                "zone": zone.pk,
                "name": "dyn",
                "type": "A",
                "ddns_enabled": True,
                "ddns_source": "wan0",
            },
        ]


class CloudflareWAFRuleAPITest(*_CRUD):
    model = CloudflareWAFRule
    brief_fields = ["action", "description", "display", "id", "order", "phase", "url"]
    bulk_update_data = {"enabled": False}

    @classmethod
    def setUpTestData(cls):
        cls.zone = make_zone("waf-api.example")
        cls.zone2 = make_zone("waf-api2.example")
        cls.alias = make_alias("exempt", "198.51.100.0/24")
        for expression, action, order in (("a", "block", 1), ("b", "log", 2), ("c", "challenge", 3)):
            make_waf_rule([cls.zone], expression=expression, action=action, order=order)
        cls.create_data = [
            {
                "phase": "http_request_firewall_custom",
                "expression": "(ip.src in $exempt)",
                "action": "block",
                "order": 10,
                "ip_alias": cls.alias.pk,
            },
            {
                "phase": "http_ratelimit",
                "expression": "(http.request.uri.path eq \"/login\")",
                "action": "managed_challenge",
                "order": 20,
                "ratelimit_threshold": 10,
                "ratelimit_period": 60,
            },
            {
                "phase": "http_request_firewall_managed",
                "expression": "(cf.bot_management.score lt 30)",
                "action": "js_challenge",
                "order": 30,
            },
        ]

    def test_create_writes_zone_assignments(self):
        self.add_permissions("netbox_cloudflare.add_cloudflarewafrule")
        payload = {
            "expression": "(ip.src in $exempt)",
            "action": "block",
            "order": 40,
            "zone_assignments": [
                {"zone": self.zone.pk, "enabled": None},
                {"zone": self.zone2.pk, "enabled": False},
            ],
        }
        response = self.client.post(self._get_list_url(), payload, format="json", **self.header)
        self.assertHttpStatus(response, 201)
        rule = CloudflareWAFRule.objects.get(pk=response.data["id"])
        self.assertEqual(
            {za.zone_id: za.enabled for za in rule.zone_assignments.all()},
            {self.zone.pk: None, self.zone2.pk: False},
        )

    def test_update_reconciles_zone_assignments(self):
        self.add_permissions("netbox_cloudflare.change_cloudflarewafrule")
        rule = make_waf_rule([self.zone], expression="r", action="log", order=50)
        payload = {"zone_assignments": [{"zone": self.zone2.pk, "enabled": True}]}
        response = self.client.patch(
            self._get_detail_url(rule), payload, format="json", **self.header
        )
        self.assertHttpStatus(response, 200)
        self.assertEqual(
            {za.zone_id: za.enabled for za in rule.zone_assignments.all()},
            {self.zone2.pk: True},
        )


class CloudflareZoneSettingsAPITest(*_CRUD):
    model = CloudflareZoneSettings
    brief_fields = ["bot_fight_mode", "display", "id", "ssl_mode", "url", "zone"]
    bulk_update_data = {"bot_fight_mode": False, "ssl_mode": "full"}

    @classmethod
    def setUpTestData(cls):
        CloudflareZoneSettings.objects.bulk_create(
            [CloudflareZoneSettings(zone=make_zone(f"zs-ex{i}.example")) for i in range(3)]
        )
        cls.create_data = [
            {"zone": make_zone("zs-new0.example").pk},
            {"zone": make_zone("zs-new1.example").pk, "bot_fight_mode": False, "ssl_mode": "strict"},
            {"zone": make_zone("zs-new2.example").pk, "bot_fight_mode": True, "ssl_mode": "full"},
        ]


class CloudflareMonitorAPITest(*_CRUD):
    model = CloudflareMonitor
    brief_fields = ["display", "id", "name", "type", "url"]
    bulk_update_data = {"retries": 3}

    @classmethod
    def setUpTestData(cls):
        for i in range(3):
            make_monitor(f"ex-mon{i}")
        cls.create_data = [
            {
                "name": "wp-https", "account": "omg", "type": "https", "method": "GET",
                "path": "/", "expected_codes": "200", "expected_body": "<html",
                "probe_zone": "tolleytire.com", "interval": 60, "timeout": 5, "retries": 2,
            },
            {
                "name": "wp-https-strict", "account": "omg", "type": "https", "path": "/",
                "expected_codes": "2xx", "consecutive_down": 3, "consecutive_up": 2,
            },
            {"name": "mail-tcp", "account": "omg", "type": "tcp", "port": 25},
        ]


class CloudflareLBPoolAPITest(*_CRUD):
    model = CloudflareLBPool
    brief_fields = ["display", "enabled", "id", "name", "url"]
    bulk_update_data = {"enabled": False}

    @classmethod
    def setUpTestData(cls):
        monitor = make_monitor("pool-api-mon")
        for i in range(3):
            make_pool(f"ex-pool{i}", monitor=monitor)
        cls.create_data = [
            {"name": "omg-origin", "account": "omg", "monitor": monitor.pk},
            {"name": "house-origin", "account": "omg", "monitor": monitor.pk, "minimum_origins": 1},
            {"name": "no-monitor", "account": "omg"},
        ]


class CloudflareLBOriginAPITest(*_CRUD):
    model = CloudflareLBOrigin
    brief_fields = ["address", "display", "id", "name", "pool", "url"]
    bulk_update_data = {"enabled": False}

    @classmethod
    def setUpTestData(cls):
        pool = make_pool("origin-api-pool")
        CloudflareLBOrigin.objects.bulk_create(
            [
                CloudflareLBOrigin(pool=pool, name=f"ex{i}", address=f"203.0.113.{i + 1}")
                for i in range(3)
            ]
        )
        cls.create_data = [
            {
                "pool": pool.pk, "name": "omg-wan", "address": "203.0.113.100",
                "header": {"Host": ["tolleytire.com"]},
            },
            {
                "pool": pool.pk, "name": "house-wan", "address": "198.18.0.100",
                "weight": Decimal("0.500"),
            },
            {"pool": pool.pk, "name": "disabled", "address": "198.18.0.101", "enabled": False},
        ]


class CloudflareLoadBalancerAPITest(*_CRUD):
    model = CloudflareLoadBalancer
    brief_fields = ["display", "enabled", "id", "name", "url", "zone"]
    bulk_update_data = {"session_affinity": "cookie"}

    @classmethod
    def setUpTestData(cls):
        zone = make_zone("tolleytire.com")
        pool = make_pool("lb-api-pool")
        CloudflareLoadBalancer.objects.bulk_create(
            [
                CloudflareLoadBalancer(zone=zone, name=f"ex{i}.tolleytire.com")
                for i in range(3)
            ]
        )
        cls.create_data = [
            {"zone": zone.pk, "name": "tolleytire.com", "fallback_pool": pool.pk},
            {"zone": zone.pk, "name": "www.tolleytire.com", "steering_policy": "off"},
            {"zone": zone.pk, "name": "shop.tolleytire.com", "session_affinity": "cookie"},
        ]


class CloudflareLBDefaultPoolAPITest(*_CRUD):
    model = CloudflareLBDefaultPool
    brief_fields = ["display", "id", "load_balancer", "order", "pool", "url"]
    bulk_update_data = {"order": 50}

    @classmethod
    def setUpTestData(cls):
        zone = make_zone("dp.example")
        # One existing row per load balancer: the bulk update sets every row to the same order,
        # which (lb, order) uniqueness only allows when no two rows share a load balancer.
        existing = [make_pool(f"dp-ex{i}") for i in range(3)]
        existing_lbs = [
            CloudflareLoadBalancer.objects.create(zone=zone, name=f"ex{i}.dp.example")
            for i in range(3)
        ]
        CloudflareLBDefaultPool.objects.bulk_create(
            [
                CloudflareLBDefaultPool(load_balancer=existing_lbs[i], pool=p, order=1)
                for i, p in enumerate(existing)
            ]
        )
        # Each row needs a distinct (lb, order) AND a distinct (lb, pool), so give the created
        # rows their own load balancers.
        fresh = [make_pool(f"dp-new{i}") for i in range(3)]
        lbs = [
            CloudflareLoadBalancer.objects.create(zone=zone, name=f"new{i}.dp.example")
            for i in range(3)
        ]
        cls.create_data = [
            {"load_balancer": lbs[i].pk, "pool": fresh[i].pk, "order": i + 1} for i in range(3)
        ]
