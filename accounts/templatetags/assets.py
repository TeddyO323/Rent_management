from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static


register = template.Library()


@register.simple_tag
def asset_url(path):
    asset_path = Path(settings.BASE_DIR) / "static" / path
    version = int(asset_path.stat().st_mtime) if asset_path.exists() else 1
    return f"{static(path)}?v={version}"
