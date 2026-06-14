# netbox-cloudflare — Agent Operating Guide

Adapted from `../netbox-load-balancing-acl`'s `CLAUDE.md` (same engineering + test discipline),
re-targeted from load-balancer routing ACLs to **Cloudflare intent**.

`netbox-cloudflare` is an **AGPL-3.0** NetBox 4.6 Django plugin that is the native source of truth
for Cloudflare intent: **DNS records (incl. DDNS), cloudflared tunnels + ingress rulesets, and WAF
security rules**. It replaces the unstructured `config_context.apps` app-fabric and the global
`cloudflare` config-context that the tofu module `opentofu/net/cloud/cloudflare/` reads today,
turning each piece of Cloudflare intent into a real, choice-validated, REST/GraphQL-exposed row.

It **depends on `netbox_dns`** (declared via `required_plugins`); `CloudflareRecord` and
`CloudflareWAFRule` FK that plugin's `Zone`. The WAF IP-list match source is **core** `ipam.Prefix`
(no extra plugin dependency for it).

---

## Key Directives / Rules

### DO, ALWAYS:
- If functionality won't work without a parameter, make it a **required positional** parameter —
  never an optional one with an inline presence check.
- Any time you modify a source file, ensure its accompanying test under `netbox_cloudflare/tests/`
  contains **comprehensive tests for the change WITHOUT MOCKS**, so `manage.py test
  netbox_cloudflare` discovers them, and update any `.md` in the same directory that references the
  changed code.
- Write concise code (avoid obvious comments; use one-liners where possible).
- Critically analyze requirements and ask all necessary clarifying questions before implementing
  or refactoring.
- Phrase documentation for yourself (AI) and for autistic/ADHD humans: a clear architectural
  summary you could reconstruct the code from with 95% accuracy, with minimal snippets — **not**
  usage examples (the browsable REST/GraphQL schema is the usage reference).

### DO NOT, EVER, UNDER ANY CIRCUMSTANCE:
- Make assumptions, or answer with "is likely", "probably", or "might be".
- Use frame-local or thread-local state instead of passing data via parameters.
- Skip a failing test instead of fixing the root cause.
- Fix broken functionality while keeping the broken path as a fallback.
- Re-implement existing functionality in a second location to bypass the original.
- Use bandaid fixes instead of fixing the core functionality.
- **Mock the database, the ORM, the NetBox API test client, or any integration path.** Tests run
  against a **real test database** via NetBox's Django test framework — use real model instances
  (including real `netbox_dns` `Zone`/`NameServer` and core `ipam` `Prefix`) and real API
  requests. Only pure utility functions may use mocks for isolation.

### Python / Django Guidelines:
- Import children of `datetime`: `from datetime import date` — **never** `import datetime` then
  `datetime.date`.
- Imports are package-relative inside `netbox_cloudflare` (`from .models import CloudflareRecord`),
  never `from netbox_cloudflare.models import ...`. Imports of upstream plugins/core use their real
  package paths (`from netbox_dns.models import Zone`, `from ipam.models import Prefix`).
- Models inherit `netbox.models.NetBoxModel` (custom fields, tags, journaling, change logging,
  GraphQL — for free).
- **SPDX header on every source file**: `# SPDX-License-Identifier: AGPL-3.0-or-later`.

### Documentation Guidelines:
- Markdown docs are concise: reconstruct-the-code-with-95%-accuracy architectural summaries with
  minimal snippets, not usage tutorials.

---

## Architecture (NetBox 4.6 plugin)

| File | Responsibility |
|------|----------------|
| `__init__.py` | `PluginConfig` — name `netbox_cloudflare`, `base_url='cloudflare'`, `required_plugins=["netbox_dns"]`, min/max NetBox version |
| `choices.py` | `CloudflareRecordTypeChoices` (A/AAAA/CNAME/TXT/MX/SRV), `CloudflareWAFPhaseChoices`, `CloudflareWAFActionChoices` — values match the `cloudflare/cloudflare` provider |
| `models.py` | The four models (see §Models) |
| `migrations/` | hand-authored (NetBox disables `makemigrations` in prod); verify with `makemigrations --check --dry-run` on an ephemeral NetBox |
| `api/serializers.py`, `api/views.py`, `api/urls.py` | REST API (`NetBoxModelViewSet`) — endpoints `tunnels`, `ingress-rules`, `records`, `waf-rules` under `/api/plugins/cloudflare/` |
| `filtersets.py` | `NetBoxModelFilterSet`: explicit `zone_id` / `tunnel_id` / `prefix_id` FK filters + `type`/`phase`/`action`/`proxied`/`ddns_enabled` choice/bool filters |
| `tables.py`, `forms.py`, `navigation.py`, `views.py`, `urls.py` | UI layer |
| `graphql/` | GraphQL types (none shipped yet — `NetBoxModel` still exposes auto GraphQL) |

### Models — the Cloudflare-intent SoT
- **CloudflareTunnel** (`NetBoxModel`): `name` (unique), `account`, `tunnel_id` (blank), `comment`.
  The cloudflared daemon's tunnel.
