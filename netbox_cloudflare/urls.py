# SPDX-License-Identifier: AGPL-3.0-or-later
from django.urls import path
from netbox.views.generic import ObjectChangeLogView, ObjectJournalView

from . import models, views


def _crud(slug, name, model, view, list_view, edit_view, delete_view, bulk_delete_view):
    """Standard NetBox object URL set (list/add/bulk-delete/detail/edit/delete/changelog/journal)."""
    return [
        path(f"{slug}/", list_view.as_view(), name=f"{name}_list"),
        path(f"{slug}/add/", edit_view.as_view(), name=f"{name}_add"),
        path(f"{slug}/delete/", bulk_delete_view.as_view(), name=f"{name}_bulk_delete"),
        path(f"{slug}/<int:pk>/", view.as_view(), name=name),
        path(f"{slug}/<int:pk>/edit/", edit_view.as_view(), name=f"{name}_edit"),
        path(f"{slug}/<int:pk>/delete/", delete_view.as_view(), name=f"{name}_delete"),
        path(
            f"{slug}/<int:pk>/changelog/",
            ObjectChangeLogView.as_view(),
            name=f"{name}_changelog",
            kwargs={"model": model},
        ),
        path(
            f"{slug}/<int:pk>/journal/",
            ObjectJournalView.as_view(),
            name=f"{name}_journal",
            kwargs={"model": model},
        ),
    ]


urlpatterns = [
    *_crud(
        "tunnels",
        "cloudflaretunnel",
        models.CloudflareTunnel,
        views.CloudflareTunnelView,
        views.CloudflareTunnelListView,
        views.CloudflareTunnelEditView,
        views.CloudflareTunnelDeleteView,
        views.CloudflareTunnelBulkDeleteView,
    ),
    *_crud(
        "ingress-rules",
        "cloudflareingress",
        models.CloudflareIngress,
        views.CloudflareIngressView,
        views.CloudflareIngressListView,
        views.CloudflareIngressEditView,
        views.CloudflareIngressDeleteView,
        views.CloudflareIngressBulkDeleteView,
    ),
    *_crud(
        "records",
        "cloudflarerecord",
        models.CloudflareRecord,
        views.CloudflareRecordView,
        views.CloudflareRecordListView,
        views.CloudflareRecordEditView,
        views.CloudflareRecordDeleteView,
        views.CloudflareRecordBulkDeleteView,
    ),
    *_crud(
        "waf-rules",
        "cloudflarewafrule",
        models.CloudflareWAFRule,
        views.CloudflareWAFRuleView,
        views.CloudflareWAFRuleListView,
        views.CloudflareWAFRuleEditView,
        views.CloudflareWAFRuleDeleteView,
        views.CloudflareWAFRuleBulkDeleteView,
    ),
]
