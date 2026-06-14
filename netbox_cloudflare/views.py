# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.views import generic

from . import filtersets, forms, models, tables


class CloudflareTunnelView(generic.ObjectView):
    queryset = models.CloudflareTunnel.objects.all()


class CloudflareTunnelListView(generic.ObjectListView):
    queryset = models.CloudflareTunnel.objects.all()
    table = tables.CloudflareTunnelTable
    filterset = filtersets.CloudflareTunnelFilterSet
    filterset_form = forms.CloudflareTunnelFilterForm


class CloudflareTunnelEditView(generic.ObjectEditView):
    queryset = models.CloudflareTunnel.objects.all()
    form = forms.CloudflareTunnelForm


class CloudflareTunnelDeleteView(generic.ObjectDeleteView):
    queryset = models.CloudflareTunnel.objects.all()


class CloudflareTunnelBulkDeleteView(generic.BulkDeleteView):
    queryset = models.CloudflareTunnel.objects.all()
    table = tables.CloudflareTunnelTable


class CloudflareIngressView(generic.ObjectView):
    queryset = models.CloudflareIngress.objects.all()


class CloudflareIngressListView(generic.ObjectListView):
    queryset = models.CloudflareIngress.objects.all()
    table = tables.CloudflareIngressTable
    filterset = filtersets.CloudflareIngressFilterSet
    filterset_form = forms.CloudflareIngressFilterForm


class CloudflareIngressEditView(generic.ObjectEditView):
    queryset = models.CloudflareIngress.objects.all()
    form = forms.CloudflareIngressForm


class CloudflareIngressDeleteView(generic.ObjectDeleteView):
    queryset = models.CloudflareIngress.objects.all()


class CloudflareIngressBulkDeleteView(generic.BulkDeleteView):
    queryset = models.CloudflareIngress.objects.all()
    table = tables.CloudflareIngressTable


class CloudflareRecordView(generic.ObjectView):
    queryset = models.CloudflareRecord.objects.all()


class CloudflareRecordListView(generic.ObjectListView):
    queryset = models.CloudflareRecord.objects.all()
    table = tables.CloudflareRecordTable
    filterset = filtersets.CloudflareRecordFilterSet
    filterset_form = forms.CloudflareRecordFilterForm


class CloudflareRecordEditView(generic.ObjectEditView):
    queryset = models.CloudflareRecord.objects.all()
    form = forms.CloudflareRecordForm


class CloudflareRecordDeleteView(generic.ObjectDeleteView):
    queryset = models.CloudflareRecord.objects.all()


class CloudflareRecordBulkDeleteView(generic.BulkDeleteView):
    queryset = models.CloudflareRecord.objects.all()
    table = tables.CloudflareRecordTable


class CloudflareWAFRuleView(generic.ObjectView):
    queryset = models.CloudflareWAFRule.objects.all()


class CloudflareWAFRuleListView(generic.ObjectListView):
    queryset = models.CloudflareWAFRule.objects.all()
    table = tables.CloudflareWAFRuleTable
    filterset = filtersets.CloudflareWAFRuleFilterSet
    filterset_form = forms.CloudflareWAFRuleFilterForm


class CloudflareWAFRuleEditView(generic.ObjectEditView):
    queryset = models.CloudflareWAFRule.objects.all()
    form = forms.CloudflareWAFRuleForm


class CloudflareWAFRuleDeleteView(generic.ObjectDeleteView):
    queryset = models.CloudflareWAFRule.objects.all()


class CloudflareWAFRuleBulkDeleteView(generic.BulkDeleteView):
    queryset = models.CloudflareWAFRule.objects.all()
    table = tables.CloudflareWAFRuleTable
