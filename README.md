# SmartRent

SmartRent is a rent and property management system being built with Python, Django, and PostgreSQL-ready configuration.

The system is still under construction. What exists now is no longer just a static prototype: it is an in-progress Django application with working landlord and tenant authentication, live billing flows, maintenance tracking, and event-based notifications.

## Live Demo

- [https://smartrent-ke.onrender.com](https://smartrent-ke.onrender.com)

## Preview

The screenshot below shows the current look and feel of the system:

![SmartRent dashboard preview](media/Screenshot%202026-04-10%20at%2015.55.36.png)

## Current Product Scope

SmartRent currently includes two main workspaces:

- `Landlord side`
- `Tenant side`

### Landlord side

Implemented landlord workflows currently include:

- login and protected landlord dashboard
- live overview page with portfolio signals and action cards
- property creation with unit mix, renting price, and buying price
- unit generation per property using house numbers like `House 1`, `House 2`
- tenant creation, editing, viewing, and deletion
- automatic tenant login account creation
- bills management with live balances
- payment recording and cash payment approval
- maintenance complaint handling with status updates
- maintenance expense records linked to complaints
- tenant-responsible repair bills
- live analytics page
- persistent landlord settings
- live notifications inbox

### Tenant side

Implemented tenant workflows currently include:

- tenant login through the shared authentication page
- tenant overview page
- receipts and payments workspace
- multi-bill payment selection flow
- rent prepayment support
- cash, M-Pesa, and card payment paths
- lease extension requests
- profile editing
- complaint logging and complaint detail tracking
- autopay settings for rent bills only
- analytics page
- live notifications inbox

## Key Behaviors Already Working

- automatic rent billing for rental tenants every 30 days from the rent schedule anchor
- rent prepayment stored as rent credit and applied on due date
- non-rent overpayment stored as current balance
- payment allocations tracked against specific bills
- bill balances update after partial, full, and over-payments
- cash payments stay pending until landlord approval
- complaint status changes reflect back on the tenant side
- maintenance expenses only create tenant bills when the cost bearer is `Tenant`
- notifications are stored and shown per user with read and unread state

## Notification System

SmartRent now has a real event-based notification system.

Landlords receive notifications for events such as:

- new complaint submitted
- cash payment awaiting approval
- tenant payment confirmed
- lease extension request submitted
- automatic rent charge created

Tenants receive notifications for events such as:

- new bill added
- payment confirmed
- cash payment submitted
- complaint logged
- complaint status updated
- lease extension submitted, approved, or declined
- password change reminder
- autopay enabled or disabled
- rent due soon

## Tech Stack

- Python
- Django
- PostgreSQL-ready configuration
- SQLite fallback for local development
- HTML templates
- CSS
- Vanilla JavaScript
- [Chart.js](https://www.chartjs.org/) via CDN
- [Font Awesome](https://fontawesome.com/) via CDN
- Google Fonts (`Manrope` and `Sora`)

## Project Structure

```text
Rent_management/
├── accounts/
│   ├── migrations/
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── config/
├── media/
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── accounts/
│   ├── landlord/
│   └── tenant/
├── manage.py
├── requirements.txt
└── README.md
```

## Template Organization

Landlord and tenant pages are organized by page folder.

Examples:

- `templates/landlord/properties/index.html`
- `templates/landlord/properties/add_property.html`
- `templates/landlord/properties/property_detail.html`
- `templates/landlord/tenants/index.html`
- `templates/tenant/receipts/index.html`
- `templates/tenant/complaints/detail.html`

Shared behavior is handled in:

- `static/js/main.js`
- `static/css/style.css`

## Main Pages

### Landlord templates

- `templates/landlord/overview/index.html`
- `templates/landlord/properties/index.html`
- `templates/landlord/tenants/index.html`
- `templates/landlord/payments/index.html`
- `templates/landlord/bills/index.html`
- `templates/landlord/maintenance/index.html`
- `templates/landlord/analytics/index.html`
- `templates/landlord/notifications/index.html`
- `templates/landlord/settings/index.html`

### Tenant templates

- `templates/tenant/overview/index.html`
- `templates/tenant/receipts/index.html`
- `templates/tenant/profile/index.html`
- `templates/tenant/complaints/index.html`
- `templates/tenant/notifications/index.html`
- `templates/tenant/analytics/index.html`
- `templates/tenant/settings/index.html`

## Running The Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
python3 manage.py migrate
```

Seed demo accounts:

```bash
python3 manage.py seed_demo_accounts
```

Start the development server:

```bash
python3 manage.py runserver 127.0.0.1:8000
```

Open:

- [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- [https://smartrent-ke.onrender.com](https://smartrent-ke.onrender.com)

## Demo Credentials

### Landlord

- Email: `landlord.demo@smartrent.local`
- Password: `DemoPass123!`

### Tenant

Tenant accounts are generated from the landlord side when a tenant is created.

- Username: tenant email
- Default password format: `Property-Name-House-Number`
- Example: `Phenom-Park-House-13`

Tenants are prompted to change that password from their settings page after login.

## Current Limitations

The system is still under construction, and a few areas are still evolving:

- notifications are live, but more filtering and delivery-channel logic can still be added
- no real external payment gateway integration yet; card and M-Pesa are currently test-mode flows
- no background worker yet; some recurring actions are request-driven
- PostgreSQL is the intended main database, but local development can still use SQLite
- some older templates, like `templates/landlord/dashboard.html`, remain in the repo as legacy leftovers and are not part of the primary flow

## Recent Progress Snapshot

Recent major milestones already implemented:

- Phase 1: financial trust
  - live bill balances
  - payment allocation ledger
  - bill detail views
- Phase 2: operational workflows
  - lease extension review flow
  - live landlord overview
- Phase 3: management intelligence
  - live landlord analytics
  - persistent landlord settings
- Phase 4: tenant self-service polish
  - editable tenant profile
  - improved receipts and complaint tracking
  - live notification system

## Summary

SmartRent is now an active Django product foundation for landlord and tenant workflows, not just a UI mockup. It already supports authentication, property and tenant setup, live billing, complaints, maintenance cost handling, approvals, analytics, settings, and notifications, while still being under construction as the system moves toward fuller production readiness.
