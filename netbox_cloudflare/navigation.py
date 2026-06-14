# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem


def _item(name, label):
    return PluginMenuItem(
        link=f"plugins:netbox_cloudflare:{name}_list",
        link_text=label,
        buttons=[
            PluginMenuButton(
                f"plugins:netbox_cloudflare:{name}_add", "Add", "mdi mdi-plus-thick"
            )
        ],
    )


menu = PluginMenu(
    label="Cloudflare",
    groups=(
        (
            "DNS",
            (
                _item("cloudflarerecord", "Records"),
                _item("cloudflarewafrule", "WAF Rules"),
            ),
        ),
        (
            "Tunnels",
            (
                _item("cloudflaretunnel", "Tunnels"),
                _item("cloudflareingress", "Ingress Rules"),
            ),
        ),
    ),
    icon_class="mdi mdi-cloud",
)
