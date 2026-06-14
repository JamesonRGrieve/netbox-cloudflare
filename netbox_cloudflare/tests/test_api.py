# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests against a real DB + real API client (no mocks).

Composes the explicit CRUD mixins (not the GraphQL-inclusive APIViewTestCase) since the plugin
ships no GraphQL type yet. Records carry exactly one target driver so CloudflareRecord.clean()
passes on create; one WAF rule references a netbox_pf.Alias via ip_alias; ingress rules use
distinct orders so the (tunnel, order) constraint never trips inside the create batch."""

from utilities.testing import APIViewTestCases

from netbox_cloudflare.models import (
    CloudflareIngress,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
)

from .factories import make_alias, make_zone


class _CRUD(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    pass


class CloudflareTunnelAPITest(_CRUD):
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


class CloudflareIngressAPITest(_CRUD):
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


class CloudflareRecordAPITest(_CRUD):
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


class CloudflareWAFRuleAPITest(_CRUD):
    model = CloudflareWAFRule
    brief_fields = ["action", "display", "id", "order", "phase", "url", "zone"]
    bulk_update_data = {"enabled": False}

    @classmethod
    def setUpTestData(cls):
        zone = make_zone("waf-api.example")
        cls.alias = make_alias("exempt", "198.51.100.0/24")
        CloudflareWAFRule.objects.bulk_create(
            [
                CloudflareWAFRule(zone=zone, expression="a", action="block", order=1),
                CloudflareWAFRule(zone=zone, expression="b", action="log", order=2),
                CloudflareWAFRule(zone=zone, expression="c", action="challenge", order=3),
            ]
        )
        cls.create_data = [
            {
                "zone": zone.pk,
                "phase": "http_request_firewall_custom",
                "expression": "(ip.src in $exempt)",
                "action": "block",
                "order": 10,
                "ip_alias": cls.alias.pk,
            },
            {
                "zone": zone.pk,
                "phase": "http_ratelimit",
                "expression": "(http.request.uri.path eq \"/login\")",
                "action": "managed_challenge",
                "order": 20,
                "ratelimit_threshold": 10,
                "ratelimit_period": 60,
            },
            {
                "zone": zone.pk,
                "phase": "http_request_firewall_managed",
                "expression": "(cf.bot_management.score lt 30)",
                "action": "js_challenge",
                "order": 30,
            },
        ]
