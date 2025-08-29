# AK Exams - Exam Management System

## 📋 Overview

**AK Exams** is a comprehensive exam management system built for Odoo 18 CE that provides enterprise-grade survey and examination capabilities with advanced security features, API integration, and multi-company support.

## ✨ Key Features

### 🎯 Core Functionality
- **Company-based Isolation**: Complete data separation between companies
- **Advanced Survey Management**: Enhanced Odoo survey module with custom features
- **Excel Import/Export**: Bulk import of questions, participants, and responses
- **Real-time Monitoring**: Live exam session tracking and analytics

### 🔒 Security & Anti-Cheating
- **Fullscreen Mode Enforcement**: Automatic fullscreen detection and enforcement
- **Tab Switching Detection**: Monitors and logs tab/window switches
- **Developer Tools Detection**: Prevents unauthorized debugging tools
- **Print Screen Monitoring**: Tracks print screen attempts
- **Session Termination**: Automatic termination for security violations

### 🔗 API Integration
- **REST API Endpoints**: Complete API for external system integration
- **Organization Sync**: Automated team and department synchronization
- **User Management**: Bulk user creation and updates via API
- **Exam Access Control**: Secure exam link generation and distribution

### 📊 Question Management
- **Poll Templates**: Reusable question templates with categories
- **Bulk Import**: Excel-based question and answer import
- **Category Management**: Hierarchical question categorization
- **Scoring System**: Flexible scoring with correct answer validation

### 👥 Team & User Management
- **CRM Integration**: Seamless integration with Odoo CRM teams
- **External ID Support**: Integration with external systems
- **Hierarchy Management**: Team hierarchy and reporting structure
- **Role-based Access**: Granular permissions and access control

## 🏗️ Architecture

### Models Overview
- **`survey.survey`**: Enhanced survey management with company isolation
- **`survey.question.poll`**: Question poll templates with options
- **`survey.question.poll.category`**: Question categorization system
- **`crm.team`**: Extended CRM teams with external ID support
- **`survey.user_input`**: Enhanced user responses with security tracking

### API Endpoints
```
GET  /api/v1/system/status          # System health check
POST /api/v1/organization/sync      # Organization structure sync
POST /api/v1/users/sync             # User synchronization
POST /api/v1/exams/access           # Generate exam access links
```

## 🚀 Installation

### Prerequisites
- Odoo 18.0 Community Edition
- Python 3.8+
- Required Python packages:
  - `openpyxl` (for Excel import functionality)

### Installation Steps
1. **Clone or download** the addon to your Odoo addons directory:
   ```bash
   cd /opt/odoo18/addons-custom/
   git clone <repository-url> ak_exams
   ```

2. **Install Python dependencies**:
   ```bash
   pip install openpyxl
   ```

3. **Update Odoo configuration**:
   Add `ak_exams` to your `addons_path` in `odoo.conf`

4. **Restart Odoo service**:
   ```bash
   sudo systemctl restart odoo
   ```

5. **Install the module**:
   - Go to **Apps** → **Update Apps List**
   - Search for "AK Exams"
   - Click **Install**

## ⚙️ Configuration

### API Key Setup
1. Navigate to **Settings** → **Users & Companies** → **Users**
2. Select a user and go to **API Keys** tab
3. Generate a new API key with scope `ak_exams`

### Company Configuration
1. Ensure proper company setup in **Settings** → **Users & Companies** → **Companies**
2. Configure company-specific settings for data isolation

### Security Settings
Configure exam security settings:
- Enable/disable fullscreen mode
- Set violation thresholds
- Configure penalty points system

## 📖 Usage Guide

### Creating an Exam
1. **Navigate to Surveys**: Go to **Surveys** → **Surveys**
2. **Create New Survey**: Click **Create** and fill in basic information
3. **Add Questions**: Use the **Questions** tab to add exam questions
4. **Configure Security**: Set security options in the **Options** tab

### Excel Import Process
1. **Prepare Excel File**: Create Excel file with required sheets:
   - `Soru`: Questions and answer options
   - `Yanıt`: Participant responses and correct answers
   - `Katılımcı`: Participant information (optional)
   - `TEAM`: Team/territory data (optional)

2. **Upload File**: In survey form, upload the Excel file
3. **Import Data**: Click **Import from Excel** button
4. **Review Results**: Check import summary and resolve any errors

### API Integration
#### Organization Synchronization
```bash
curl -X POST https://your-odoo.com/api/v1/organization/sync \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '[
    {
      "unit_id": "SALES001",
      "unit_name": "Sales Department",
      "parent_unit_id": null
    }
  ]'
```

#### User Synchronization
```bash
curl -X POST https://your-odoo.com/api/v1/users/sync \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '[
    {
      "user_id": "EMP001",
      "user_email": "john.doe@company.com",
      "user_full_name": "John Doe",
      "unit_id": "SALES001"
    }
  ]'
```

#### Exam Access Generation
```bash
curl -X POST https://your-odoo.com/api/v1/exams/access \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_id": "EMP001",
    "exam_id": "survey_123"
  }'
```

## 📊 Excel Import Format

### Required Sheets

#### 1. Soru (Questions) Sheet
| Column | Description | Required |
|--------|-------------|----------|
| Soru | Question text | Yes |
| A | Answer option A | Yes |
| B | Answer option B | Yes |
| C | Answer option C | Yes |
| D | Answer option D | Yes |
| Kategori | Question category | No |
| ID | Question ID | No |

#### 2. Yanıt (Answers) Sheet
| Column | Description | Required |
|--------|-------------|----------|
| Katılımcı | Participant name | Yes |
| Takım | Team name | No |
| Kategori | Category | No |
| Soru | Question text | Yes |
| Yanıt | Answer (a, b, c, d) | Yes |
| Doğru mu | Is correct (1 = correct) | Yes |

