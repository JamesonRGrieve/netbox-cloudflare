# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cloudflare intent models, replacing the ``config_context.apps`` fabric + the global
``cloudflare`` config-context the tofu module reads:

* ``CloudflareTunnel`` / ``CloudflareIngress`` — the cloudflared daemon's tunnel + its ordered
  ingress ruleset (hostname→service; the ``http_status:404`` catch-all is the last ``order``).
* ``CloudflareRecord`` — a DNS record FK-ing a ``netbox_dns.Zone``; ``clean()`` enforces that
  exactly one of static ``content`` / ``tunnel`` / ``ddns`` drives the record's target.
* ``CloudflareWAFRule`` — a per-zone WAF rule (expression + action), optionally matching an IP
  list held in a ``netbox_pf`` ``Alias`` (the same named-list primitive the firewall uses).

Load balancing — DNS-tier failover, which survives the total loss of an origin site (its edge
router, power, or ISP), unlike any load balancer running *at* that origin:

* ``CloudflareMonitor`` — the health probe. The sensor everything else depends on.
* ``CloudflareLBPool`` / ``CloudflareLBOrigin`` — an account-scoped origin pool and its members,
  addressed by their **public** endpoints (what Cloudflare's edge can reach).
* ``CloudflareLoadBalancer`` — a zone-scoped balanced hostname.
* ``CloudflareLBDefaultPool`` — one position in that hostname's ordered pool list. With
  ``steering_policy = off`` the order *is* the failover priority: order 1 primary, order 2
  standby.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .choices import (
    CloudflareLBSessionAffinityChoices,
    CloudflareLBSteeringChoices,
    CloudflareMonitorMethodChoices,
    CloudflareMonitorTypeChoices,
    CloudflareRecordTypeChoices,
    CloudflareWAFActionChoices,
    CloudflareWAFPhaseChoices,
)


class CloudflareTunnel(NetBoxModel):
    """A cloudflared tunnel. Minted out-of-band (Ansible); ``tunnel_id`` is the non-secret
    cloudflared UUID written back here once the tunnel exists."""

    name = models.CharField(max_length=100, unique=True)
    account = models.CharField(
        max_length=100, help_text="Cloudflare account id/slug that owns this tunnel."
    )
    tunnel_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="The cloudflared UUID, once the tunnel is created. Records CNAME to "
        "<tunnel_id>.cfargotunnel.com.",
    )
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Cloudflare Tunnel"
        constraints = [
            models.UniqueConstraint(fields=["name"], name="netbox_cloudflare_tunnel_name")
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflaretunnel", args=[self.pk])


class CloudflareIngress(NetBoxModel):
    """One entry in a tunnel's ordered cloudflared ingress ruleset (hostname→service). The
    last entry (highest ``order``) is the mandatory ``http_status:404`` catch-all."""

    tunnel = models.ForeignKey(
        CloudflareTunnel,
        on_delete=models.CASCADE,
        related_name="ingress_rules",
        help_text="The tunnel this ingress rule belongs to.",
    )
    hostname = models.CharField(
        max_length=255,
        blank=True,
        help_text="FQDN this rule matches (blank for the catch-all entry).",
    )
    path = models.CharField(
        max_length=255, blank=True, help_text="Optional path match (cloudflared path regex)."
    )
    service = models.CharField(
        max_length=255,
        help_text="Origin service, e.g. http://192.168.7.234:80 or http_status:404.",
    )
    order = models.PositiveIntegerField(
        default=100, help_text="Evaluation order; the catch-all is last (highest order)."
    )
    origin_request = models.JSONField(
        blank=True,
        null=True,
        help_text="Per-rule originRequest overrides (e.g. {\"noTLSVerify\": true}).",
    )

    class Meta:
        ordering = ["tunnel", "order"]
        verbose_name = "Cloudflare Ingress Rule"
        constraints = [
            models.UniqueConstraint(
                fields=["tunnel", "order"], name="netbox_cloudflare_ingress_tunnel_order"
            )
        ]

    def __str__(self):
        target = self.hostname or "(catch-all)"
        return f"{self.tunnel}: {target} → {self.service}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflareingress", args=[self.pk])


