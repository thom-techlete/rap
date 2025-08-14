# Static File Versioning for Cache Busting

This document explains how to use the custom static file versioning system implemented for the SV Rap 8 Event Presence webapp.

## Overview

The static versioning system automatically adds version parameters to static file URLs to ensure browsers load fresh files when they are updated. This solves the common problem where updated CSS/JS files are not loaded due to browser caching.

## How It Works

The system generates version hashes based on file modification time and size. When a file is updated, its version hash changes, forcing browsers to download the new version.

Example:
- Original: `/static/css/style.css`
- Versioned: `/static/css/style.css?v=abc123def456`

## Usage

### Load the Template Tags

Add this to the top of your templates:

```html
{% load static_versioning %}
```

### Basic Usage

Replace `{% static %}` tags with `{% static_v %}`:

```html
<!-- Old -->
<link rel="stylesheet" href="{% static 'css/style.css' %}" />

<!-- New -->
<link rel="stylesheet" href="{% static_v 'css/style.css' %}" />
```

### Convenience Tags

For common use cases, use the specialized tags:

#### CSS Files
```html
{% static_v_css 'css/style.css' %}
<!-- Generates: <link rel="stylesheet" href="/static/css/style.css?v=abc123def456" /> -->
```

#### JavaScript Files
```html
{% static_v_js 'js/app.js' %}
<!-- Generates: <script src="/static/js/app.js?v=abc123def456"></script> -->
```

#### Images
```html
{% static_v_img 'media/logo.png' alt_text='Logo' css_class='logo-image' %}
<!-- Generates: <img src="/static/media/logo.png?v=abc123def456" alt="Logo" class="logo-image" /> -->

<!-- With additional attributes -->
{% static_v_img 'media/avatar.jpg' alt_text='Avatar' width='50' height='50' %}
```

#### Generic Links
```html
{% static_v_link 'media/favicon.ico' rel='icon' type='image/x-icon' %}
<!-- Generates: <link rel="icon" type="image/x-icon" href="/static/media/favicon.ico?v=abc123def456" /> -->
```

## Configuration

### Enable/Disable Versioning

In `settings.py`, you can control whether versioning is enabled:

```python
# Enable static file versioning (default: opposite of DEBUG)
STATIC_VERSIONING_ENABLED = True  # or False to disable
```

By default, versioning is enabled in production (when `DEBUG=False`) and disabled in development.

### Environment Variable

You can also control this via environment variable:

```bash
export STATIC_VERSIONING_ENABLED=true
```

## Management Commands

### Clear Static Cache

Force regeneration of all static file versions:

```bash
# Preview what files would be touched
python manage.py clear_static_cache --dry-run

# Actually update modification times
python manage.py clear_static_cache
```

This command updates the modification time of all static files, which will generate new version hashes.

## Template Updates

### Updated Base Template

The main `base.html` template has been updated to use versioned static tags:

```html
{% load static %}
{% load static_versioning %}

<!-- Favicon -->
<link rel="icon" type="image/x-icon" href="{% static_v 'media/favicon.ico' %}" />

<!-- CSS -->
{% static_v_css 'css/style.css' %}

<!-- Images -->
{% static_v_img 'media/sv-rap.png' alt_text='SV Rap Logo' css_class='logo-image' %}

<!-- JavaScript -->
{% static_v_js 'js/app.js' %}
```

### Child Templates

For child templates, use the `extra_css` and `extra_js` blocks:

```html
{% extends "base.html" %}
{% load static_versioning %}

{% block extra_css %}
{% static_v_css 'css/events/event_form.css' %}
{% endblock %}

{% block extra_js %}
{% static_v_js 'js/events/event_form.js' %}
{% endblock %}
```

## Testing

Run the static versioning tests:

```bash
python manage.py test events.test_static_versioning
```

## Files Created/Modified

### New Files
- `web/events/templatetags/static_versioning.py` - Template tags for versioned static files
- `web/events/management/commands/clear_static_cache.py` - Management command for cache clearing
- `web/events/test_static_versioning.py` - Unit tests for static versioning

### Modified Files
- `web/rap_web/settings.py` - Added `STATIC_VERSIONING_ENABLED` setting
- `web/templates/base.html` - Updated to use versioned static tags

## Benefits

1. **Automatic Cache Busting**: No manual intervention needed when files are updated
2. **Improved User Experience**: Users always get the latest version of static files
3. **Performance**: Browsers can still cache files efficiently until they change
4. **Easy Integration**: Simple template tag replacement with minimal code changes
5. **Configurable**: Can be enabled/disabled based on environment
6. **Fallback Safety**: If versioning fails, falls back to regular static URLs

## Troubleshooting

### Versioning Not Working
1. Check that `STATIC_VERSIONING_ENABLED` is `True` in settings
2. Verify static files exist in `STATICFILES_DIRS` or `STATIC_ROOT`
3. Check file permissions on static files

### Performance Concerns
The system uses file system operations to get file modification times. For very large numbers of static files, consider:
1. Using a CDN with its own cache busting
2. Disabling versioning in development
3. Pre-computing version hashes during deployment

### Development vs Production
- **Development**: Versioning is disabled by default (DEBUG=True)
- **Production**: Versioning is enabled by default (DEBUG=False)

This ensures rapid development while providing cache busting in production.
