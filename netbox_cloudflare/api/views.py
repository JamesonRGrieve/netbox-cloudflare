# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
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
)
from .serializers import (
    CloudflareIngressSerializer,
    CloudflareLBDefaultPoolSerializer,
    CloudflareLBOriginSerializer,
    CloudflareLBPoolSerializer,
    CloudflareLoadBalancerSerializer,
    CloudflareMonitorSerializer,
    CloudflareRecordSerializer,
    CloudflareTunnelSerializer,
    CloudflareWAFRuleSerializer,
)


class CloudflareTunnelViewSet(NetBoxModelViewSet):
    queryset = CloudflareTunnel.objects.prefetch_related("tags")
    serializer_class = CloudflareTunnelSerializer
    filterset_class = filtersets.CloudflareTunnelFilterSet


class CloudflareIngressViewSet(NetBoxModelViewSet):
    queryset = CloudflareIngress.objects.prefetch_related("tunnel", "tags")
    serializer_class = CloudflareIngressSerializer
    filterset_class = filtersets.CloudflareIngressFilterSet


class CloudflareRecordViewSet(NetBoxModelViewSet):
    queryset = CloudflareRecord.objects.prefetch_related("zone", "tunnel", "tags")
    serializer_class = CloudflareRecordSerializer
    filterset_class = filtersets.CloudflareRecordFilterSet


class CloudflareWAFRuleViewSet(NetBoxModelViewSet):
    queryset = CloudflareWAFRule.objects.prefetch_related("zones", "zone_assignments", "zone_assignments__zone", "ip_alias", "tags")
    serializer_class = CloudflareWAFRuleSerializer
    filterset_class = filtersets.CloudflareWAFRuleFilterSet

    def perform_update(self, serializer):
        instance = serializer.save()
        za_input = self.request.data.get("zone_assignments")
        if za_input is not None:
            from ..models import CloudflareWAFRuleZone
            incoming = {}
            for item in za_input:
                zone_id = item["zone"] if isinstance(item["zone"], int) else item["zone"]["id"]
                incoming[zone_id] = item.get("enabled")
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

    def perform_create(self, serializer):
        instance = serializer.save()
        za_input = self.request.data.get("zone_assignments")
        if za_input is not None:
            from ..models import CloudflareWAFRuleZone
            for item in za_input:
                zone_id = item["zone"] if isinstance(item["zone"], int) else item["zone"]["id"]
                CloudflareWAFRuleZone.objects.create(rule=instance, zone_id=zone_id, enabled=item.get("enabled"))


class CloudflareMonitorViewSet(NetBoxModelViewSet):
    queryset = CloudflareMonitor.objects.prefetch_related("tags")
    serializer_class = CloudflareMonitorSerializer
    filterset_class = filtersets.CloudflareMonitorFilterSet


class CloudflareLBPoolViewSet(NetBoxModelViewSet):
    queryset = CloudflareLBPool.objects.prefetch_related("monitor", "origins", "tags")
    serializer_class = CloudflareLBPoolSerializer
    filterset_class = filtersets.CloudflareLBPoolFilterSet


class CloudflareLBOriginViewSet(NetBoxModelViewSet):
    queryset = CloudflareLBOrigin.objects.prefetch_related("pool", "tags")
    serializer_class = CloudflareLBOriginSerializer
    filterset_class = filtersets.CloudflareLBOriginFilterSet


class CloudflareLoadBalancerViewSet(NetBoxModelViewSet):
    queryset = CloudflareLoadBalancer.objects.prefetch_related(
        "zone", "fallback_pool", "pool_assignments", "tags"
    )
    serializer_class = CloudflareLoadBalancerSerializer
    filterset_class = filtersets.CloudflareLoadBalancerFilterSet


class CloudflareLBDefaultPoolViewSet(NetBoxModelViewSet):
    queryset = CloudflareLBDefaultPool.objects.prefetch_related(
        "load_balancer", "pool", "tags"
    )
    serializer_class = CloudflareLBDefaultPoolSerializer
    filterset_class = filtersets.CloudflareLBDefaultPoolFilterSet
