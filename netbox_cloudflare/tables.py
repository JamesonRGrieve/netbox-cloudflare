# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import (
    CloudflareIngress,
    CloudflareLBDefaultPool,
    CloudflareLBOrigin,
    CloudflareLBPool,
    CloudflareLoadBalancer,
    CloudflareMonitor,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
)


class CloudflareTunnelTable(NetBoxTable):
    name = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflaretunnel_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareTunnel
        fields = (
            "pk",
            "id",
            "name",
            "account",
            "tunnel_id",
            "comment",
            "tags",
            "created",
            "last_updated",
        )
        default_columns = ("name", "account", "tunnel_id", "comment")


class CloudflareIngressTable(NetBoxTable):
    tunnel = tables.Column(linkify=True)
    hostname = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflareingress_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareIngress
        fields = (
            "pk",
            "id",
            "tunnel",
            "hostname",
            "path",
            "service",
            "order",
            "origin_request",
            "tags",
            "created",
            "last_updated",
        )
        default_columns = ("tunnel", "hostname", "path", "service", "order")


class CloudflareRecordTable(NetBoxTable):
    zone = tables.Column(linkify=True)
    name = tables.Column(linkify=True)
    type = columns.ChoiceFieldColumn()
    tunnel = tables.Column(linkify=True)
    proxied = columns.BooleanColumn()
    ddns_enabled = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflarerecord_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareRecord
        fields = (
            "pk",
            "id",
            "zone",
            "name",
            "type",
            "content",
            "proxied",
            "ttl",
            "ddns_enabled",
            "ddns_source",
            "tunnel",
            "tags",
            "created",
            "last_updated",
        )
        default_columns = (
            "zone",
            "name",
            "type",
            "content",
            "proxied",
            "ddns_enabled",
            "tunnel",
        )


class CloudflareWAFRuleTable(NetBoxTable):
    zone = tables.Column(linkify=True)
    phase = columns.ChoiceFieldColumn()
    action = columns.ChoiceFieldColumn()
    enabled = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflarewafrule_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareWAFRule
        fields = (
            "pk",
            "id",
            "zone",
            "phase",
            "description",
            "expression",
            "action",
            "order",
            "enabled",
            "ratelimit_threshold",
            "ratelimit_period",
            "tags",
            "created",
            "last_updated",
        )
        default_columns = ("zone", "phase", "description", "action", "order", "enabled")


class CloudflareMonitorTable(NetBoxTable):
    name = tables.Column(linkify=True)
    type = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflaremonitor_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareMonitor
        fields = (
            "pk", "id", "name", "account", "type", "method", "path", "port",
            "expected_codes", "expected_body", "probe_zone", "interval", "timeout",
            "retries", "consecutive_up", "consecutive_down", "follow_redirects",
            "allow_insecure", "description", "tags", "created", "last_updated",
        )
        default_columns = ("name", "type", "path", "expected_codes", "interval", "retries")


class CloudflareLBPoolTable(NetBoxTable):
    name = tables.Column(linkify=True)
    monitor = tables.Column(linkify=True)
    enabled = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflarelbpool_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareLBPool
        fields = (
            "pk", "id", "name", "account", "monitor", "enabled", "minimum_origins",
            "notification_email", "description", "tags", "created", "last_updated",
        )
        default_columns = ("name", "monitor", "enabled", "minimum_origins", "description")


class CloudflareLBOriginTable(NetBoxTable):
    pool = tables.Column(linkify=True)
    name = tables.Column(linkify=True)
    enabled = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflarelborigin_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareLBOrigin
        fields = (
            "pk", "id", "pool", "name", "address", "enabled", "weight", "tags",
            "created", "last_updated",
        )
        default_columns = ("pool", "name", "address", "enabled", "weight")


class CloudflareLoadBalancerTable(NetBoxTable):
    name = tables.Column(linkify=True)
    zone = tables.Column(linkify=True)
    fallback_pool = tables.Column(linkify=True)
    steering_policy = columns.ChoiceFieldColumn()
    proxied = columns.BooleanColumn()
    enabled = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflareloadbalancer_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareLoadBalancer
        fields = (
            "pk", "id", "zone", "name", "fallback_pool", "steering_policy",
            "session_affinity", "proxied", "enabled", "ttl", "description", "tags",
            "created", "last_updated",
        )
        default_columns = ("name", "zone", "steering_policy", "fallback_pool", "proxied", "enabled")


class CloudflareLBDefaultPoolTable(NetBoxTable):
    load_balancer = tables.Column(linkify=True)
    pool = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="plugins:netbox_cloudflare:cloudflarelbdefaultpool_list")

    class Meta(NetBoxTable.Meta):
        model = CloudflareLBDefaultPool
        fields = ("pk", "id", "load_balancer", "pool", "order", "tags", "created", "last_updated")
        default_columns = ("load_balancer", "order", "pool")
