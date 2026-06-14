# SPDX-License-Identifier: AGPL-3.0-or-later
import django_filters
from django.db.models import Q
from ipam.models import Prefix
from netbox.filtersets import NetBoxModelFilterSet
from netbox_dns.models import Zone

from .choices import (
    CloudflareRecordTypeChoices,
    CloudflareWAFActionChoices,
    CloudflareWAFPhaseChoices,
)
from .models import (
    CloudflareIngress,
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
        field_name="zone", queryset=Zone.objects.all(), label="Zone (ID)"
    )
    prefix_id = django_filters.ModelMultipleChoiceFilter(
        field_name="ip_prefixes", queryset=Prefix.objects.all(), label="IP prefix (ID)"
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
            | Q(zone__name__icontains=value)
        )
