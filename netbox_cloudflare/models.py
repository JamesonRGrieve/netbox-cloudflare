# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cloudflare intent models. Four ``NetBoxModel`` rows replace the ``config_context.apps``
fabric + the global ``cloudflare`` config-context the tofu module reads:

* ``CloudflareTunnel`` / ``CloudflareIngress`` — the cloudflared daemon's tunnel + its ordered
  ingress ruleset (hostname→service; the ``http_status:404`` catch-all is the last ``order``).
* ``CloudflareRecord`` — a DNS record FK-ing a ``netbox_dns.Zone``; ``clean()`` enforces that
  exactly one of static ``content`` / ``tunnel`` / ``ddns`` drives the record's target.
* ``CloudflareWAFRule`` — a per-zone WAF rule (expression + action), optionally matching an IP
  list sourced from core ``ipam.Prefix`` rows.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .choices import (
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
    """A per-zone Cloudflare WAF / rate-limit rule: an expression + action deployed into a
    ruleset ``phase``, optionally matching an IP list sourced from core ``ipam.Prefix`` rows."""

    zone = models.ForeignKey(
        "netbox_dns.Zone",
        on_delete=models.CASCADE,
        related_name="waf_rules",
        help_text="The zone (netbox_dns) this rule applies to.",
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
    enabled = models.BooleanField(default=True)
    ratelimit_threshold = models.PositiveIntegerField(
        null=True, blank=True, help_text="Requests before the rate-limit action fires."
    )
    ratelimit_period = models.PositiveIntegerField(
        null=True, blank=True, help_text="Rate-limit counting window, in seconds."
    )
    ip_prefixes = models.ManyToManyField(
        "ipam.Prefix",
        blank=True,
        related_name="cloudflare_waf_rules",
        help_text="IP-list match source for this rule.",
    )

    class Meta:
        ordering = ["zone", "order"]
        verbose_name = "Cloudflare WAF Rule"
        constraints = [
            models.UniqueConstraint(
                fields=["zone", "order"], name="netbox_cloudflare_waf_rule_zone_order"
            )
        ]

    def __str__(self):
        return f"{self.zone} [{self.phase}] {self.action} (order {self.order})"

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloudflare:cloudflarewafrule", args=[self.pk])

    def get_phase_color(self):
        return CloudflareWAFPhaseChoices.colors.get(self.phase)

    def get_action_color(self):
        return CloudflareWAFActionChoices.colors.get(self.action)