class CloudflareRecord(NetBoxModel):
    """A Cloudflare DNS record. Its target is exactly one of: static ``content``, a ``tunnel``
    (CNAME to ``<tunnel_id>.cfargotunnel.com``), or a dynamic ``ddns`` source whose live value
    the apply side reads at runtime — enforced in ``clean()``."""

    zone = models.ForeignKey(
        "netbox_dns.Zone",
        on_delete=models.PROTECT,
        related_name="cloudflare_records",
        help_text="The DNS zone (netbox_dns) this record lives in.",
    )
    name = models.CharField(max_length=255, help_text="Record name / subdomain, or @ for apex.")
    type = models.CharField(max_length=16, choices=CloudflareRecordTypeChoices)
    content = models.CharField(
        max_length=255, blank=True, help_text="Static target value (when not tunnel/DDNS driven)."
    )
    proxied = models.BooleanField(
        default=True, help_text="Route through the Cloudflare edge (A/AAAA/CNAME only)."
    )
    ttl = models.PositiveIntegerField(
        default=1, help_text="TTL in seconds; 1 means automatic (required when proxied)."
    )
    ddns_enabled = models.BooleanField(
        default=False, help_text="Content is updated from a dynamic source after creation."
    )
    ddns_source = models.CharField(
        max_length=255,
        blank=True,
        help_text="Dynamic-IP source marker (e.g. the interface/device the live WAN IP is read "
        "from).",
    )
    tunnel = models.ForeignKey(
        CloudflareTunnel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="records",
        help_text="When set, this record is a CNAME to <tunnel_id>.cfargotunnel.com.",
    )

    class Meta:
        ordering = ["zone", "name", "type"]
        verbose_name = "Cloudflare Record"
        constraints = [
            models.UniqueConstraint(
                fields=["zone", "name", "type", "content"],
                name="netbox_cloudflare_record_zone_name_type_content",
            )
        ]

    def __str__(self):
        return f"{self.name} [{self.type}] @ {self.zone}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflarerecord", args=[self.pk])

    def get_type_color(self):
        return CloudflareRecordTypeChoices.colors.get(self.type)

    def clean(self):
        super().clean()
        # Exactly one of static content / tunnel / ddns drives the record target.
        drivers = [
            ("content", bool(self.content)),
            ("tunnel", self.tunnel_id is not None),
            ("ddns", self.ddns_enabled),
        ]
        active = [name for name, on in drivers if on]
        if len(active) != 1:
            raise ValidationError(
                "Exactly one target driver must be set: static content, a tunnel, or DDNS "
                f"(got: {', '.join(active) or 'none'})."
            )
        if self.ddns_enabled and not self.ddns_source:
            raise ValidationError({"ddns_source": "A DDNS source is required when DDNS is enabled."})


