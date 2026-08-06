# SPDX-License-Identifier: AGPL-3.0-or-later
import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet
from netbox_dns.models import Zone
from netbox_pf.models import Alias

from .choices import (
    CloudflareLBSteeringChoices,
    CloudflareMonitorTypeChoices,
    CloudflareRecordTypeChoices,
    CloudflareWAFActionChoices,
    CloudflareWAFPhaseChoices,
)
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


# Explicit FK filters: django-filter does NOT derive `<fk>_id` from a bare FK in Meta.fields,
# so a bare `zone`/`tunnel` would be silently ignored. NetBox convention is `<fk>_id`.
class CloudflareTunnelFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = CloudflareTunnel
        fields = ["id", "name", "account", "tunnel_id"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(account__icontains=value)
            | Q(tunnel_id__icontains=value)
        )


class CloudflareIngressFilterSet(NetBoxModelFilterSet):
    tunnel_id = django_filters.ModelMultipleChoiceFilter(
        field_name="tunnel", queryset=CloudflareTunnel.objects.all(), label="Tunnel (ID)"
    )

    class Meta:
        model = CloudflareIngress
        fields = ["id", "hostname", "path", "service", "order"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(hostname__icontains=value) | Q(service__icontains=value)
        )


class CloudflareRecordFilterSet(NetBoxModelFilterSet):
    zone_id = django_filters.ModelMultipleChoiceFilter(
        field_name="zone", queryset=Zone.objects.all(), label="Zone (ID)"
    )
    tunnel_id = django_filters.ModelMultipleChoiceFilter(
        field_name="tunnel", queryset=CloudflareTunnel.objects.all(), label="Tunnel (ID)"
    )
    type = django_filters.MultipleChoiceFilter(choices=CloudflareRecordTypeChoices)

    class Meta:
        model = CloudflareRecord
        fields = ["id", "name", "content", "proxied", "ttl", "ddns_enabled", "ddns_source"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(content__icontains=value)
            | Q(zone__name__icontains=value)
        )


class CloudflareWAFRuleFilterSet(NetBoxModelFilterSet):
    zone_id = django_filters.ModelMultipleChoiceFilter(
        field_name="zones", queryset=Zone.objects.all(), label="Zone (ID)"
    )
    ip_alias_id = django_filters.ModelMultipleChoiceFilter(
        field_name="ip_alias", queryset=Alias.objects.all(), label="IP alias (ID)"
    )
    phase = django_filters.MultipleChoiceFilter(choices=CloudflareWAFPhaseChoices)
    action = django_filters.MultipleChoiceFilter(choices=CloudflareWAFActionChoices)

    class Meta:
        model = CloudflareWAFRule
        fields = ["id", "description", "order", "enabled"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(description__icontains=value)
            | Q(expression__icontains=value)
            | Q(zones__name__icontains=value)
        ).distinct()


class CloudflareMonitorFilterSet(NetBoxModelFilterSet):
    type = django_filters.MultipleChoiceFilter(choices=CloudflareMonitorTypeChoices)

    class Meta:
        model = CloudflareMonitor
        fields = ["id", "name", "account", "path", "probe_zone", "interval", "retries"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(probe_zone__icontains=value)
            | Q(description__icontains=value)
        )


class CloudflareLBPoolFilterSet(NetBoxModelFilterSet):
    monitor_id = django_filters.ModelMultipleChoiceFilter(
        field_name="monitor", queryset=CloudflareMonitor.objects.all(), label="Monitor (ID)"
    )

    class Meta:
        model = CloudflareLBPool
        fields = ["id", "name", "account", "enabled", "minimum_origins"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class CloudflareLBOriginFilterSet(NetBoxModelFilterSet):
    pool_id = django_filters.ModelMultipleChoiceFilter(
        field_name="pool", queryset=CloudflareLBPool.objects.all(), label="Pool (ID)"
    )

    class Meta:
        model = CloudflareLBOrigin
        fields = ["id", "name", "address", "enabled"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(address__icontains=value)
            | Q(pool__name__icontains=value)
        )


class CloudflareLoadBalancerFilterSet(NetBoxModelFilterSet):
    zone_id = django_filters.ModelMultipleChoiceFilter(
        field_name="zone", queryset=Zone.objects.all(), label="Zone (ID)"
    )
    fallback_pool_id = django_filters.ModelMultipleChoiceFilter(
        field_name="fallback_pool",
        queryset=CloudflareLBPool.objects.all(),
        label="Fallback pool (ID)",
    )
    # The default pools are reached through the ordered through-model, not a direct FK.
    pool_id = django_filters.ModelMultipleChoiceFilter(
        field_name="pool_assignments__pool",
        queryset=CloudflareLBPool.objects.all(),
        label="Default pool (ID)",
        distinct=True,
    )
    steering_policy = django_filters.MultipleChoiceFilter(choices=CloudflareLBSteeringChoices)

    class Meta:
        model = CloudflareLoadBalancer
        fields = ["id", "name", "proxied", "enabled"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(zone__name__icontains=value)
            | Q(description__icontains=value)
        )


class CloudflareLBDefaultPoolFilterSet(NetBoxModelFilterSet):
    load_balancer_id = django_filters.ModelMultipleChoiceFilter(
        field_name="load_balancer",
        queryset=CloudflareLoadBalancer.objects.all(),
        label="Load balancer (ID)",
    )
    pool_id = django_filters.ModelMultipleChoiceFilter(
        field_name="pool", queryset=CloudflareLBPool.objects.all(), label="Pool (ID)"
    )

    class Meta:
        model = CloudflareLBDefaultPool
        fields = ["id", "order"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(load_balancer__name__icontains=value) | Q(pool__name__icontains=value)
        )