- **CloudflareIngress**: FK `CloudflareTunnel` (CASCADE, `ingress_rules`), `hostname` (blank for
  catch-all), `path` (blank), `service`, `order`, `origin_request` (JSON). `UniqueConstraint(tunnel,
  order)`. The ordered cloudflared ingress list; last entry is the `http_status:404` catch-all.
- **CloudflareRecord**: FK `netbox_dns.Zone` (PROTECT, `cloudflare_records`), `name`, `type`,
  `content` (blank), `proxied`, `ttl`, `ddns_enabled`, `ddns_source` (blank), `tunnel`
  (SET_NULL, null). `clean()` enforces **exactly one** of static `content` / `tunnel` / `ddns`
  drives the target, and that DDNS records carry a `ddns_source`. `UniqueConstraint(zone, name,
  type, content)`.
- **CloudflareWAFRule**: FK `netbox_dns.Zone` (CASCADE, `waf_rules`), `phase`, `description`,
  `expression` (text), `action`, `order`, `enabled`, `ratelimit_threshold`/`ratelimit_period`
  (null), M2M `ipam.Prefix` (`ip_prefixes`, the IP-list match source). `UniqueConstraint(zone,
  order)`.

`zone` is PROTECT on records (a referenced zone can't be deleted out from under a record) and
CASCADE on WAF rules (drop the zone, its rules go); `tunnel` CASCADEs ingress and SET_NULLs records.
The migration depends on netbox_dns's **latest** migration
(`0030_dnsseckeytemplate_comments_dnsseckeytemplate_owner_and_more`) plus `extras 0001_initial` and
`ipam 0001_initial` (the M2M target), so every referenced table exists before the CreateModels run.

### How this maps back to the tofu cloudflare module
The tofu module (`opentofu/net/cloud/cloudflare/`) consumes this plugin's REST API instead of the
old config-context reads:
- **DNS** — `CloudflareRecord` rows feed `cloudflare_record`. A row with `tunnel` set becomes the
  proxied CNAME to `<tunnel_id>.cfargotunnel.com` (was the `apps.<x>.tunnel` branch in `netbox.tf`).
  A row with `ddns_enabled` becomes a `cloudflare_record` in the `dns_ddns` pool whose `content` is
  `ignore_changes`d (the DDNS updater owns it; `ddns_source` tells the updater where the live WAN IP
  is) — replacing `app_fabric.ddns`. A static-`content` row is a plain managed record.
- **Tunnels/ingress** — `CloudflareTunnel` + ordered `CloudflareIngress` rows feed
  `cloudflare_zero_trust_tunnel_cloudflared_config` (hostname→service ingress list with the
  `http_status:404` catch-all last) — replacing the `_tunnel_ingress` derivation in `tunnels.tf`.
- **WAF** — `CloudflareWAFRule` rows feed `cloudflare_ruleset` (per-zone, per-`phase`) with
  `expression`/`action`/`enabled`; `ratelimit_*` drive `http_ratelimit` rules; `ip_prefixes` source
  the account-level `cloudflare_list` an expression references — replacing the
  `security.custom_rules` / `exemption_ips` config-context keys in `cloudflare.tf`.

---

## Testing (NO MOCKS — real DB, NetBox test framework)

- Tests live in `netbox_cloudflare/tests/` (inside the package, so `manage.py test
  netbox_cloudflare` discovers them and they ship with the plugin), one module per source module
  (`test_models.py`, `test_api.py`, `test_filtersets.py`) plus `factories.py`.
- Build real upstream objects via `factories.make_zone()` / `make_prefix()`: a `Zone` needs a
  `NameServer` for its `soa_mname` and an `soa_rname` — its `view`, TTL and numeric SOA fields
  auto-fill from netbox_dns plugin defaults in `Zone.clean_fields` (run by `Zone.save()`). A
  `Prefix` needs only its CIDR.
- Use NetBox's base classes from `utilities.testing`: `APIViewTestCases.APIViewTestCase` (composed
  CRUD mixins).
- **Test isolation**: Django wraps each test in a transaction against a per-run test database with
  automatic teardown.
- **Never skip a failing test** — fix the root cause; repair deficiencies starting with the
  lowest-hanging fruit.
- **Run**: `python /opt/netbox/app/netbox/manage.py test netbox_cloudflare --keepdb -v2`
  (or `pytest` with `pytest-django` + `DJANGO_SETTINGS_MODULE=netbox.settings`).
- **Coverage bar**: every model, serializer, filterset, and view has tests — including each
  uniqueness constraint, the `CloudflareRecord.clean()` one-driver rule, the `ip_prefixes` M2M, and
  the FK delete behaviors (zone PROTECT on records, zone CASCADE on WAF rules, tunnel CASCADE on
  ingress, tunnel SET_NULL on records).

---

## Licensing
- **AGPL-3.0-or-later** (workspace production-IaC standard). SPDX header in every file.