#### 3. Katılımcı (Participants) Sheet (Optional)
| Column | Description | Required | Format |
|--------|-------------|----------|--------|
| Katılımcı | Participant name | Yes | Text |
| Takım | Team name | No | Text |
| Başlama Zamanı | Start time | **Required for import** | YYYY-MM-DD HH:MM:SS |
| Bitirme Zamanı | End time | No | YYYY-MM-DD HH:MM:SS |
| Puan | Score | No | Number (0-100 for percentage, or raw score) |

**Important Notes**:
- **Başlama Zamanı (Start Time) is now required** for participants to be imported. Participants without a start time will be completely skipped during import.
- The "Puan" column can contain either:
  - **Percentage scores** (0-100): Will be used directly as the final percentage
  - **Raw scores** (>100): Will be automatically converted to percentage based on expected total (25 questions × 4 points = 100 points)

## 🔐 Security Features

### Violation Types
- **Fullscreen Violations**: Exiting fullscreen mode during exam
- **Tab Switching**: Switching between browser tabs/windows
- **Developer Tools**: Opening browser developer tools
- **Print Screen**: Attempting to capture screen content

### Penalty System
- Configurable penalty points for each violation type
- Automatic session termination based on violation thresholds
- Exclusion from statistics for terminated sessions

## 👥 User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Survey Manager** | Full access to surveys, questions, and analytics |
| **Survey User** | Can participate in surveys and view results |
| **Portal User** | Limited access for external participants |

## 🛠️ Technical Details

### Dependencies
- `base`: Odoo base module
- `survey`: Odoo survey module
- `crm`: Odoo CRM module
- `mail`: Odoo mail module
- `website`: Odoo website module

### Database Tables
- `survey_survey`: Extended survey table
- `survey_question_poll`: Question poll templates
- `survey_question_poll_category`: Question categories
- `crm_team`: Extended CRM teams
- `survey_user_input`: Enhanced user responses

### Key Files Structure
```
ak_exams/
├── __init__.py                 # Module initialization
├── __manifest__.py            # Module manifest
├── controllers/               # Web controllers
│   ├── sync_controller.py     # API endpoints
│   └── survey_main_controller.py
├── models/                    # Data models
│   ├── survey_survey.py       # Enhanced survey model
│   ├── survey_question_poll.py # Poll templates
│   └── crm_team.py           # Extended CRM teams
├── security/                  # Access control
│   ├── ir.model.access.csv   # Model permissions
│   └── survey_security.xml   # Security rules
├── views/                     # UI views
│   ├── views.xml             # Main views
│   └── survey_exam_features_view.xml
├── data/                      # Default data
│   ├── ir_default_data.xml   # Default settings
│   └── survey_question_poll_category_data.xml
└── static/                    # Static assets
    ├── src/
    │   ├── js/               # JavaScript files
    │   ├── scss/             # Stylesheets
    │   └── css/              # CSS files
    └── description/          # Module description
```

## 🔧 Customization

### Adding Custom Fields
1. Extend existing models in `models/` directory
2. Update corresponding views in `views/` directory
3. Add access rules in `security/` directory

### Custom API Endpoints
1. Add new methods to `SyncController` class
2. Implement proper authentication and validation
3. Update API documentation

### Security Enhancements
1. Modify violation detection in `survey_security_controller.py`
2. Adjust penalty calculations in `survey_user_input.py`
3. Configure security settings in survey forms

## 📈 Monitoring & Analytics

### Available Metrics
- **Participation Rates**: Track survey completion rates
- **Security Violations**: Monitor cheating attempts
- **Performance Analytics**: Response times and patterns
- **Team Performance**: Comparative analysis by teams

### Reporting
- Built-in Odoo reporting system integration
- Custom dashboards for exam analytics
- Export capabilities for external analysis

## 🐛 Troubleshooting

### Common Issues

#### Excel Import Errors
- **Issue**: "openpyxl library not found"
- **Solution**: Install with `pip install openpyxl`

#### Incorrect Scoring Percentage Display
- **Issue**: Participant scores show incorrect percentages (e.g., 10.50 instead of 84.00)
- **Solution**: This was a known issue in versions prior to the fix. The system now automatically converts raw scores to percentages during import. If you encounter this issue:
  1. Re-import the Excel file with the updated code
  2. The system will detect raw scores (>100) and convert them to percentages
  3. Raw score 84/100 = 84.00% (21 correct answers × 4 points each)

#### Participants Not Imported
- **Issue**: Some participants from the Excel file are not appearing in the survey results
- **Solution**: Check if the participants have a "Başlama Zamanı" (Start Time) in the Katılımcı sheet. Participants without a start time are automatically skipped during import to ensure data integrity.

#### API Authentication Errors
- **Issue**: "Invalid API key"
- **Solution**: Verify API key scope and validity

#### Permission Errors
- **Issue**: "Access denied"
- **Solution**: Check user roles and group assignments

### Debug Mode
Enable debug mode for detailed logging:
```python
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This module is licensed under the LGPL-3 License. See the LICENSE file for details.

## 📞 Support

For support and questions:
- **Email**: support@kardan.digital
- **Website**: https://kardan.digital
- **Documentation**: [Full Documentation](https://docs.kardan.digital/ak-exams)

## 🏷️ Version History

### v18.0.1.0 (Current)
- Initial release for Odoo 18
- Company-based data isolation
- Advanced security features
- REST API integration
- Excel import functionality
- Multi-language support (Turkish/English)

---

**Developed with ❤️ by [Kardan.Digital](https://kardan.digital)**