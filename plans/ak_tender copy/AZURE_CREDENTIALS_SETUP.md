# Azure Credentials Setup Guide

## ⚠️ SECURITY WARNING

**NEVER commit actual Azure credentials to version control!**

This module requires Azure AD credentials to be configured in Odoo System Parameters. The credentials should be obtained from your Azure Portal and configured directly in your Odoo instance.

## Setup Instructions

### 1. Obtain Azure Credentials

From your Azure Portal (https://portal.azure.com):

1. Navigate to **Azure Active Directory** (Microsoft Entra ID)
2. Go to **App registrations**
3. Select your application or create a new one
4. Note down the following values:
   - **Application (client) ID**
   - **Directory (tenant) ID**
5. Go to **Certificates & secrets**
6. Create a new client secret and note down:
   - **Client secret value** (shown only once!)
   - **Secret ID**

### 2. Configure in Odoo

After installing the `ak_tender` module:

1. Go to **Settings > Technical > Parameters > System Parameters**
2. Update the following parameters with your actual values:

| Parameter Key | Description | Example Value |
|--------------|-------------|---------------|
| `ak_tender.azure_client_id` | Azure Application (Client) ID | `xxx` |
| `ak_tender.azure_client_secret` | Azure Client Secret | `xxx` |
| `ak_tender.azure_tenant_id` | Azure Tenant ID | `xxx` |
| `ak_tender.email_user` | Email address to monitor | `your-email@company.com` |

### 3. Required Azure Permissions

Ensure your Azure application has the following Microsoft Graph API permissions:

- `Mail.Read` - Read mail in all mailboxes
- `Mail.ReadWrite` - Read and write mail in all mailboxes

### 4. Security Best Practices

1. **Rotate Secrets Regularly**: Microsoft recommends rotating client secrets every 6 months
2. **Minimum Permissions**: Only grant the permissions your application needs
3. **Monitor Access**: Regularly review Azure AD sign-in logs
4. **Secure Storage**: Never store credentials in:
   - Version control (Git)
   - Plain text files
   - Email or chat messages
   - Screenshots or documentation

### 5. Environment-Specific Configuration

For different environments (development, staging, production):

- Use **different Azure applications** for each environment
- Configure **separate credentials** in each Odoo instance
- Never share credentials between environments

## Troubleshooting

### Token Acquisition Fails

- Verify Client ID, Client Secret, and Tenant ID are correct
- Check if the client secret has expired in Azure Portal
- Ensure the application has the required permissions

### Email Access Denied

- Verify the email address is correct
- Check if the Azure application has Mail.Read permissions
- Ensure the user account exists and is accessible

## Support

For issues related to:
- **Azure configuration**: Contact your Azure administrator
- **Odoo configuration**: Refer to OAUTH2_EMAIL_IMPORT_README.md
- **Module functionality**: Contact Kardan.Digital

---

**Last Updated**: 2025-11-02
**Version**: 1.0