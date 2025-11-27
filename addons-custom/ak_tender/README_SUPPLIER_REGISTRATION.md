# Supplier Registration Module

## Overview

This module provides a complete online supplier registration system integrated into the `ak_tender` module. It allows potential suppliers to register through a public website form with a token-based draft system, enabling them to save and resume their applications.

## Features

### 1. **Token-Based Draft System**
- Suppliers can start an application and save it as a draft
- Unique access token (UUID) generated for each application
- Draft link sent via email for later resumption
- Applications can be completed over multiple sessions

### 2. **Multi-Language Support (TR/EN)**
- All forms and emails support both Turkish and English
- Automatic language detection based on user preferences
- Bilingual email templates

### 3. **Complete Information Collection**
- Company information (name, VAT, tax office, MERSIS, KEP)
- Contact person details
- Payment terms and banking information (TRY, USD, EUR IBANs)
- Product/Service categories
- Required document uploads:
  - Tax Certificate (Vergi Levhası)
  - Signature Circular (İmza Sirküleri)
  - Trade Registry Gazette (Ticari Sicil Gazetesi)
  - Bank Information on Stamped Letterhead (IBAN Bilgisi - Antetli)

### 4. **Workflow States**
- **Draft**: Application in progress, editable via token
- **Submitted**: Application completed and sent for review
- **Under Review**: Being reviewed by procurement team
- **Approved**: Application approved, partner and portal user created
- **Rejected**: Application rejected with reason

### 5. **Automated Actions**
- Email notifications at each workflow stage
- Automatic partner (`res.partner`) creation upon approval
- Portal user creation with welcome email
- Procurement team notifications for new submissions

## Technical Architecture

### Models

#### `supplier.application`
Main model storing all supplier application data with the following key fields:
- `access_token`: Unique UUID for draft access
- `state`: Workflow state (draft/submitted/under_review/approved/rejected)
- `partner_id`: Link to created partner after approval
- Company and contact information fields
- Document binary fields for uploads
- Banking and payment information

#### `res.partner` (Extended)
- `supplier_application_id`: Link back to original application
- `supplier_application_date`: Application submission date

### Controllers

#### `/supplier/register`
Public form for new supplier registration

#### `/supplier/application/<token>`
Resume existing draft application via unique token

#### `/supplier/application/save`
Save or submit application (POST)

### Security

- **Public Access**: Draft applications accessible via token
- **Manager Access**: Full CRUD for procurement managers
- **User Access**: Read-only for procurement users
- Record rules enforce proper access control

### Email Templates

1. **Draft Link** (`email_template_supplier_application_draft_link`)
   - Sent when application is saved as draft
   - Contains unique link to resume

2. **Submission Confirmation** (`email_template_supplier_application_confirmation`)
   - Sent to supplier upon

 successful submission
   - Confirms receipt and provides application number

3. **Procurement Notification** (`email_template_supplier_application_submitted`)
   - Sent to procurement team when new application submitted
   - Includes all application details and review link

4. **Rejection Notice** (`email_template_supplier_application_rejected`)
   - Sent when application is rejected
   - Includes rejection reason

### Views

- **List View**: Overview of all applications with status badges
- **Form View**: Detailed application review with workflow buttons
- **Kanban View**: Visual pipeline grouped by state
- **Website Form**: Public registration form with all required fields

## User Workflows

### Supplier Workflow

1. **Start Application**
   - Visit `/supplier/register`
   - Fill in basic company information
   - Provide contact email

2. **Save Draft**
   - Click "Save as Draft" button
   - Receive email with unique continuation link
   - Can close and return later

3. **Complete Application**
   - Fill all required fields
   - Upload required documents
   - Click "Submit Application"
   - Receive confirmation email

4. **Wait for Review**
   - Procurement team reviews application
   - Receive approval or rejection notification

5. **Upon Approval**
   - Receive portal access welcome email
   - Can log in and start business

### Procurement Team Workflow

1. **Receive Notification**
   - Get email when new application submitted
   - View application in "Supplier Applications" menu

