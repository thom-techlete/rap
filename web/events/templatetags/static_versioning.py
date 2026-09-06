import hashlib
import os

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import format_html, format_html_join

register = template.Library()


def is_versioning_enabled():
    """Check if static versioning is enabled in settings."""
    return getattr(settings, "STATIC_VERSIONING_ENABLED", True)


@register.simple_tag
def static_v(path):
    """
    Template tag that adds a version parameter to static files for cache busting.

    Usage: {% static_v 'css/style.css' %}
    Result: /static/css/style.css?v=abc123def456

    The version is based on the file's modification time and size for reliability.
    Can be disabled via STATIC_VERSIONING_ENABLED setting.
    """
    # Get the normal static URL
    static_url = static(path)

    # If versioning is disabled, return the normal static URL
    if not is_versioning_enabled():
        return static_url

    # Get the full file path
    full_path = None

    if hasattr(settings, "STATICFILES_DIRS") and settings.STATICFILES_DIRS:
        # Development: check in STATICFILES_DIRS
        for static_dir in settings.STATICFILES_DIRS:
            test_path = os.path.join(static_dir, path)
            if os.path.exists(test_path):
                full_path = test_path
                break

    # If not found in STATICFILES_DIRS, try STATIC_ROOT
    if not full_path and hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT:
        test_path = os.path.join(settings.STATIC_ROOT, path)
        if os.path.exists(test_path):
            full_path = test_path

    # If file doesn't exist, return original URL
    if not full_path:
        return static_url

    # Generate version based on file modification time and size
    try:
        # Get file stats
        stat = os.stat(full_path)
        mtime = str(int(stat.st_mtime))
        size = str(stat.st_size)

        # Create a hash based on mtime and size for shorter version string
        version_string = f"{mtime}-{size}"
        version_hash = hashlib.md5(
            version_string.encode(), usedforsecurity=False
        ).hexdigest()[:8]

        # Add version parameter to URL
        separator = "&" if "?" in static_url else "?"
        versioned_url = f"{static_url}{separator}v={version_hash}"

        return versioned_url
    except OSError:
        # Error accessing file, return original URL
        return static_url


@register.simple_tag
def static_v_css(path):
    """
    Template tag specifically for CSS files with cache busting.

    Usage: {% static_v_css 'css/style.css' %}
    Result: <link rel="stylesheet" href="/static/css/style.css?v=abc123def456" />
    """
    versioned_url = static_v(path)
    return format_html('<link rel="stylesheet" href="{}" />', versioned_url)


@register.simple_tag
def static_v_js(path):
    """
    Template tag specifically for JavaScript files with cache busting.

    Usage: {% static_v_js 'js/app.js' %}
    Result: <script src="/static/js/app.js?v=abc123def456"></script>
    """
    versioned_url = static_v(path)
    return format_html('<script src="{}"></script>', versioned_url)


@register.simple_tag
def static_v_img(path, alt_text="", css_class="", **attrs):
    """
    Template tag specifically for image files with cache busting.

    Usage: {% static_v_img 'media/logo.png' alt_text='Logo' css_class='logo-image' %}
    Result: <img src="/static/media/logo.png?v=abc123def456" alt="Logo" class="logo-image" />
    """
    versioned_url = static_v(path)

    # Build attributes string
    attr_parts: list[tuple[str, object]] = []
    if alt_text:
        attr_parts.append(("alt", alt_text))
    if css_class:
        attr_parts.append(("class", css_class))

    # Add any additional attributes
    for key, value in attrs.items():
        attr_parts.append((key, value))

    attrs_string = format_html_join("", ' {}="{}"', attr_parts)

    return format_html('<img src="{}"{} />', versioned_url, attrs_string)


@register.simple_tag
def static_v_link(path, rel="stylesheet", **attrs):
    """
    Generic template tag for link elements with cache busting.

    Usage: {% static_v_link 'media/favicon.ico' rel='icon' type='image/x-icon' %}
    Result: <link rel="icon" type="image/x-icon" href="/static/media/favicon.ico?v=abc123def456" />
    """
    versioned_url = static_v(path)

    # Build attributes string
    attr_parts: list[tuple[str, object]] = [("rel", rel)]
    for key, value in attrs.items():
        attr_parts.append((key, value))

    attrs_string = format_html_join("", ' {}="{}"', attr_parts)

    return format_html('<link{} href="{}" />', attrs_string, versioned_url)