class CloudflareWAFRule(NetBoxModel):
    """A Cloudflare WAF / rate-limit rule applied to one or many zones: an expression + action
    deployed into a ruleset ``phase``, optionally matching an IP list held in a ``netbox_pf``
    ``Alias``. One canonical rule definition can be shared across every zone in an account (or
    across accounts); per-zone enable/disable is handled via the ``CloudflareWAFRuleZone``
    through-table."""

    zones = models.ManyToManyField(
        "netbox_dns.Zone",
        through="CloudflareWAFRuleZone",
        related_name="waf_rules",
        blank=True,
        help_text="Zones (netbox_dns) this rule applies to.",
    )
    phase = models.CharField(
        max_length=40,
        choices=CloudflareWAFPhaseChoices,
        default=CloudflareWAFPhaseChoices.CUSTOM,
    )
    description = models.CharField(max_length=255, blank=True)
    expression = models.TextField(help_text="Cloudflare rule expression language.")
    action = models.CharField(max_length=20, choices=CloudflareWAFActionChoices)
    order = models.PositiveIntegerField(
        default=100, help_text="Evaluation order within the zone's ruleset; lower first."
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Default enabled state; overridden per-zone via the zone assignment.",
    )
    ratelimit_threshold = models.PositiveIntegerField(
        null=True, blank=True, help_text="Requests before the rate-limit action fires."
    )
    ratelimit_period = models.PositiveIntegerField(
        null=True, blank=True, help_text="Rate-limit counting window, in seconds."
    )
    ip_alias = models.ForeignKey(
        "netbox_pf.Alias",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cloudflare_waf_rules",
        help_text="Named pf alias (IPs/networks) this rule matches — synced to Cloudflare as an "
        "account IP list referenced by $<alias name> in the rule expression.",
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Cloudflare WAF Rule"

    def __str__(self):
        zone_count = self.zones.count()
        return f"{self.description or self.action} [{self.phase}] ({zone_count} zones)"

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflarewafrule", args=[self.pk])

    def get_phase_color(self):
        return CloudflareWAFPhaseChoices.colors.get(self.phase)

    def get_action_color(self):
        return CloudflareWAFActionChoices.colors.get(self.action)


class CloudflareWAFRuleZone(NetBoxModel):
    """Through-table linking a WAF rule to a zone, with a per-zone enabled override.

    ``enabled`` defaults to ``None`` (inherit from the rule); ``True``/``False`` overrides the
    rule's default for this specific zone (e.g. obsessedmediagroup.ca carries the Bot Fight
    rule but with enabled=false)."""

    rule = models.ForeignKey(
        CloudflareWAFRule,
        on_delete=models.CASCADE,
        related_name="zone_assignments",
    )
    zone = models.ForeignKey(
        "netbox_dns.Zone",
        on_delete=models.CASCADE,
        related_name="waf_rule_assignments",
    )
    enabled = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        help_text="Override the rule's default enabled state for this zone. "
        "Null = inherit from the rule.",
    )

    class Meta:
        ordering = ["rule", "zone"]
        verbose_name = "WAF Rule Zone Assignment"
        constraints = [
            models.UniqueConstraint(
                fields=["rule", "zone"],
                name="netbox_cloudflare_waf_rule_zone_unique",
            )
        ]

    def __str__(self):
        state = "inherit" if self.enabled is None else ("enabled" if self.enabled else "disabled")
        return f"{self.rule.description} @ {self.zone} ({state})"

    def get_absolute_url(self):
        return self.rule.get_absolute_url()

    @property
    def effective_enabled(self):
        return self.rule.enabled if self.enabled is None else self.enabled