2. **Review Application**
   - Open application in Odoo
   - Review all information and documents
   - Add internal notes if needed

3. **Take Action**
   - **Start Review**: Change to "Under Review" status
   - **Approve**: Creates partner + portal user, sends welcome email
   - **Reject**: Provide reason, sends rejection email

## Installation & Configuration

### Prerequisites
- Odoo 18 CE
- `ak_tender` module installed
- Mail server configured for email notifications

### Installation Steps

1. **Update Module**
   ```bash
   cd /opt/odoo18
   ./odoo-bin -c odoo.conf -u ak_tender -d your_database
   ```

2. **Verify Installation**
   - Check "Supplier Applications" menu under Purchases
   - Visit `/supplier/register` on your website
   - Test email configuration

### Configuration

1. **Email Settings**
   - Configure outgoing mail server in Settings > Technical > Email > Outgoing Mail Servers
   - Verify base URL in Settings > General Settings > Web Base URL

2. **User Groups**
   - Procurement managers: `ak_tender.group_tender_manager`
   - Procurement users: `ak_tender.group_tender_user`

3. **Customize Email Templates**
   - Navigate to Settings > Technical > Email > Templates
   - Edit supplier application templates as needed

## Menu Structure

```
Purchases
└── Supplier Applications
    ├── All Applications (Kanban/List/Form)
    └── Filter: Pending Review (default)
```

## Data Files

- `data/supplier_application_sequence.xml`: Application number sequence (SUP/APP/00001)
- `data/supplier_application_mail_templates.xml`: All email templates
- `security/ir.model.access.csv`: Access rights
- `security/security_rules.xml`: Record rules

## URLs

- **Public Registration**: `/supplier/register`
- **Resume Application**: `/supplier/application/{token}`
- **Backend Access**: `Purchases > Supplier Applications`

## Customization

### Adding Custom Fields

1. Edit `models/supplier_application.py`
2. Add field to model
3. Update `views/supplier_application_views.xml` (backend form)
4. Update `views/supplier_registration_templates.xml` (website form)
5. Update `controllers/supplier_application.py` (_prepare_application_values)

### Modifying Workflow

Edit the workflow methods in `models/supplier_application.py`:
- `action_submit()`: Submission logic
- `action_approve()`: Approval logic
- `action_reject()`: Rejection logic

### Custom Validations

Add validation methods decorated with `@api.constrains()` in the model.

## Best Practices

1. **VAT Number Validation**: System checks for duplicate VAT numbers
2. **Email Validation**: Basic email format validation included
3. **Document Management**: Documents stored as binary fields with filenames
4. **Token Security**: UUIDs ensure unique, hard-to-guess access tokens
5. **Audit Trail**: All state changes tracked via Odoo's mail/activity system

## Troubleshooting

### Issue: Draft link email not received
- Check mail server configuration
- Verify contact email is valid
- Check Odoo logs for email sending errors

### Issue: Cannot access website form
- Verify website module is installed
- Check if route is registered (`/supplier/register`)
- Ensure module is properly installed and updated

### Issue: Approval doesn't create partner
- Check user has necessary permissions
- Verify `res.partner` model access rights
- Check for duplicate VAT number constraints

## Future Enhancements

Potential improvements for consideration:
- [ ] MERSIS API validation
- [ ] Automatic duplicate supplier detection
- [ ] Document OCR for auto-filling
- [ ] Multi-step wizard form
- [ ] Supplier scoring/rating system
- [ ] Integration with external vendor databases
- [ ] Advanced analytics dashboard

## Support

For issues or questions:
- Check Odoo logs: `/var/log/odoo/odoo.log`
- Review application state in backend
- Verify email template configuration
- Check security groups and access rights

## Version History

- **v1.0** (2025-11-27): Initial release
  - Token-based draft system
  - Multi-language support (TR/EN)
  - Complete workflow with email notifications
  - Document upload support
  - Portal user auto-creation

## License

LGPL-3 (same as ak_tender module)