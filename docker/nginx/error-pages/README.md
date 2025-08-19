# Static Error Pages

This directory contains static error pages that are served by nginx when Django/backend errors occur. These pages are designed to match the webapp's styling and provide a user-friendly experience even when the backend is unavailable.

## Error Pages

- **400.html** - Bad Request (Ongeldige aanvraag)
- **403.html** - Forbidden (Toegang geweigerd)  
- **404.html** - Not Found (Pagina niet gevonden)
- **500.html** - Internal Server Error (Server probleem)
- **502.html** - Bad Gateway (Service tijdelijk niet beschikbaar)

## Features

### Design & Styling
- **Consistent branding**: Matches the SV Rap 8 webapp design
- **Team colors**: Uses the same color scheme (blue, green, red) as the main application
- **Responsive design**: Works on desktop, tablet, and mobile devices
- **Dutch language**: All text is in Dutch to match the webapp's interface

### User Experience
- **Clear messaging**: Each error has appropriate Dutch descriptions
- **Call-to-action**: Prominent button to return to the dashboard (/)
- **Visual consistency**: Same navigation header and footer as the main app
- **Accessibility**: Proper semantic HTML and ARIA support

### Independence
- **Self-contained**: No dependencies on Django templates or backend
- **CDN resources**: Uses external CDNs for fonts and icons (graceful degradation if blocked)
- **Static assets**: References static files that are served by nginx even if Django is down

## Nginx Configuration

The error pages are configured in both development and production nginx configs:

```nginx
# Error page mappings
error_page 400 /error-pages/400.html;
error_page 403 /error-pages/403.html;
error_page 404 /error-pages/404.html;
error_page 500 502 503 504 /error-pages/500.html;
error_page 502 /error-pages/502.html;

# Static error pages location
location /error-pages/ {
    root /etc/nginx;
    internal;
}
```

## Docker Setup

The error pages are mounted as read-only volumes in Docker Compose:

```yaml
nginx:
  volumes:
    - ./nginx/error-pages:/etc/nginx/error-pages:ro
```

## Testing

To test the error pages locally:

1. **Development**: Access via nginx proxy at `http://localhost:8080/`
2. **Direct testing**: Run a simple HTTP server in this directory:
   ```bash
   cd docker/nginx/error-pages
   python -m http.server 8080
   ```

## Error Page Triggers

These pages will be shown when:

- **400**: Invalid request format or malformed data
- **403**: Authentication/authorization failures  
- **404**: Requested URL/resource not found
- **500**: Django application errors, database connection issues
- **502**: Backend unavailable (during deployments, restarts)

The static nature ensures users always see a branded, helpful error page regardless of the backend state.