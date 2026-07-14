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
    queryset = CloudflareWAFRule.objects.prefetch_related("zone", "ip_alias", "tags")
    serializer_class = CloudflareWAFRuleSerializer
    filterset_class = filtersets.CloudflareWAFRuleFilterSet


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
