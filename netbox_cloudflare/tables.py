# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import (
    CloudflareIngress,
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
