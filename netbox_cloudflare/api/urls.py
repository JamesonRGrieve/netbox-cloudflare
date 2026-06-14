# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_cloudflare"

router = NetBoxRouter()
router.register("tunnels", views.CloudflareTunnelViewSet)
router.register("ingress-rules", views.CloudflareIngressViewSet)
router.register("records", views.CloudflareRecordViewSet)
router.register("waf-rules", views.CloudflareWAFRuleViewSet)

urlpatterns = router.urls
