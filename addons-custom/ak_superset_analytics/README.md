# Superset Analytics Integration

This module provides seamless integration between Odoo and Apache Superset, allowing you to embed Superset dashboards directly in your Odoo instance.

## Features

- Embed Superset dashboards directly in Odoo
- Single Sign-On (SSO) authentication via JWT
- Role-based access control
- Automatic token refresh
- Responsive iframe integration

## Requirements

- Odoo 16.0+
- Apache Superset with JWT authentication enabled
- PyJWT Python package

## Configuration

1. Install the module
2. Go to Analytics > Dashboard Configuration
3. Create a new dashboard configuration with the following information:
   - Dashboard Name: A descriptive name for the dashboard
   - Dashboard ID: The ID of the dashboard in Superset
   - Superset URL: The URL of your Superset instance
   - JWT Secret Key: The secret key used for JWT authentication
   - Allowed Groups: The Odoo groups that are allowed to access this dashboard

## Usage

1. Go to Analytics menu
2. Click on the dashboard you want to view
3. The dashboard will be displayed in an iframe with automatic authentication

## Technical Details

The module uses JWT (JSON Web Tokens) for authentication with Superset. When a user accesses a dashboard, the module generates a JWT token with the user's information and embeds it in the URL to Superset. Superset validates the token and displays the dashboard for the user.

The token is automatically refreshed every 50 minutes to ensure continuous access to the dashboard.

## Security

- Only users in the allowed groups can access the dashboards
- JWT tokens are encrypted and have a limited lifetime
- Dashboard configurations can only be created and modified by system administrators

## Support

For any issues or questions, please contact kardan.digital.