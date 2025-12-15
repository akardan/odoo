# Digital Certificates & Badges

## Overview

**Digital Certificates & Badges** is a comprehensive Odoo 18 module for managing and issuing digital certificates and Open Badges. The module is fully compliant with [Open Badges 2.0 Specification](https://www.imsglobal.org/sites/default/files/Badges/OBv2p0Final/index.html) and provides a complete solution for creating, issuing, and verifying digital credentials.

![Version](https://img.shields.io/badge/version-18.0.1.0-blue)
![License](https://img.shields.io/badge/license-LGPL--3-green)
![Odoo](https://img.shields.io/badge/Odoo-18.0%20CE-purple)

**Author:** Kardan.Digital  
**Website:** [https://kardan.digital](https://kardan.digital)

---

## Digital Certificates vs. Traditional Certificates

### Traditional (Paper) Certificates:
- 📄 Printed as physical documents and stored
- ✋ Delivered in person or sent by mail
- 📦 Requires physical storage and can deteriorate over time
- ❌ Can be lost, torn, or tampered with
- 🕐 Verification is difficult and time-consuming
- 💰 High costs for printing, paper, and shipping
- 🌍 Limited sharing and international recognition

### Digital Certificates (This Module):
- 💻 Electronic format (PDF + metadata)
- ⚡ Instantly delivered via email
- ☁️ Stored in the cloud, no physical space required
- 🔒 Protected with cryptographic signatures and secure against fraud
- ✅ Verified in seconds via QR code
- 🆓 Zero printing costs, unlimited copying
- 🌐 Globally shareable with universal recognition through Open Badges 2.0 standard
- 📊 Automatic reporting and tracking
- 🔄 Updateable and revocable
- 🎯 Can be integrated into LinkedIn, digital CVs, and professional platforms

**In Summary:** Digital certificates provide all the functionality of traditional certificates while offering significant advantages in security, verifiability, cost-effectiveness, and accessibility.

---

## Features

### 🏆 Core Functionality
- **Open Badges 2.0 Compliant** - Full compliance with international Open Badges specification
- **Digital Certificate Issuance** - Create and issue professional digital certificates
- **Badge Management** - Design and manage badge templates with custom criteria
- **Multi-language Support** - Primary and secondary language support for certificates
- **Verification System** - QR code-based certificate verification

### 🎯 Badge Management
- **Badge Classes** - Create reusable badge templates with custom criteria
- **Badge Issuers** - Manage issuing organizations with branding and signatures
- **Badge Types** - Categorize badges (Achievement, Participation, Competency, etc.)
- **Badge Tags** - Organize badges with custom tags
- **Badge Alignments** - Link badges to educational frameworks and standards

### 🔐 Security & Verification
- **Cryptographic Signing** - RSA-based digital signatures for badge authenticity
- **QR Code Verification** - Quick verification through QR codes
- **Public Key Infrastructure** - Automatic key pair generation for issuers
- **Hashed Recipient Identities** - Privacy-preserving recipient identification
- **Unique Badge IDs** - UUID-based unique identifiers for each badge

### 📄 Certificate Generation
- **PDF Certificates** - Professional PDF certificate generation
- **Custom Templates** - Multiple certificate templates with custom backgrounds
- **Custom Fonts** - Support for custom TrueType fonts (PT Sans, Pirata One, Ephesis)
- **Dual Signatures** - Support for two-signature certificates
- **Bilingual Certificates** - Support for certificates in two languages

### 🔗 Integration
- **Event Integration** - Issue badges for event participants
- **E-Learning Integration** - Award badges for course completion (website_slides)
- **Contact Management** - Link badges to contacts/partners
- **Email Notifications** - Automated email delivery of certificates

### 📊 Reporting & Management
- **Badge Reports** - Generate reports for issued badges
- **Evidence Tracking** - Attach evidence to badge assertions
- **Activity Tracking** - Full audit trail with mail integration
- **Batch Operations** - Issue certificates to multiple recipients

---

## Installation

### Prerequisites

Ensure the following Odoo modules are installed:
- `base`
- `mail`
- `web`
- `event`
- `website_event`
- `website_slides`
- `contacts`

### Python Dependencies

The module requires the following Python packages:

```bash
pip install cryptography reportlab
```

### Installation Steps

1. Clone or copy the module to your Odoo addons directory:
   ```bash
   cp -r ak_open_badges /opt/odoo18/addons-custom/
   ```

2. Update the addons list:
   - Go to **Apps** menu
   - Click **Update Apps List**
   - Search for "Digital Certificates & Badges"

3. Install the module:
   - Click **Install** on the module card

---

## Configuration

### 1. Configure Badge Issuer

Navigate to **Certificates > Configuration > Issuers**

1. Create a new issuer record
2. Fill in the required information:
   - Name (translatable)
   - Description (translatable)
   - URL (issuer website)
   - Email (contact email)
   - Issuer Logo
   - Issuer Signature (optional)
   - Issuer Title (e.g., "Director", "CEO")

3. Generate cryptographic keys:
   - Click **Generate Key Pair** button to create RSA keys
   - Public key will be used for badge verification
   - Private key is used for signing (restricted to admin)

### 2. Create Badge Types

Navigate to **Certificates > Configuration > Badge Types**

Create categories for your badges (examples included):
- Achievement Badge
- Participation Badge
- Competency Badge
- Certificate of Completion
- Certificate of Achievement

### 3. Create Badge Classes (Templates)

Navigate to **Certificates > Badge Classes**

1. Create a new badge class
2. Configure:
   - **Name** - Badge title (translatable)
   - **Description** - Badge description (translatable)
   - **Badge Type** - Select badge category
   - **Issuer** - Select the issuing organization
   - **Image** - Upload badge image (PNG recommended)
   - **Criteria** - Define criteria for earning the badge
   - **Primary Language** - Main language for the certificate
   - **Secondary Language** - Optional second language
   - **Tags** - Add relevant tags

### 4. Configure Certificate Templates

The module includes pre-configured certificate templates with custom backgrounds and fonts. You can customize templates in:
- [`data/certificate_template.xml`](data/certificate_template.xml:1)

### 5. System Parameters

Configure base URL for proper badge verification:
- Go to **Settings > Technical > Parameters > System Parameters**
- Ensure `web.base.url` is correctly set to your domain

---

## Usage

### Issuing a Badge

#### Manual Issuance

Navigate to **Certificates > Badge Assertions**

1. Click **Create**
2. Select:
   - **Certificate Class** - Badge template to use
   - **Recipient** - Select from contacts/partners
   - **Issue Date** - Defaults to current date
   - **Expiry Date** - Optional expiration
   - **Evidence** - Add supporting evidence (optional)
   - **Language** - Select certificate language

3. Click **Save**
4. Click **Issue Badge** to generate the certificate
5. Click **Send Badge via Email** to notify recipient

#### Batch Issuance

For issuing multiple badges (e.g., course completion):
1. Use the integration with Events or E-Learning modules
2. Configure automation rules for automatic badge issuance
3. Generate badges in bulk from event participants or course completions

### Verifying a Badge

#### QR Code Verification

1. Scan the QR code on the certificate
2. The verification page will display:
   - Badge details
   - Recipient information
   - Issue date and expiry
   - Issuer information
   - Verification status

#### Manual Verification

Navigate to: `https://yourdomain.com/badge/verify/<badge_uid>`

### Viewing Badge Details

Public badge page: `https://yourdomain.com/badge/<badge_uid>`

This page displays:
- Badge class information
- Issue details
- Verification status
- Evidence (if available)
- Open Badges JSON-LD metadata

### Downloading Certificates

Recipients can download their certificates in PDF format:
- From the badge details page
- From the email notification
- Through the partner portal

---

## Technical Details

### Models

#### [`badge.issuer`](models/badge_issuer.py:1)
Manages organizations that issue badges with cryptographic key pairs.

**Key Fields:**
- `name`, `description` - Translatable issuer information
- `url`, `email` - Contact information
- `public_key`, `private_key` - RSA key pair for signing
- `signature`, `image` - Branding assets

#### [`badge.class`](models/badge_class.py:1)
Defines badge templates with criteria and metadata.

**Key Fields:**
- `name`, `description` - Translatable badge information
- `badge_type_id` - Badge category
- `issuer_id` - Issuing organization
- `criteria_url`, `criteria_narrative` - Earning criteria
- `primary_lang`, `secondary_lang` - Language settings

#### [`badge.assertion`](models/badge_assertion.py:1)
Represents issued badges to specific recipients.

**Key Fields:**
- `badge_class_id` - Badge template
- `recipient_id` - Badge recipient (partner)
- `issuance_date`, `expiration_date` - Validity period
- `uid` - Unique badge identifier
- `verification_key` - Cryptographic verification
- `state` - Badge status (draft, issued, revoked)

#### [`badge.type`](models/badge_type.py:1)
Categorizes badges into types.

#### [`badge.tag`](models/badge_tag.py:1)
Provides tagging functionality for badge organization.

#### [`badge.alignment`](models/badge_alignment.py:1)
Links badges to educational frameworks and standards.

#### [`badge.evidence`](models/badge_evidence.py:1)
Attaches supporting evidence to badge assertions.

### Controllers

#### [`main.py`](controllers/main.py:1)
Handles web routes for:
- Badge verification pages
- Public badge display
- QR code generation
- JSON-LD endpoints for Open Badges compliance

### Security

User groups defined in [`security/open_badges_security.xml`](security/open_badges_security.xml:1):
- **Badge User** - Can view badges
- **Badge Manager** - Can create and issue badges
- **Badge Administrator** - Full access including issuer management

Access rights configured in [`security/ir.model.access.csv`](security/ir.model.access.csv:1)

### Reports

PDF certificate generation with:
- Custom backgrounds (pattern templates)
- Custom fonts (TrueType fonts in [`static/fonts/`](static/fonts/))
- QR codes for verification
- Bilingual support
- Dual signatures

Report templates: [`reports/badge_reports.xml`](reports/badge_reports.xml:1)

### Data Files

- [`data/badge_sequence.xml`](data/badge_sequence.xml:1) - Certificate numbering sequences
- [`data/badge_type_data.xml`](data/badge_type_data.xml:1) - Default badge types
- [`data/certificate_template.xml`](data/certificate_template.xml:1) - Certificate templates
- [`data/mail_template_data.xml`](data/mail_template_data.xml:1) - Email templates

### Views

- [`views/badge_issuer_views.xml`](views/badge_issuer_views.xml:1) - Issuer management
- [`views/badge_class_views.xml`](views/badge_class_views.xml:1) - Badge template management
- [`views/badge_assertion_views.xml`](views/badge_assertion_views.xml:1) - Badge issuance
- [`views/templates.xml`](views/templates.xml:1) - Website templates
- [`views/menu_views.xml`](views/menu_views.xml:1) - Menu structure

---

## Open Badges 2.0 Compliance

This module fully implements the Open Badges 2.0 specification:

### JSON-LD Support
All badges include proper JSON-LD metadata accessible at:
- Badge class: `/badge/class/<id>/json`
- Badge assertion: `/badge/<uid>/json`
- Issuer: `/badge/issuer/<id>/json`

### Required Properties
- `@context`: "https://w3id.org/openbadges/v2"
- `type`: Assertion, BadgeClass, or Issuer
- `id`: Unique identifier URL
- `badge`: Link to BadgeClass
- `recipient`: Hashed or plain recipient identity
- `issuedOn`: ISO 8601 datetime
- `verification`: Verification method and signature

### Verification Methods
- Hosted verification (primary method)
- Signed badges with RSA signatures
- Public key verification

---

## Internationalization

The module includes translations for:
- **English** (en_US) - [`i18n/en_US.po`](i18n/en_US.po:1)
- **Turkish** (tr_TR) - [`i18n/tr.po`](i18n/tr.po:1)

All user-facing strings are translatable. Certificates support bilingual output with primary and secondary languages.

---

## Customization

### Custom Certificate Backgrounds

Add custom background images to [`static/src/img/`](static/src/img/) and reference them in certificate templates.

### Custom Fonts

Add TrueType fonts (.ttf) to [`static/fonts/`](static/fonts/) and register them in the certificate generation code.

### Custom Badge Criteria

Define custom criteria in badge classes and implement validation logic in badge assertion models.

### Integration with Other Modules

The module can be extended to integrate with:
- HR modules (employee training certificates)
- Sales (customer certification)
- Projects (project completion badges)
- Custom modules (domain-specific badges)

---

## Troubleshooting

### Certificates Not Generating

1. Verify Python dependencies are installed:
   ```bash
   pip install cryptography reportlab
   ```

2. Check file permissions for font directory
3. Verify base URL is configured correctly

### Verification Not Working

1. Ensure `web.base.url` system parameter is set
2. Check SSL certificate if using HTTPS
3. Verify badge UID is correct

### Email Not Sending

1. Configure outgoing mail server in Odoo
2. Check email template in [`data/mail_template_data.xml`](data/mail_template_data.xml:1)
3. Verify recipient email addresses

---

## License

This module is licensed under **LGPL-3** (GNU Lesser General Public License v3.0)

---

## Credits

**Developer:** Kardan.Digital  
**Email:** info@kardan.digital  
**Website:** https://kardan.digital

### Dependencies
- **Odoo** - Open source ERP platform
- **ReportLab** - PDF generation library
- **Cryptography** - Python cryptography toolkit
- **Open Badges** - IMS Global Learning Consortium specification

---

## Support

For support, bug reports, or feature requests:
- Visit: https://kardan.digital
- Email: info@kardan.digital

---

## Changelog

### Version 18.0.1.0
- Initial release for Odoo 18 CE
- Open Badges 2.0 compliance
- Multi-language certificate support
- QR code verification system
- Event and e-learning integration
- Cryptographic signing of badges
- PDF certificate generation with custom templates

---

## Screenshots

The module includes:
- Modern badge management interface
- Professional certificate templates
- Mobile-friendly verification pages
- Comprehensive reporting dashboards

For screenshots and demos, visit the module on Odoo Apps Store or contact Kardan.Digital.
