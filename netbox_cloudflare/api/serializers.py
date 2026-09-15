# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.serializers import NetBoxModelSerializer
from netbox_dns.api.serializers import ZoneSerializer
from netbox_pf.api.serializers import AliasSerializer
from rest_framework import serializers

from ..models import (
    CloudflareIngress,
    CloudflareLBDefaultPool,
    CloudflareLBOrigin,
    CloudflareLBPool,
    CloudflareLoadBalancer,
    CloudflareMonitor,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
    CloudflareWAFRuleZone,
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
            "unmanaged",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "zone", "name", "type"]


class CloudflareWAFRuleZoneSerializer(NetBoxModelSerializer):
    zone = ZoneSerializer(nested=True)

    class Meta:
        model = CloudflareWAFRuleZone
        fields = ["id", "zone", "enabled"]


class CloudflareWAFRuleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflarewafrule-detail"
    )
    zones = ZoneSerializer(nested=True, many=True, read_only=True)
    zone_assignments = CloudflareWAFRuleZoneSerializer(many=True, read_only=True)
    ip_alias = AliasSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = CloudflareWAFRule
        fields = [
            "id",
            "url",
            "display",
            "zones",
            "zone_assignments",
            "phase",
            "description",
            "expression",
            "action",
            "order",
            "enabled",
            "ratelimit_threshold",
            "ratelimit_period",
            "ip_alias",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "description", "phase", "action", "order"]


class CloudflareMonitorSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflaremonitor-detail"
    )

    class Meta:
        model = CloudflareMonitor
        fields = [
            "id",
            "url",
            "display",
            "name",
            "account",
            "type",
            "method",
            "path",
            "port",
            "expected_codes",
            "expected_body",
            "header",
            "probe_zone",
            "interval",
            "timeout",
            "retries",
            "consecutive_up",
            "consecutive_down",
            "follow_redirects",
            "allow_insecure",
            "description",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "type"]


class CloudflareLBPoolSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflarelbpool-detail"
    )
    monitor = CloudflareMonitorSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = CloudflareLBPool
        fields = [
            "id",
            "url",
            "display",
            "name",
            "account",
            "monitor",
            "enabled",
            "minimum_origins",
            "notification_email",
            "description",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "enabled"]


class CloudflareLBOriginSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflarelborigin-detail"
    )
    pool = CloudflareLBPoolSerializer(nested=True)

    class Meta:
        model = CloudflareLBOrigin
        fields = [
            "id",
            "url",
            "display",
            "pool",
            "name",
            "address",
            "enabled",
            "weight",
            "header",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "pool", "name", "address"]


class CloudflareLoadBalancerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflareloadbalancer-detail"
    )
    zone = ZoneSerializer(nested=True)
    fallback_pool = CloudflareLBPoolSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = CloudflareLoadBalancer
        fields = [
            "id",
            "url",
            "display",
            "zone",
            "name",
            "fallback_pool",
            "steering_policy",
            "session_affinity",
            "proxied",
            "enabled",
            "ttl",
            "description",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "zone", "name", "enabled"]


class CloudflareLBDefaultPoolSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflarelbdefaultpool-detail"
    )
    load_balancer = CloudflareLoadBalancerSerializer(nested=True)
    pool = CloudflareLBPoolSerializer(nested=True)

    class Meta:
        model = CloudflareLBDefaultPool
        fields = [
            "id",
            "url",
            "display",
            "load_balancer",
            "pool",
            "order",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "load_balancer", "pool", "order"]
