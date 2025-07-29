# Superset Analytics Integration

This module provides seamless integration between Odoo and Apache Superset, allowing you to embed Superset dashboards directly in your Odoo instance.

## Features

- Embed Superset dashboards directly in Odoo
- Single Sign-On (SSO) authentication via JWT
- Role-based access control
- Automatic token refresh
- Responsive iframe integration

## Requirements

- Odoo 18.0+
- Apache Superset with JWT authentication enabled
- PyJWT Python package (optional but recommended for SSO functionality)

## Installation

1. Install the module in your Odoo instance
2. If you want to use the SSO functionality, install the PyJWT package:
   ```
   pip install PyJWT
   ```
   Note: The module will work without PyJWT, but the SSO functionality will be disabled.

## Configuration

### Odoo Configuration
1. Install the module
2. Go to Analytics > Dashboard Configuration
3. Create a new dashboard configuration with the following information:
   - Dashboard Name: A descriptive name for the dashboard
   - Dashboard ID: The ID of the dashboard in Superset
   - Superset URL: The URL of your Superset instance
   - JWT Secret Key: The secret key used for JWT authentication
   - Allowed Groups: The Odoo groups that are allowed to access this dashboard
   - Superset User Credentials: The username, email, first name, and last name to use for authentication with Superset

### Superset Configuration
For detailed instructions on how to configure Apache Superset for this integration, please refer to the [Superset Configuration Guide](doc/superset_configuration.md) included in this module.

## Usage

1. Go to Analytics menu
2. Click on the dashboard you want to view
3. The dashboard will be displayed in an iframe within Odoo, with automatic authentication

### Viewing Options

The module provides three ways to view dashboards:

1. **Iframe View**: The dashboard is displayed in an iframe within Odoo, allowing you to stay within the Odoo interface while viewing the dashboard. This is the default method when clicking the "View Dashboard (Iframe)" button. It may have authentication issues with some Superset configurations due to browser security restrictions. Note that if you navigate within Superset (e.g., clicking "Back to home" or other Superset menu items), you will lose authentication and see the Superset login page. This is expected behavior as the JWT token is only valid for the specific dashboard URL.

2. **New Window View**: The dashboard is opened directly in a new browser window or tab. This is useful when you want to keep the Odoo interface open while viewing the dashboard. Click the "View Dashboard (New Window)" button to use this option.

3. **Test Connection**: You can test the connection to Superset by clicking the "Test Connection" button in the dashboard configuration form. This will show you the URL that will be used to access the dashboard.

## Technical Details

The module uses JWT (JSON Web Tokens) for authentication with Superset. When a user accesses a dashboard, the module generates a JWT token with the configured Superset user credentials and embeds it in the URL to Superset. Superset validates the token and displays the dashboard for the user.

The token is automatically refreshed every 50 minutes to ensure continuous access to the dashboard.

### Superset User Credentials

The module allows you to configure specific user credentials for authentication with Superset. This is useful when you want to use a dedicated Superset user for all connections from Odoo, rather than mapping each Odoo user to a Superset user.

The following fields are available:
- Superset Username: The username to use for authentication with Superset
- Superset Email: The email to use for authentication with Superset
- Superset First Name: The first name to use for authentication with Superset
- Superset Last Name: The last name to use for authentication with Superset

These credentials are used to generate the JWT token that is sent to Superset for authentication.

## Security

- Only users in the allowed groups can access the dashboards
- JWT tokens are encrypted and have a limited lifetime
- Dashboard configurations can only be created and modified by system administrators

## Troubleshooting

If you encounter any issues with the module or the integration with Superset, please refer to the [Troubleshooting Guide](doc/troubleshooting.md) for common problems and their solutions.

## Support

For any issues or questions, please contact kardan.digital.