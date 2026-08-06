# SPDX-License-Identifier: AGPL-3.0-or-later
from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from netbox_dns.models import Zone
from netbox_pf.models import Alias
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet

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


class CloudflareTunnelForm(NetBoxModelForm):
    fieldsets = (FieldSet("name", "account", "tunnel_id", "comment", name="Tunnel"),)

    class Meta:
        model = CloudflareTunnel
        fields = ["name", "account", "tunnel_id", "comment", "tags"]


class CloudflareTunnelFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareTunnel
    account = forms.CharField(required=False)
    tag = TagFilterField(CloudflareTunnel)


class CloudflareIngressForm(NetBoxModelForm):
    tunnel = DynamicModelChoiceField(queryset=CloudflareTunnel.objects.all())

    fieldsets = (
        FieldSet("tunnel", "order", name="Tunnel"),
        FieldSet("hostname", "path", "service", "origin_request", name="Match"),
    )

    class Meta:
        model = CloudflareIngress
        fields = ["tunnel", "hostname", "path", "service", "order", "origin_request", "tags"]


class CloudflareIngressFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareIngress
    tunnel_id = DynamicModelMultipleChoiceField(
        queryset=CloudflareTunnel.objects.all(), required=False, label="Tunnel"
    )
    tag = TagFilterField(CloudflareIngress)


class CloudflareRecordForm(NetBoxModelForm):
    zone = DynamicModelChoiceField(queryset=Zone.objects.all())
    tunnel = DynamicModelChoiceField(queryset=CloudflareTunnel.objects.all(), required=False)

    fieldsets = (
        FieldSet("zone", "name", "type", name="Record"),
        FieldSet("content", "tunnel", name="Static / Tunnel target"),
        FieldSet("ddns_enabled", "ddns_source", name="DDNS"),
        FieldSet("proxied", "ttl", name="Edge"),
    )

    class Meta:
        model = CloudflareRecord
        fields = [
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
        ]


class CloudflareRecordFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareRecord
    zone_id = DynamicModelMultipleChoiceField(
        queryset=Zone.objects.all(), required=False, label="Zone"
    )
    tunnel_id = DynamicModelMultipleChoiceField(
        queryset=CloudflareTunnel.objects.all(), required=False, label="Tunnel"
    )
    type = forms.MultipleChoiceField(choices=CloudflareRecordTypeChoices, required=False)
    proxied = forms.NullBooleanField(required=False)
    ddns_enabled = forms.NullBooleanField(required=False)
    tag = TagFilterField(CloudflareRecord)


class CloudflareWAFRuleForm(NetBoxModelForm):
    zones = DynamicModelMultipleChoiceField(queryset=Zone.objects.all(), required=False)
    ip_alias = DynamicModelChoiceField(queryset=Alias.objects.all(), required=False)

    fieldsets = (
        FieldSet("zones", "phase", "order", "enabled", name="Rule"),
        FieldSet("description", "expression", "action", name="Match"),
        FieldSet("ratelimit_threshold", "ratelimit_period", name="Rate limit"),
        FieldSet("ip_alias", name="IP list"),
    )

    class Meta:
        model = CloudflareWAFRule
        fields = [
            "zones",
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
        ]


class CloudflareWAFRuleFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareWAFRule
    zone_id = DynamicModelMultipleChoiceField(
        queryset=Zone.objects.all(), required=False, label="Zone"
    )
    ip_alias_id = DynamicModelMultipleChoiceField(
        queryset=Alias.objects.all(), required=False, label="IP alias"
    )
    phase = forms.MultipleChoiceField(choices=CloudflareWAFPhaseChoices, required=False)
    action = forms.MultipleChoiceField(choices=CloudflareWAFActionChoices, required=False)
    enabled = forms.NullBooleanField(required=False)
    tag = TagFilterField(CloudflareWAFRule)


class CloudflareMonitorForm(NetBoxModelForm):
    fieldsets = (
        FieldSet("name", "account", "type", "description", name="Monitor"),
        FieldSet(
            "method", "path", "port", "expected_codes", "expected_body", "header", "probe_zone",
            name="Probe",
        ),
        FieldSet(
            "interval", "timeout", "retries", "consecutive_up", "consecutive_down",
            name="Timing",
        ),
        FieldSet("follow_redirects", "allow_insecure", name="TLS / redirects"),
    )

    class Meta:
        model = CloudflareMonitor
        fields = [
            "name", "account", "type", "method", "path", "port", "expected_codes",
            "expected_body", "header", "probe_zone", "interval", "timeout", "retries",
            "consecutive_up", "consecutive_down", "follow_redirects", "allow_insecure",
            "description", "tags",
        ]


class CloudflareMonitorFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareMonitor
    account = forms.CharField(required=False)
    type = forms.MultipleChoiceField(choices=CloudflareMonitorTypeChoices, required=False)
    tag = TagFilterField(CloudflareMonitor)


class CloudflareLBPoolForm(NetBoxModelForm):
    monitor = DynamicModelChoiceField(queryset=CloudflareMonitor.objects.all(), required=False)

    fieldsets = (
        FieldSet("name", "account", "description", name="Pool"),
        FieldSet("monitor", "enabled", "minimum_origins", "notification_email", name="Health"),
    )

    class Meta:
        model = CloudflareLBPool
        fields = [
            "name", "account", "monitor", "enabled", "minimum_origins",
            "notification_email", "description", "tags",
        ]


class CloudflareLBPoolFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareLBPool
    monitor_id = DynamicModelMultipleChoiceField(
        queryset=CloudflareMonitor.objects.all(), required=False, label="Monitor"
    )
    account = forms.CharField(required=False)
    enabled = forms.NullBooleanField(required=False)
    tag = TagFilterField(CloudflareLBPool)


class CloudflareLBOriginForm(NetBoxModelForm):
    pool = DynamicModelChoiceField(queryset=CloudflareLBPool.objects.all())

    fieldsets = (
        FieldSet("pool", "name", "address", name="Origin"),
        FieldSet("enabled", "weight", "header", name="Behaviour"),
    )

    class Meta:
        model = CloudflareLBOrigin
        fields = ["pool", "name", "address", "enabled", "weight", "header", "tags"]


class CloudflareLBOriginFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareLBOrigin
    pool_id = DynamicModelMultipleChoiceField(
        queryset=CloudflareLBPool.objects.all(), required=False, label="Pool"
    )
    enabled = forms.NullBooleanField(required=False)
    tag = TagFilterField(CloudflareLBOrigin)


class CloudflareLoadBalancerForm(NetBoxModelForm):
    zone = DynamicModelChoiceField(queryset=Zone.objects.all())
    fallback_pool = DynamicModelChoiceField(
        queryset=CloudflareLBPool.objects.all(), required=False
    )

    fieldsets = (
        FieldSet("zone", "name", "description", name="Load balancer"),
        FieldSet("steering_policy", "session_affinity", "fallback_pool", name="Steering"),
        FieldSet("proxied", "enabled", "ttl", name="Edge"),
    )

    class Meta:
        model = CloudflareLoadBalancer
        fields = [
            "zone", "name", "fallback_pool", "steering_policy", "session_affinity",
            "proxied", "enabled", "ttl", "description", "tags",
        ]


class CloudflareLoadBalancerFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareLoadBalancer
    zone_id = DynamicModelMultipleChoiceField(
        queryset=Zone.objects.all(), required=False, label="Zone"
    )
    pool_id = DynamicModelMultipleChoiceField(
        queryset=CloudflareLBPool.objects.all(), required=False, label="Default pool"
    )
    steering_policy = forms.MultipleChoiceField(
        choices=CloudflareLBSteeringChoices, required=False
    )
    enabled = forms.NullBooleanField(required=False)
    tag = TagFilterField(CloudflareLoadBalancer)


class CloudflareLBDefaultPoolForm(NetBoxModelForm):
    load_balancer = DynamicModelChoiceField(queryset=CloudflareLoadBalancer.objects.all())
    pool = DynamicModelChoiceField(queryset=CloudflareLBPool.objects.all())

    fieldsets = (FieldSet("load_balancer", "pool", "order", name="Failover priority"),)

    class Meta:
        model = CloudflareLBDefaultPool
        fields = ["load_balancer", "pool", "order", "tags"]


class CloudflareLBDefaultPoolFilterForm(NetBoxModelFilterSetForm):
    model = CloudflareLBDefaultPool
    load_balancer_id = DynamicModelMultipleChoiceField(
        queryset=CloudflareLoadBalancer.objects.all(), required=False, label="Load balancer"
    )
    pool_id = DynamicModelMultipleChoiceField(
        queryset=CloudflareLBPool.objects.all(), required=False, label="Pool"
    )
    tag = TagFilterField(CloudflareLBDefaultPool)
