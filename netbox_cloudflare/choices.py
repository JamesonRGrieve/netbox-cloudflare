# SPDX-License-Identifier: AGPL-3.0-or-later
"""Choice sets for the Cloudflare intent models. Values match exactly what the
``cloudflare/cloudflare`` terraform provider applies (record ``type``, ruleset ``phase``,
rule ``action``) so the tofu module reads them back verbatim."""

from utilities.choices import ChoiceSet


class CloudflareRecordTypeChoices(ChoiceSet):
    """DNS record type. Cloudflare proxies only A/AAAA/CNAME; the rest are DNS-only."""

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    TXT = "TXT"
    MX = "MX"
    SRV = "SRV"
    CHOICES = [
        (A, "A", "blue"),
        (AAAA, "AAAA", "indigo"),
        (CNAME, "CNAME", "cyan"),
        (TXT, "TXT", "gray"),
        (MX, "MX", "orange"),
        (SRV, "SRV", "purple"),
    ]


class CloudflareWAFPhaseChoices(ChoiceSet):
    """Cloudflare ruleset phase the rule deploys into."""

    CUSTOM = "http_request_firewall_custom"
    RATELIMIT = "http_ratelimit"
    MANAGED = "http_request_firewall_managed"
    CHOICES = [
        (CUSTOM, "Custom firewall (http_request_firewall_custom)", "blue"),
        (RATELIMIT, "Rate limit (http_ratelimit)", "orange"),
        (MANAGED, "Managed firewall (http_request_firewall_managed)", "purple"),
    ]


class CloudflareWAFActionChoices(ChoiceSet):
    """Action a matched WAF rule takes."""

    BLOCK = "block"
    CHALLENGE = "challenge"
    JS_CHALLENGE = "js_challenge"
    MANAGED_CHALLENGE = "managed_challenge"
    SKIP = "skip"
    LOG = "log"
    ALLOW = "allow"
    CHOICES = [
        (BLOCK, "Block", "red"),
        (CHALLENGE, "Challenge", "orange"),
        (JS_CHALLENGE, "JS challenge", "yellow"),
        (MANAGED_CHALLENGE, "Managed challenge", "cyan"),
        (SKIP, "Skip", "gray"),
        (LOG, "Log", "blue"),
        (ALLOW, "Allow", "green"),
    ]
