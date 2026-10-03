# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model tests against a real DB (no mocks): creation, str/url/color, uniqueness constraints,
the CloudflareRecord.clean() one-driver rule, the ip_alias FK to netbox_pf.Alias, and the FK
delete behaviors (zone PROTECT on records, zone/rule CASCADE on WAF-rule zone assignments,
tunnel CASCADE on ingress, tunnel SET_NULL on records, ip_alias PROTECT on WAF rules). Real netbox_dns Zone + netbox_pf Alias
instances back everything.

The load-balancing tests additionally pin the failover semantics: a monitor's http/https probe
requires a path + expected codes, a proxied LB refuses an explicit TTL, a DNS-only LB is rejected
outright (it is never health-checked, so it cannot fail over), and the ordered default-pool list
is unique per (lb, order) and per (lb, pool) — the order IS the failover priority."""

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
    CloudflareLBDefaultPool,
    CloudflareLBOrigin,
    CloudflareLoadBalancer,
    CloudflareMonitor,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
    CloudflareWAFRuleZone,
    CloudflareZoneSettings,
)

from .factories import make_alias, make_monitor, make_pool, make_waf_rule, make_zone


class CloudflareZoneSettingsModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zone = make_zone("settings.example")

    def test_create_str_url_defaults_bot_fight_on(self):
        s = CloudflareZoneSettings.objects.create(zone=self.zone)
        self.assertTrue(s.bot_fight_mode)
        self.assertEqual(str(s), "settings.example settings")
        self.assertIn("/plugins/cloudflare/zone-settings/", s.get_absolute_url())
        self.assertEqual(self.zone.cloudflare_settings, s)

    def test_one_row_per_zone(self):
        CloudflareZoneSettings.objects.create(zone=self.zone)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareZoneSettings.objects.create(zone=self.zone, bot_fight_mode=False)

    def test_zone_delete_cascades(self):
        zone = make_zone("gone.example")
        CloudflareZoneSettings.objects.create(zone=zone, bot_fight_mode=False)
        zone.delete()
        self.assertFalse(CloudflareZoneSettings.objects.filter(zone__name="gone.example").exists())


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

    def test_clean_unmanaged_no_driver_ok(self):
        # An unmanaged record documents an externally-owned value (Stalwart automatic DNS);
        # the tofu apply skips it, so the one-driver rule does not apply and no driver is fine.
        r = CloudflareRecord(
            zone=self.zone, name="_acme-challenge", type=CloudflareRecordTypeChoices.TXT,
            unmanaged=True,
        )
        r.clean()  # no exception
        r.full_clean()  # field-level validation also passes with a blank content

    def test_clean_unmanaged_still_requires_ddns_source(self):
        # Unmanaged waives the driver rule but not the ddns_source coupling.
        r = CloudflareRecord(
            zone=self.zone, name="dyn", type=CloudflareRecordTypeChoices.A,
            unmanaged=True, ddns_enabled=True,
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
        rule = make_waf_rule(
            [self.zone],
            phase=CloudflareWAFPhaseChoices.CUSTOM,
            expression='(ip.src in $exempt)',
            action=CloudflareWAFActionChoices.BLOCK,
            order=1,
            description="exempt-block",
        )
        self.assertEqual(str(rule), "exempt-block [http_request_firewall_custom] (1 zones)")
        self.assertIn("/plugins/cloudflare/waf-rules/", rule.get_absolute_url())
        self.assertEqual(rule.get_action_color(), "red")
        self.assertEqual(rule.get_phase_color(), "blue")
        self.assertTrue(rule.enabled)
        self.assertEqual(list(rule.zones.all()), [self.zone])

    def test_one_rule_shared_across_zones(self):
        other = make_zone("waf-other.example")
        rule = make_waf_rule(
            [self.zone, other], expression="s", action=CloudflareWAFActionChoices.LOG, order=2
        )
        self.assertEqual(rule.zones.count(), 2)
        self.assertIn(rule, other.waf_rules.all())

    def test_unique_rule_zone_assignment(self):
        rule = make_waf_rule(
            [self.zone], expression="x", action=CloudflareWAFActionChoices.LOG, order=5
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareWAFRuleZone.objects.create(rule=rule, zone=self.zone)

    def test_effective_enabled_inherits_then_overrides(self):
        rule = make_waf_rule(
            [self.zone], expression="e", action=CloudflareWAFActionChoices.BLOCK, order=6
        )
        assignment = rule.zone_assignments.get()
        self.assertIsNone(assignment.enabled)
        self.assertTrue(assignment.effective_enabled)
        assignment.enabled = False
        assignment.save()
        self.assertFalse(assignment.effective_enabled)
        rule.enabled = False
        rule.save()
        assignment.enabled = True
        assignment.save()
        self.assertTrue(CloudflareWAFRuleZone.objects.get(pk=assignment.pk).effective_enabled)

    def test_set_zone_assignments_reconciles(self):
        z2, z3 = make_zone("waf-set2.example"), make_zone("waf-set3.example")
        rule = make_waf_rule(
            [self.zone, z2], expression="set", action=CloudflareWAFActionChoices.LOG, order=8
        )
        kept_pk = rule.zone_assignments.get(zone=z2).pk
        rule.set_zone_assignments({z2: False, z3: None})
        self.assertEqual(
            {za.zone_id: za.enabled for za in rule.zone_assignments.all()},
            {z2.pk: False, z3.pk: None},
        )
        # The surviving assignment is updated in place, not recreated.
        self.assertEqual(rule.zone_assignments.get(zone=z2).pk, kept_pk)
        rule.set_zone_assignments({})
        self.assertFalse(rule.zone_assignments.exists())

    def test_zone_delete_cascades_assignment_not_rule(self):
        zone = make_zone("cascade.example")
        rule = make_waf_rule(
            [zone], expression="z", action=CloudflareWAFActionChoices.BLOCK, order=1
        )
        zone.delete()
        self.assertTrue(CloudflareWAFRule.objects.filter(pk=rule.pk).exists())
        self.assertFalse(CloudflareWAFRuleZone.objects.filter(rule=rule).exists())

    def test_rule_delete_cascades_assignments(self):
        rule = make_waf_rule(
            [self.zone], expression="d", action=CloudflareWAFActionChoices.BLOCK, order=7
        )
        pk = rule.pk
        rule.delete()
        self.assertFalse(CloudflareWAFRuleZone.objects.filter(rule_id=pk).exists())

    def test_ip_alias_fk(self):
        alias = make_alias("exempt", "198.51.100.0/24\n203.0.113.0/24")
        rule = make_waf_rule(
            [self.zone],
            expression="m",
            action=CloudflareWAFActionChoices.SKIP,
            order=10,
            ip_alias=alias,
        )
        self.assertEqual(rule.ip_alias, alias)
        self.assertIn(rule, alias.cloudflare_waf_rules.all())

    def test_ip_alias_protect_on_delete(self):
        alias = make_alias("protected-alias", "198.51.100.0/24")
        make_waf_rule(
            [self.zone],
            expression="p",
            action=CloudflareWAFActionChoices.BLOCK,
            order=11,
            ip_alias=alias,
        )
        with self.assertRaises(ProtectedError), transaction.atomic():
            alias.delete()


class CloudflareMonitorModelTest(TestCase):
    def test_https_monitor_requires_path_and_codes(self):
        m = CloudflareMonitor(name="m1", account="omg", type="https")
        with self.assertRaises(ValidationError):
            m.clean()

    def test_tcp_monitor_needs_neither(self):
        m = CloudflareMonitor(name="m-tcp", account="omg", type="tcp")
        m.clean()  # must not raise
        m.save()
        self.assertEqual(str(m), "m-tcp")
        self.assertIn("/plugins/cloudflare/monitors/", m.get_absolute_url())

    def test_timeout_must_be_under_interval(self):
        m = CloudflareMonitor(
            name="m2", account="omg", type="https", path="/", expected_codes="200",
            interval=5, timeout=5,
        )
        with self.assertRaises(ValidationError):
            m.clean()

    def test_defaults_and_color(self):
        m = make_monitor("m3")
        self.assertEqual(m.interval, 60)
        self.assertEqual(m.retries, 2)
        self.assertFalse(m.allow_insecure)
        self.assertEqual(m.get_type_color(), "green")  # https

    def test_unique_name(self):
        make_monitor("dup")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_monitor("dup")


class CloudflareLBPoolModelTest(TestCase):
    def test_pool_protects_its_monitor(self):
        monitor = make_monitor("m-protect")
        make_pool("p-protect", monitor=monitor)
        with self.assertRaises(ProtectedError), transaction.atomic():
            monitor.delete()

    def test_origins_cascade_from_pool(self):
        pool = make_pool("p-cascade")
        origin = CloudflareLBOrigin.objects.create(
            pool=pool, name="omg-wan", address="203.0.113.100"
        )
        pk = origin.pk
        self.assertIn("203.0.113.100", str(origin))
        pool.delete()
        self.assertFalse(CloudflareLBOrigin.objects.filter(pk=pk).exists())

    def test_origin_name_unique_per_pool(self):
        pool = make_pool("p-uniq")
        CloudflareLBOrigin.objects.create(pool=pool, name="wan", address="203.0.113.1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareLBOrigin.objects.create(pool=pool, name="wan", address="203.0.113.2")

    def test_same_origin_name_in_another_pool_allowed(self):
        CloudflareLBOrigin.objects.create(
            pool=make_pool("p-a"), name="wan", address="203.0.113.1"
        )
        o = CloudflareLBOrigin.objects.create(
            pool=make_pool("p-b"), name="wan", address="198.18.0.1"
        )
        self.assertEqual(o.name, "wan")


class CloudflareLoadBalancerModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zone = make_zone("tolleytire.com")
        cls.monitor = make_monitor("wp-https-lb")
        cls.omg = make_pool("omg-origin-lb", monitor=cls.monitor)
        cls.house = make_pool("house-origin-lb", monitor=cls.monitor)

    def _lb(self, **kwargs):
        return CloudflareLoadBalancer.objects.create(
            zone=self.zone, name="tolleytire.com", **kwargs
        )

    def test_defaults_to_ordered_failover(self):
        lb = self._lb()
        lb.full_clean()
        self.assertEqual(lb.steering_policy, "off")
        self.assertTrue(lb.proxied)
        self.assertEqual(lb.get_steering_policy_color(), "green")
        self.assertIn("/plugins/cloudflare/load-balancers/", lb.get_absolute_url())

    def test_proxied_lb_rejects_explicit_ttl(self):
        lb = CloudflareLoadBalancer(zone=self.zone, name="x.tolleytire.com", proxied=True, ttl=300)
        with self.assertRaises(ValidationError):
            lb.clean()

    def test_dns_only_lb_is_rejected(self):
        # A DNS-only LB is never health-checked, so it cannot fail over.
        lb = CloudflareLoadBalancer(zone=self.zone, name="y.tolleytire.com", proxied=False)
        with self.assertRaises(ValidationError):
            lb.clean()

    def test_ordered_default_pools_are_the_failover_priority(self):
        lb = self._lb()
        CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.omg, order=1)
        CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.house, order=2)
        self.assertEqual(
            [a.pool.name for a in lb.pool_assignments.all()],
            ["omg-origin-lb", "house-origin-lb"],
        )

    def test_one_pool_per_order(self):
        lb = self._lb()
        CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.omg, order=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.house, order=1)

    def test_pool_cannot_be_listed_twice(self):
        lb = self._lb()
        CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.omg, order=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.omg, order=2)

    def test_assignments_cascade_from_lb(self):
        lb = self._lb()
        a = CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.omg, order=1)
        pk = a.pk
        lb.delete()
        self.assertFalse(CloudflareLBDefaultPool.objects.filter(pk=pk).exists())

    def test_listed_pool_is_protected(self):
        lb = self._lb()
        CloudflareLBDefaultPool.objects.create(load_balancer=lb, pool=self.omg, order=1)
        with self.assertRaises(ProtectedError), transaction.atomic():
            self.omg.delete()

    def test_fallback_pool_is_protected(self):
        lb = self._lb(fallback_pool=self.house)
        self.assertEqual(lb.fallback_pool, self.house)
        with self.assertRaises(ProtectedError), transaction.atomic():
            self.house.delete()
