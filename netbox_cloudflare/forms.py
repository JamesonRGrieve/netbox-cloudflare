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
    zone = DynamicModelChoiceField(queryset=Zone.objects.all())
    ip_alias = DynamicModelChoiceField(queryset=Alias.objects.all(), required=False)

    fieldsets = (
        FieldSet("zone", "phase", "order", "enabled", name="Rule"),
        FieldSet("description", "expression", "action", name="Match"),
        FieldSet("ratelimit_threshold", "ratelimit_period", name="Rate limit"),
        FieldSet("ip_alias", name="IP list"),
    )

    class Meta:
        model = CloudflareWAFRule
        fields = [
            "zone",
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
