# SPDX-License-Identifier: AGPL-3.0-or-later
from ipam.api.serializers import PrefixSerializer
from netbox.api.serializers import NetBoxModelSerializer
from netbox_dns.api.serializers import ZoneSerializer
from rest_framework import serializers

from ..models import (
    CloudflareIngress,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
)


class CloudflareTunnelSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflaretunnel-detail"
    )

    class Meta:
        model = CloudflareTunnel
        fields = [
            "id",
            "url",
            "display",
            "name",
            "account",
            "tunnel_id",
            "comment",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "account", "tunnel_id"]


class CloudflareIngressSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflareingress-detail"
    )
    tunnel = CloudflareTunnelSerializer(nested=True)

    class Meta:
        model = CloudflareIngress
        fields = [
            "id",
            "url",
            "display",
            "tunnel",
            "hostname",
            "path",
            "service",
            "order",
            "origin_request",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "tunnel", "hostname", "service", "order"]


class CloudflareRecordSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflarerecord-detail"
    )
    zone = ZoneSerializer(nested=True)
    tunnel = CloudflareTunnelSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = CloudflareRecord
        fields = [
            "id",
            "url",
            "display",
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
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "zone", "name", "type"]


class CloudflareWAFRuleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflarewafrule-detail"
    )
    zone = ZoneSerializer(nested=True)
    ip_prefixes = PrefixSerializer(nested=True, many=True, required=False)

    class Meta:
        model = CloudflareWAFRule
        fields = [
            "id",
            "url",
            "display",
            "zone",
            "phase",
            "description",
            "expression",
            "action",
            "order",
            "enabled",
            "ratelimit_threshold",
            "ratelimit_period",
            "ip_prefixes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "zone", "phase", "action", "order"]
