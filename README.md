# SmartRent Dashboard

SmartRent is a rent management dashboard project for landlords and property managers. It started as a frontend prototype and is now being moved into a real Django application with landlord authentication and PostgreSQL-ready configuration.

The system is still under construction, so the current version should be treated as an in-progress product UI rather than a finished application.

The project has now started moving into a real backend implementation using Python, Django, and PostgreSQL-ready configuration, beginning with landlord authentication.

## Preview

The screenshot below shows the current look and feel of the system:

![SmartRent dashboard preview](media/Screenshot%202026-04-10%20at%2015.55.36.png)

## What is in the project so far

The project currently focuses on the landlord-side user interface and dashboard experience while the backend foundation is being built out.

- Multi-page landlord dashboard with dedicated views for overview, properties, tenants, payments, maintenance, analytics, notifications, and settings
- Django templates for landlord pages under `templates/landlord/`
- Reusable styling system with responsive dashboard components
- Shared landlord shell and page behavior consolidated into `static/js/main.js`
- Mock property, tenant, payment, maintenance, and alert data where backend data is not wired yet
- Interactive charts rendered with Chart.js from a CDN
- Sidebar navigation, mobile menu behavior, reveal animations, filters, and metric animations
- Django project scaffold for backend development
- Landlord authentication flow with a protected dashboard
- Demo landlord and tenant accounts for local development

## Landlord pages

- `templates/landlord/overview/index.html`: portfolio overview dashboard
- `templates/landlord/properties/index.html`: main properties dashboard
- `templates/landlord/properties/add_property.html`: property creation and editing flow
- `templates/landlord/properties/property_detail.html`: property detail page
- `templates/landlord/tenants/index.html`: tenant records, renewals, and risk signals
- `templates/landlord/tenants/add_tenant.html`: tenant intake flow
- `templates/landlord/payments/index.html`: rent activity and payment breakdowns
- `templates/landlord/maintenance/index.html`: ticket tracking and vendor performance
- `templates/landlord/analytics/index.html`: portfolio analytics and benchmark insights
- `templates/landlord/notifications/index.html`: alerts, communication feed, and automation rules
- `templates/landlord/settings/index.html`: integrations, access roles, and platform settings

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
├── manage.py
├── requirements.txt
├── static/
├── templates/
└── README.md
```

## How it works

Landlord pages now live in Django templates under `templates/landlord/`, organized by page folder.

- shared shell pieces like the sidebar and session banner are included from template partials
- each landlord section has its own folder with an `index.html` entry page
- related pages stay in the same folder as the section they belong to, for example the properties folder contains its main page, add page, and detail page
- shared interactions and page behavior live in `static/js/main.js`
- some areas already use live Django data, especially landlord authentication and property management

## Running the project

Run the Django landlord flow:

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

Then open `http://127.0.0.1:8000/`.

Demo landlord credentials:

- Email: `landlord.demo@smartrent.local`
- Password: `DemoPass123!`

## Current limitations

This project is still under construction, so a few things are not implemented yet:

- only part of the landlord flow is database-driven today
- tenant-side authentication and tenant-facing pages are not built yet
- several sections still use mock operational data
- no live API integrations
- PostgreSQL is planned, but local development can still fall back to SQLite

## Good next steps

- connect the dashboard to a real backend and database
- add authentication for landlords, managers, and staff
- implement real property, tenant, and payment management workflows
- replace remaining page-level mock data with API-driven or model-driven data
- continue splitting landlord functionality into smaller Django views, templates, and modules

## Summary

So far, SmartRent is a strong landlord-side dashboard foundation with real Django structure, authentication, and live property management beginning to replace the original prototype. It is still under construction, and the next phase is turning the remaining mock sections into fully model-driven workflows.
