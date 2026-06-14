# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
from ..models import (
    CloudflareIngress,
    CloudflareRecord,
    CloudflareTunnel,
    CloudflareWAFRule,
)
from .serializers import (
    CloudflareIngressSerializer,
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
    queryset = CloudflareWAFRule.objects.prefetch_related("zone", "ip_prefixes", "tags")
    serializer_class = CloudflareWAFRuleSerializer
    filterset_class = filtersets.CloudflareWAFRuleFilterSet
