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


class CloudflareMonitorTypeChoices(ChoiceSet):
    """Probe protocol a load-balancer health monitor speaks."""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP_ICMP = "udp_icmp"
    ICMP_PING = "icmp_ping"
    SMTP = "smtp"
    CHOICES = [
        (HTTPS, "HTTPS", "green"),
        (HTTP, "HTTP", "blue"),
        (TCP, "TCP", "cyan"),
        (UDP_ICMP, "UDP-ICMP", "gray"),
        (ICMP_PING, "ICMP ping", "gray"),
        (SMTP, "SMTP", "orange"),
    ]


class CloudflareMonitorMethodChoices(ChoiceSet):
    """HTTP method an http/https monitor probes with."""

    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    CHOICES = [(GET, "GET", "blue"), (HEAD, "HEAD", "gray"), (POST, "POST", "orange")]


class CloudflareLBSteeringChoices(ChoiceSet):
    """How a load balancer selects among its default pools.

    ``off`` is the failover policy: pools are tried in their configured order and the first
    healthy one serves. Everything else distributes traffic, which is not what an
    active-passive origin pair wants."""

    OFF = "off"
    GEO = "geo"
    RANDOM = "random"
    DYNAMIC_LATENCY = "dynamic_latency"
    PROXIMITY = "proximity"
    LEAST_OUTSTANDING_REQUESTS = "least_outstanding_requests"
    CHOICES = [
        (OFF, "Off (ordered failover)", "green"),
        (GEO, "Geo", "blue"),
        (RANDOM, "Random", "gray"),
        (DYNAMIC_LATENCY, "Dynamic latency", "cyan"),
        (PROXIMITY, "Proximity", "indigo"),
        (LEAST_OUTSTANDING_REQUESTS, "Least outstanding requests", "purple"),
    ]


class CloudflareLBSessionAffinityChoices(ChoiceSet):
    """Session affinity (stickiness) mode."""

    NONE = "none"
    COOKIE = "cookie"
    IP_COOKIE = "ip_cookie"
    HEADER = "header"
    CHOICES = [
        (NONE, "None", "gray"),
        (COOKIE, "Cookie", "blue"),
        (IP_COOKIE, "IP + cookie", "cyan"),
        (HEADER, "Header", "purple"),
    ]
