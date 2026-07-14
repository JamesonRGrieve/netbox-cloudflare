# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_cloudflare"

router = NetBoxRouter()
router.register("tunnels", views.CloudflareTunnelViewSet)
router.register("ingress-rules", views.CloudflareIngressViewSet)
router.register("records", views.CloudflareRecordViewSet)
router.register("waf-rules", views.CloudflareWAFRuleViewSet)
router.register("monitors", views.CloudflareMonitorViewSet)
router.register("lb-pools", views.CloudflareLBPoolViewSet)
router.register("lb-origins", views.CloudflareLBOriginViewSet)
router.register("load-balancers", views.CloudflareLoadBalancerViewSet)
router.register("lb-default-pools", views.CloudflareLBDefaultPoolViewSet)

urlpatterns = router.urls
