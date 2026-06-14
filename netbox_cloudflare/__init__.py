# SPDX-License-Identifier: AGPL-3.0-or-later
"""netbox-cloudflare: the native NetBox source of truth for **Cloudflare intent** —
DNS records (incl. DDNS-driven ones), cloudflared tunnels + their ingress rulesets, and
WAF security rules.

Replaces the unstructured ``config_context.apps`` app-fabric + the global ``cloudflare``
config-context that the tofu module ``opentofu/net/cloud/cloudflare/`` reads today. Each piece
of Cloudflare intent becomes a real, choice-validated, REST/GraphQL-exposed row:

* ``CloudflareTunnel`` / ``CloudflareIngress`` — the cloudflared daemon's tunnel + its ordered
  hostname→service ingress list (the catch-all ``http_status:404`` is the last entry).
* ``CloudflareRecord`` — a DNS record FK-ing a ``netbox_dns.Zone``; its target is exactly one of
  a static ``content``, a ``tunnel`` (CNAME to ``<tunnel_id>.cfargotunnel.com``), or a dynamic
  ``ddns_source`` (content owned by a DDNS updater after creation).
* ``CloudflareWAFRule`` — a per-zone WAF/ratelimit rule (expression + action), optionally
  matching against an IP list held in a ``netbox_pf`` ``Alias`` (the same named-list primitive
  the firewall uses), synced to Cloudflare as an account IP list referenced by ``$<alias name>``.

DNS zones come from the ``netbox_dns`` plugin and the WAF IP-list ``Alias`` from ``netbox_pf``
(both declared via ``required_plugins``).
"""

from netbox.plugins import PluginConfig

__version__ = "0.0.1"


class NetBoxCloudflareConfig(PluginConfig):
    name = "netbox_cloudflare"
    verbose_name = "NetBox Cloudflare"
    description = (
        "Native SoT for Cloudflare intent: DNS (incl. DDNS), cloudflared tunnels/ingress, WAF rules"
    )
    version = __version__
    author = "Jameson"
    base_url = "cloudflare"
    min_version = "4.6.0"
    max_version = "4.6.99"
    required_plugins = ["netbox_dns", "netbox_pf"]


config = NetBoxCloudflareConfig
