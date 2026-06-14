<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# netbox-cloudflare

A NetBox 4.6 plugin that is the native source of truth for **Cloudflare intent** — DNS records
(including DDNS-driven ones), cloudflared tunnels + their ingress rulesets, and WAF security
rules.

It replaces the unstructured `config_context.apps` app-fabric and the global `cloudflare`
config-context that the tofu module `opentofu/net/cloud/cloudflare/` reads today. Each piece of
Cloudflare intent becomes a real, choice-validated, REST/GraphQL-exposed row.

## Models

Four models, all inheriting `NetBoxModel` (custom fields, tags, change logging, GraphQL, REST):

### CloudflareTunnel
The cloudflared daemon's tunnel (minted out-of-band; the `tunnel_id` UUID is written back here).

| Field | Type | Notes |
|-------|------|-------|
| `name` | char(100) unique | Tunnel name |
| `account` | char(100) | Cloudflare account id/slug |
| `tunnel_id` | char(64) blank | cloudflared UUID once created |
| `comment` | char(255) blank | |

### CloudflareIngress
One entry in a tunnel's ordered ingress ruleset; the last (highest `order`) is the
`http_status:404` catch-all.

| Field | Type | Notes |
|-------|------|-------|
| `tunnel` | FK `CloudflareTunnel` (CASCADE) | `related_name=ingress_rules` |
| `hostname` | char(255) blank | FQDN matched (blank for catch-all) |
| `path` | char(255) blank | Optional path match |
| `service` | char(255) | `http://10.0.0.1:80` or `http_status:404` |
| `order` | positive int (100) | Catch-all last |
| `origin_request` | JSON blank | per-rule `originRequest` (e.g. `noTLSVerify`) |

`UniqueConstraint(tunnel, order)`.

### CloudflareRecord
A DNS record; its target is exactly one of static `content`, a `tunnel`, or a DDNS source —
enforced in `clean()`.

| Field | Type | Notes |
|-------|------|-------|
| `zone` | FK `netbox_dns.Zone` (PROTECT) | `related_name=cloudflare_records` |
| `name` | char(255) | subdomain / `@` |
| `type` | choice | A / AAAA / CNAME / TXT / MX / SRV |
| `content` | char(255) blank | static target |
| `proxied` | bool (true) | route through the edge (A/AAAA/CNAME) |
| `ttl` | positive int (1) | 1 = automatic |
| `ddns_enabled` | bool (false) | content updated from a dynamic source |
| `ddns_source` | char(255) blank | dynamic-IP source marker (required when DDNS on) |
| `tunnel` | FK `CloudflareTunnel` (SET_NULL, null) | CNAME to `<tunnel_id>.cfargotunnel.com` |

`UniqueConstraint(zone, name, type, content)`.

### CloudflareWAFRule
A per-zone WAF / rate-limit rule, optionally matching an IP list held in a `netbox_pf` `Alias`
(the same named-list primitive the firewall uses), synced to Cloudflare as an account IP list
referenced by `$<alias name>` in the rule expression.

| Field | Type | Notes |
|-------|------|-------|
| `zone` | FK `netbox_dns.Zone` (CASCADE) | `related_name=waf_rules` |
| `phase` | choice | `http_request_firewall_custom` / `http_ratelimit` / `http_request_firewall_managed` |
| `description` | char(255) blank | |
| `expression` | text | Cloudflare rule expression language |
| `action` | choice | block / challenge / js_challenge / managed_challenge / skip / log / allow |
| `order` | positive int (100) | lower first |
| `enabled` | bool (true) | |
| `ratelimit_threshold` | positive int null | requests before action fires |
| `ratelimit_period` | positive int null | window in seconds |
| `ip_alias` | FK `netbox_pf.Alias` (PROTECT, null) | named IP list; synced as the account list `$<alias name>` references |

`UniqueConstraint(zone, order)`.

## Depends on

`netbox_dns` (PyPI `netbox-plugin-dns`) and `netbox_pf` must both be installed and enabled — they
are declared via `required_plugins`, so NetBox refuses to start this plugin without them.
`CloudflareRecord` and `CloudflareWAFRule` FK `netbox_dns`'s `Zone`; `CloudflareWAFRule.ip_alias`
FKs `netbox_pf`'s `Alias` (the shared firewall named-list primitive).

## Install

```bash
uv pip install --python /opt/netbox/venv/bin/python netbox-cloudflare   # or: pip install -e .
# add "netbox_cloudflare" to PLUGINS in configuration.py (after "netbox_dns" and "netbox_pf")
python manage.py migrate netbox_cloudflare
python manage.py collectstatic --no-input
systemctl restart netbox netbox-rq
```

## Develop / test

Tests run against a **real NetBox test database** (no mocks) via NetBox's Django test framework,
building real `netbox_dns` `Zone` (+ `NameServer`) and `netbox_pf` `Alias` instances. See
`CLAUDE.md`.

```bash
python /opt/netbox/app/netbox/manage.py test netbox_cloudflare --keepdb -v2
```

## License

AGPL-3.0-or-later.
