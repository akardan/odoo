# CRM Pharma

CRM Pharma is an Odoo module designed specifically for pharmaceutical companies to manage their customer relationships, visits, and promotional activities. It provides a comprehensive solution for tracking interactions with doctors and pharmacies, managing territories, and planning promotional distributions.

## Features

*   **Visit Management:**
    *   Plan and record visits to doctors and pharmacies.
    *   Track visit details, including date, team member, and visit type.
    *   Validate visit dates to ensure they are within a reasonable timeframe (e.g., not too far in the future or past).
    *   Dashboard for analyzing visit statistics by team member and date range.
    *   Daily stats breakdown for doctor and pharmacy visits.

*   **Territory Management:**
    *   Define territories and assign them to specific companies.
    *   Manage "Bricks" (geographic units) within territories.
    *   Link bricks to states and countries.
    *   Organize units within bricks for granular tracking.

*   **Team Management:**
    *   Manage CRM team members and their assignments.
    *   Link team members to specific bricks and territories.

*   **Promotion & Distribution Planning:**
    *   Plan the distribution of promotional materials and samples.
    *   Create distribution plans linked to products and team members.
    *   Automatically generate delivery orders (stock pickings) based on distribution plans.
    *   Group delivery orders by team member for efficient logistics.

*   **Partner Management:**
    *   Classify partners as Doctors or Pharmacies.
    *   Link partners to specific bricks and units.

## Installation

1.  Ensure you have Odoo 18 installed.
2.  Place the `ak_crm` module in your Odoo addons directory.
3.  Install the module via the Odoo Apps menu.
    *   Dependencies: `base`, `crm`, `sales_team`, `contacts`.

## Configuration

1.  **Territories & Bricks:**
    *   Go to the CRM Pharma menu and configure your Territories.
    *   Create Bricks and assign them to Territories.
    *   Define Units within Bricks if necessary.

2.  **Team Members:**
    *   Set up your sales team and assign members.
    *   Link team members to the Bricks they are responsible for.

3.  **Visit Types:**
    *   Define different types of visits (e.g., Routine, promotional, follow-up) in the configuration settings.

## Usage

### Managing Visits

1.  Navigate to the **Visits** menu.
2.  Use the **Create Visit** wizard to plan new visits.
3.  Select the Team Member, Date, and filter partners by Brick or Unit.
4.  The system will help you find relevant partners (Doctors/Pharmacies) based on your criteria.
5.  Record the visit details and save.

### Visit Dashboard

1.  Access the **Visit Dashboard** to view performance metrics.
2.  Filter by date range or active period.
3.  View daily statistics for visits, including counts for doctors and pharmacies.

### Promotion Distribution

1.  Go to the **Promotion Distribution Plan** menu.
2.  Create a new plan specifying the Product, Quantity, and Team Member.
3.  Once the plan is finalized, use the "Create Delivery Order" action to generate the necessary stock moves for sample distribution.

## Technical Details

*   **Models:**
    *   `crm.visit`: Core model for storing visit data.
    *   `crm.visit.transient`: Helper model for creating visits.
    *   `crm.territory`: Manages geographic territories.
    *   `crm.brick`: Represents a subdivision of a territory.
    *   `crm.promotion.distribution.plan`: Manages sample distribution planning.
*   **Security:**
    *   Includes security rules and access rights (CSV and XML) to control user access to different features.

## Author

**Atila Kardan**
Website: [https://kardan.digital/app/crm](https://kardan.digital/app/crm)

## License

LGPL-3