class CloudflareMonitor(NetBoxModel):
    """An account-scoped load-balancer health monitor: the probe Cloudflare's edge runs against
    every origin in every pool that references it.

    This is the sensor the whole DNS-tier failover hangs off — an origin is only withdrawn from
    service when this probe fails it, so ``retries``/``interval``/``timeout`` set how long a dead
    site keeps being served. The probe must hit the **real user-visible surface** (the client's
    own hostname over HTTPS, via ``probe_zone`` + a Host ``header``), not a loopback or an IP,
    or it will report healthy while the site is down."""

    name = models.CharField(max_length=100, unique=True)
    account = models.CharField(
        max_length=100, help_text="Cloudflare account id/slug that owns this monitor."
    )
    type = models.CharField(
        max_length=16,
        choices=CloudflareMonitorTypeChoices,
        default=CloudflareMonitorTypeChoices.HTTPS,
    )
    method = models.CharField(
        max_length=8,
        choices=CloudflareMonitorMethodChoices,
        default=CloudflareMonitorMethodChoices.GET,
        blank=True,
        help_text="HTTP method (http/https monitors only).",
    )
    path = models.CharField(
        max_length=255,
        blank=True,
        help_text="Probe path, e.g. / or /health (http/https monitors only).",
    )
    port = models.PositiveIntegerField(
        null=True, blank=True, help_text="Probe port; defaults to the protocol's port."
    )
    expected_codes = models.CharField(
        max_length=32,
        blank=True,
        help_text="Status codes considered healthy, e.g. 200 or 2xx.",
    )
    expected_body = models.CharField(
        max_length=255,
        blank=True,
        help_text="Substring the response body must contain to be considered healthy. A status "
        "code alone does not prove the site rendered.",
    )
    header = models.JSONField(
        null=True,
        blank=True,
        help_text='Probe request headers, e.g. {"Host": ["tolleytire.com"]}.',
    )
    probe_zone = models.CharField(
        max_length=255,
        blank=True,
        help_text="Zone the probe resolves the origin against (sends SNI + Host for this name).",
    )
    interval = models.PositiveIntegerField(
        default=60, help_text="Seconds between probes."
    )
    timeout = models.PositiveIntegerField(default=5, help_text="Probe timeout, in seconds.")
    retries = models.PositiveIntegerField(
        default=2, help_text="Retries before an origin is marked unhealthy."
    )
    consecutive_up = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Successful probes before a recovered origin is returned to service.",
    )
    consecutive_down = models.PositiveIntegerField(
        null=True, blank=True, help_text="Failed probes before an origin is withdrawn."
    )
    follow_redirects = models.BooleanField(default=False)
    allow_insecure = models.BooleanField(
        default=False, help_text="Accept an invalid TLS certificate from the origin."
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Cloudflare Monitor"
        constraints = [
            models.UniqueConstraint(fields=["name"], name="netbox_cloudflare_monitor_name")
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflaremonitor", args=[self.pk])

    def get_type_color(self):
        return CloudflareMonitorTypeChoices.colors.get(self.type)

    def clean(self):
        super().clean()
        if self.type in (
            CloudflareMonitorTypeChoices.HTTP,
            CloudflareMonitorTypeChoices.HTTPS,
        ):
            if not self.path:
                raise ValidationError({"path": "Required for an http/https monitor."})
            if not self.expected_codes:
                raise ValidationError(
                    {"expected_codes": "Required for an http/https monitor."}
                )
        if self.timeout >= self.interval:
            raise ValidationError(
                {"timeout": "Timeout must be shorter than the probe interval."}
            )


class CloudflareLBPool(NetBoxModel):
    """An account-scoped load-balancer origin pool. A pool is healthy while at least
    ``minimum_origins`` of its origins pass the ``monitor``; an unhealthy pool is skipped by every
    load balancer that lists it."""

    name = models.CharField(max_length=100, unique=True)
    account = models.CharField(
        max_length=100, help_text="Cloudflare account id/slug that owns this pool."
    )
    monitor = models.ForeignKey(
        CloudflareMonitor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pools",
        help_text="Health monitor probing this pool's origins. Without one, origins are never "
        "health-checked and the pool can never fail over.",
    )
    enabled = models.BooleanField(default=True)
    minimum_origins = models.PositiveIntegerField(
        default=1, help_text="Healthy origins required for the pool itself to be healthy."
    )
    notification_email = models.CharField(
        max_length=255, blank=True, help_text="Address notified when the pool's health changes."
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Cloudflare LB Pool"
        constraints = [
            models.UniqueConstraint(fields=["name"], name="netbox_cloudflare_lb_pool_name")
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflarelbpool", args=[self.pk])


class CloudflareLBOrigin(NetBoxModel):
    """One origin server inside a pool — the public address traffic is sent to when this pool
    serves.

    ``address`` is a public endpoint reachable from Cloudflare's edge, so an origin behind a
    NAT/port-forward is modeled by its **public** address, not the internal one. ``header``
    carries the Host header the edge sends, which is what lets one public IP fronting many client
    hostnames route correctly."""

    pool = models.ForeignKey(
        CloudflareLBPool,
        on_delete=models.CASCADE,
        related_name="origins",
        help_text="The pool this origin belongs to.",
    )
    name = models.CharField(max_length=100, help_text="Origin name within the pool.")
    address = models.CharField(
        max_length=255, help_text="Public IP or hostname Cloudflare's edge connects to."
    )
    enabled = models.BooleanField(default=True)
    weight = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=1,
        help_text="Relative share of traffic within the pool (0–1).",
    )
    header = models.JSONField(
        null=True,
        blank=True,
        help_text='Host header the edge sends, e.g. {"Host": ["tolleytire.com"]}.',
    )

    class Meta:
        ordering = ["pool", "name"]
        verbose_name = "Cloudflare LB Origin"
        constraints = [
            models.UniqueConstraint(
                fields=["pool", "name"], name="netbox_cloudflare_lb_origin_pool_name"
            )
        ]

    def __str__(self):
        return f"{self.pool}: {self.name} ({self.address})"

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflarelborigin", args=[self.pk])


class CloudflareLoadBalancer(NetBoxModel):
    """A zone-scoped load balancer: one hostname whose traffic is steered across pools.

    With ``steering_policy = off`` (the default here) the ordered ``default_pools`` are tried in
    order and the first healthy one serves — which is exactly DNS-tier failover: pool 1 is the
    primary site, pool 2 the standby. ``fallback_pool`` serves only when every default pool is
    unhealthy, so it is the last line before an outage, not part of the rotation.

    This tier fails over independently of any load balancer running *at* an origin, which is why
    it survives the loss of an origin site's edge router entirely."""

    zone = models.ForeignKey(
        "netbox_dns.Zone",
        on_delete=models.PROTECT,
        related_name="load_balancers",
        help_text="The DNS zone (netbox_dns) the balanced hostname lives in.",
    )
    name = models.CharField(
        max_length=255, help_text="The balanced FQDN, e.g. tolleytire.com or www.tolleytire.com."
    )
    default_pools = models.ManyToManyField(
        CloudflareLBPool,
        through="CloudflareLBDefaultPool",
        related_name="load_balancers",
        help_text="Ordered pools; with steering off, the first healthy one serves.",
    )
    fallback_pool = models.ForeignKey(
        CloudflareLBPool,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="fallback_for",
        help_text="Serves only when every default pool is unhealthy.",
    )
    steering_policy = models.CharField(
        max_length=32,
        choices=CloudflareLBSteeringChoices,
        default=CloudflareLBSteeringChoices.OFF,
    )
    session_affinity = models.CharField(
        max_length=16,
        choices=CloudflareLBSessionAffinityChoices,
        default=CloudflareLBSessionAffinityChoices.NONE,
    )
    proxied = models.BooleanField(
        default=True,
        help_text="Route through the Cloudflare edge. A load balancer only health-checks and "
        "fails over when proxied; a DNS-only record is served as-is.",
    )
    enabled = models.BooleanField(default=True)
    ttl = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="TTL in seconds. Only valid when not proxied (a proxied LB is always automatic).",
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["zone", "name"]
        verbose_name = "Cloudflare Load Balancer"
        constraints = [
            models.UniqueConstraint(
                fields=["zone", "name"], name="netbox_cloudflare_lb_zone_name"
            )
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflareloadbalancer", args=[self.pk])

    def get_steering_policy_color(self):
        return CloudflareLBSteeringChoices.colors.get(self.steering_policy)

    def clean(self):
        super().clean()
        if self.proxied and self.ttl:
            raise ValidationError(
                {"ttl": "A proxied load balancer's TTL is always automatic; leave it unset."}
            )
        if not self.proxied:
            raise ValidationError(
                {
                    "proxied": "A DNS-only load balancer is never health-checked, so it cannot "
                    "fail over. Proxy it or do not model it as a load balancer."
                }
            )


class CloudflareLBDefaultPool(NetBoxModel):
    """One position in a load balancer's ordered default-pool list.

    The order **is** the failover priority under ``steering_policy = off``: order 1 is the
    primary, order 2 the standby. Modeled as a through-row rather than a bare M2M because a
    Django M2M has no stable ordering, and an unordered failover list is not a failover list."""

    load_balancer = models.ForeignKey(
        CloudflareLoadBalancer,
        on_delete=models.CASCADE,
        related_name="pool_assignments",
    )
    pool = models.ForeignKey(
        CloudflareLBPool, on_delete=models.PROTECT, related_name="pool_assignments"
    )
    order = models.PositiveIntegerField(
        default=100, help_text="Failover priority; lower is preferred."
    )

    class Meta:
        ordering = ["load_balancer", "order"]
        verbose_name = "Cloudflare LB Default Pool"
        constraints = [
            models.UniqueConstraint(
                fields=["load_balancer", "order"], name="netbox_cloudflare_lb_default_pool_order"
            ),
            models.UniqueConstraint(
                fields=["load_balancer", "pool"], name="netbox_cloudflare_lb_default_pool_unique"
            ),
        ]

    def __str__(self):
        return f"{self.load_balancer}[{self.order}]: {self.pool}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflarelbdefaultpool", args=[self.pk])
