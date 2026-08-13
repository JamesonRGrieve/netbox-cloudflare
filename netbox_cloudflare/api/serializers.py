# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.serializers import NetBoxModelSerializer
from netbox_dns.api.serializers import ZoneSerializer
from netbox_dns.models import Zone
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


class CloudflareWAFRuleZoneWriteSerializer(serializers.Serializer):
    zone = serializers.PrimaryKeyRelatedField(queryset=Zone.objects.all())
    enabled = serializers.NullBooleanField(required=False, default=None)


class CloudflareWAFRuleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloudflare-api:cloudflarewafrule-detail"
    )
    zones = ZoneSerializer(nested=True, many=True, read_only=True)
    zone_assignments = CloudflareWAFRuleZoneSerializer(many=True, read_only=True)
    ip_alias = AliasSerializer(nested=True, required=False, allow_null=True)

    def to_internal_value(self, data):
        self._zone_assignments_input = data.pop("zone_assignments", None)
        return super().to_internal_value(data)

    def _sync_zone_assignments(self, instance, za_data):
        incoming = {item["zone"].pk if hasattr(item["zone"], "pk") else item["zone"]: item.get("enabled") for item in za_data}
        existing = {za.zone_id: za for za in instance.zone_assignments.all()}
        for zone_id in set(existing) - set(incoming):
            existing[zone_id].delete()
        for zone_id, enabled in incoming.items():
            if zone_id in existing:
                if existing[zone_id].enabled != enabled:
                    existing[zone_id].enabled = enabled
                    existing[zone_id].save()
            else:
                CloudflareWAFRuleZone.objects.create(rule=instance, zone_id=zone_id, enabled=enabled)

    def create(self, validated_data):
        instance = super().create(validated_data)
        if self._zone_assignments_input is not None:
            write_ser = CloudflareWAFRuleZoneWriteSerializer(data=self._zone_assignments_input, many=True)
            write_ser.is_valid(raise_exception=True)
            self._sync_zone_assignments(instance, write_ser.validated_data)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if self._zone_assignments_input is not None:
            write_ser = CloudflareWAFRuleZoneWriteSerializer(data=self._zone_assignments_input, many=True)
            write_ser.is_valid(raise_exception=True)
            self._sync_zone_assignments(instance, write_ser.validated_data)
        return instance

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
