# SmartRent Dashboard

SmartRent is a frontend-only rent management dashboard prototype for landlords and property managers. It presents a polished multi-page interface for monitoring properties, tenants, payments, maintenance, analytics, notifications, and system settings using realistic mock data.

The system is still under construction, so the current version should be treated as an in-progress product UI rather than a finished application.

The project has now started moving into a real backend implementation using Python, Django, and PostgreSQL-ready configuration, beginning with landlord authentication.

## Preview

The screenshot below shows the current look and feel of the system:

![SmartRent dashboard preview](media/Screenshot%202026-04-10%20at%2015.55.36.png)

## What is in the project so far

The project currently focuses on the user interface and dashboard experience rather than backend functionality.

- Multi-page dashboard with dedicated views for overview, properties, tenants, payments, maintenance, analytics, notifications, and settings
- Shared layout and rendering logic powered by a single JavaScript file
- Reusable styling system with responsive dashboard components
- Mock property, tenant, payment, maintenance, and alert data
- Interactive charts rendered with Chart.js from a CDN
- Sidebar navigation, mobile menu behavior, reveal animations, filters, and metric animations
- Django project scaffold for backend development
- Landlord authentication flow with a protected dashboard
- Demo landlord and tenant accounts for local development

## Pages

- `index.html`: portfolio overview dashboard
- `properties.html`: property performance, occupancy, and unit mix
- `tenants.html`: tenant records, renewals, and risk signals
- `payments.html`: rent activity and payment breakdowns
- `maintenance.html`: ticket tracking and vendor performance
- `analytics.html`: portfolio analytics and benchmark insights
- `notifications.html`: alerts, communication feed, and automation rules
- `settings.html`: integrations, access roles, and platform settings

## Tech stack

- HTML5
- CSS3
- Vanilla JavaScript
- Python
- Django
- PostgreSQL-ready database configuration
- [Chart.js](https://www.chartjs.org/) loaded via CDN
- [Font Awesome](https://fontawesome.com/) loaded via CDN
- Google Fonts (`Manrope` and `Sora`)

## Project structure

```text
Rent_management/
├── accounts/
├── config/
├── index.html
├── properties.html
├── tenants.html
├── payments.html
├── maintenance.html
├── analytics.html
├── notifications.html
├── settings.html
├── manage.py
├── requirements.txt
├── static/
├── style.css
├── templates/
├── script.js
└── README.md
```

## How it works

Each HTML page sets a `data-page` value on the `<body>`. The shared `script.js` file reads that value and:

- builds the sidebar and page header
- injects the correct dashboard content for that page
- fills cards, tables, and lists using mock data arrays
- initializes charts, animations, filters, and UI interactions

This means most of the app behavior currently lives in `script.js`, while `style.css` contains the visual design system for the full dashboard.

## Running the project

The repo now has two ways to explore it:

### Option 1: Open the static prototype directly

Open [index.html](/Users/aliceakinyiolango/Documents/GitHub/Rent_management/index.html) in a browser.

### Option 2: Run the Django landlord auth flow

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your environment variables for PostgreSQL using `.env.example`, or run locally with the default SQLite fallback during early development.

Apply migrations:

```bash
python3 manage.py migrate
```

Seed the demo accounts:

```bash
python3 manage.py seed_demo_accounts
```

Start the server:

```bash
python3 manage.py runserver
```

Then open `http://127.0.0.1:8000/auth/login/`.

Demo landlord credentials:

- Email: `landlord.demo@smartrent.local`
- Password: `DemoPass123!`

## Current limitations

This project is still under construction and currently works as an interface prototype, so a few things are not implemented yet:

- no backend or database
- landlord auth is started, but the full application is not yet database-driven
- tenant-side authentication and tenant-facing pages are not built yet
- no form submission or persistent CRUD actions
- no live API integrations
- all metrics, tables, alerts, and charts use hard-coded sample data

## Good next steps

- connect the dashboard to a real backend and database
- add authentication for landlords, managers, and staff
- implement real property, tenant, and payment management workflows
- replace mock arrays in `script.js` with API-driven data
- add tests and improve maintainability by splitting `script.js` into smaller modules

## Summary

So far, SmartRent is a well-designed static dashboard prototype that demonstrates the product direction and user experience for a rent management platform. It already has strong visual structure and page coverage, but it is still under construction and the next phase is turning the mock interface into a real working application.
