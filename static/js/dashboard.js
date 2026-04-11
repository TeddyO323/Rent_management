const currentPage = document.body.dataset.page || "overview";

const navItems = [
  { key: "overview", label: "Overview", href: "/landlord/overview/", icon: "fa-chart-line" },
  { key: "properties", label: "Properties", href: "/landlord/properties/", icon: "fa-building" },
  { key: "tenants", label: "Tenants", href: "/landlord/tenants/", icon: "fa-users" },
  { key: "payments", label: "Rent Payments", href: "/landlord/payments/", icon: "fa-wallet" },
  { key: "maintenance", label: "Maintenance", href: "/landlord/maintenance/", icon: "fa-screwdriver-wrench" },
  { key: "analytics", label: "Analytics", href: "/landlord/analytics/", icon: "fa-chart-pie" },
  { key: "notifications", label: "Notifications", href: "/landlord/notifications/", icon: "fa-bell" },
  { key: "settings", label: "Settings", href: "/landlord/settings/", icon: "fa-gear" }
];

const routeMap = Object.fromEntries(navItems.map((item) => [item.key, item.href]));

const pageConfigs = {
  overview: {
    eyebrow: "Smart Rent Platform",
    title: "Operate your entire portfolio from one polished workspace.",
    tagline: "Track cash flow, occupancy, maintenance response times, and smart alerts across every building in real time.",
    searchPlaceholder: "Search tenants, units, or buildings",
    secondaryAction: { label: "Add Property", icon: "fa-plus" },
    primaryAction: { label: "Record Payment", icon: "fa-receipt" },
    hero: {
      label: "Premium dashboard snapshot",
      title: "Portfolio health is trending up with stronger collections and fewer unresolved issues.",
      description: "SmartRent surfaces the next best action for landlords before revenue risk grows. Every number on this page is wired to realistic mock data for a portfolio view that feels production-ready.",
      chips: [
        { value: "174 Units", label: "Across 5 active properties" },
        { value: "93.6%", label: "On-time payment adherence" },
        { value: "4.1 hrs", label: "Avg. first-response time" }
      ],
      spotlights: [
        {
          label: "Net collection pace",
          value: "91.1%",
          text: "Expected rent is being recovered at a healthy pace this month thanks to autopay and early follow-ups."
        },
        {
          label: "Vacancy watch",
          value: "2 buildings",
          text: "Skyline Suites and Bluehaven Apartments need targeted leasing attention this week."
        }
      ]
    }
  },
  properties: {
    eyebrow: "Portfolio Control",
    title: "Monitor buildings, unit mix, and vacancy risk without losing operational detail.",
    tagline: "Review property health, revenue performance, and leasing exposure across the full portfolio from one dedicated workspace.",
    searchPlaceholder: "Search properties or locations",
    secondaryAction: { label: "Import Units", icon: "fa-file-import" },
    primaryAction: { label: "Add Property", icon: "fa-plus" },
    hero: {
      label: "Property intelligence",
      title: "See which buildings are outperforming and which ones need leasing intervention.",
      description: "This workspace is built for portfolio-level visibility, from occupancy pressure to revenue contribution and unit composition.",
      chips: [
        { value: "5 Properties", label: "Actively managed this month" },
        { value: "152 Occupied", label: "Live leases across the portfolio" },
        { value: "KSh 3.12M", label: "Monthly rent target" }
      ],
      spotlights: [
        {
          label: "Best performer",
          value: "Riverpoint",
          text: "Riverpoint Residenc continues to lead on occupancy and collection pace this cycle."
        },
        {
          label: "Leasing pressure",
          value: "Skyline Suites",
          text: "Occupancy has softened enough to justify a short-term offer and faster broker follow-up."
        }
      ]
    }
  },
  tenants: {
    eyebrow: "Tenant Relationships",
    title: "Keep lease health, renewals, and tenant experience organized in one premium view.",
    tagline: "Track renewal timing, payment posture, and autopay adoption before churn or overdue risk compounds.",
    searchPlaceholder: "Search tenant, unit, or property",
    secondaryAction: { label: "Send Reminder", icon: "fa-paper-plane" },
    primaryAction: { label: "Add Tenant", icon: "fa-user-plus" },
    hero: {
      label: "Tenant operations",
      title: "Retention gets easier when payment signals and lease timing are visible at a glance.",
      description: "This page surfaces upcoming renewals, autopay adoption, and the residents who need the fastest follow-up.",
      chips: [
        { value: "152 Active", label: "Current leaseholders" },
        { value: "68.4%", label: "Autopay enrollment" },
        { value: "18 Renewals", label: "Due within 45 days" }
      ],
      spotlights: [
        {
          label: "Retention opportunity",
          value: "12 tenants",
          text: "Residents with strong payment history are entering renewal season and should receive priority offers."
        },
        {
          label: "Attention needed",
          value: "7 watchlist",
          text: "Late payments and shorter remaining lease terms make this group the highest churn-risk segment."
        }
      ]
    }
  },
  payments: {
    eyebrow: "Collections Desk",
    title: "See every rent transaction, outstanding balance, and collection trend from one page.",
    tagline: "Follow payment momentum, overdue exposure, and settlement mix without leaving the SmartRent command center.",
    searchPlaceholder: "Search payments or tenants",
    secondaryAction: { label: "Export Ledger", icon: "fa-file-export" },
    primaryAction: { label: "Record Payment", icon: "fa-receipt" },
    hero: {
      label: "Cash flow visibility",
      title: "Collection performance is strongest when overdue risk and payment channels stay visible.",
      description: "This page brings expected revenue, received rent, and account-level activity into one focused financial workspace.",
      chips: [
        { value: "KSh 2.84M", label: "Collected this month" },
        { value: "KSh 278K", label: "Outstanding balance" },
        { value: "96.2%", label: "Autopay success rate" }
      ],
      spotlights: [
        {
          label: "Top gain",
          value: "Autopay up",
          text: "Recurring billing now clears most Riverpoint and Cedar Grove payments before the 3rd of the month."
        },
        {
          label: "Collection focus",
          value: "6 overdue",
          text: "Most payment follow-up effort should remain concentrated in Bluehaven and Skyline Suites."
        }
      ]
    }
  },
  maintenance: {
    eyebrow: "Service Ops",
    title: "Coordinate tickets, SLAs, and vendor performance from one maintenance command center.",
    tagline: "Prioritize urgent requests, watch response targets, and keep residents updated on repair status.",
    searchPlaceholder: "Search tickets or units",
    secondaryAction: { label: "Dispatch Vendor", icon: "fa-truck-fast" },
    primaryAction: { label: "New Ticket", icon: "fa-plus" },
    hero: {
      label: "Maintenance workflow",
      title: "Fast response and clean vendor coordination protect both tenant satisfaction and asset value.",
      description: "SmartRent makes it easy to see where repair pressure is building and which teams are handling it well.",
      chips: [
        { value: "14 Open", label: "Active maintenance tickets" },
        { value: "92.4%", label: "SLA hit rate" },
        { value: "1.8 days", label: "Average resolution" }
      ],
      spotlights: [
        {
          label: "Priority pressure",
          value: "5 high-priority",
          text: "High-priority tickets are concentrated in Riverpoint and Skyline Suites this week."
        },
        {
          label: "Vendor strength",
          value: "Kevin Otieno",
          text: "Plumbing tickets continue to close fastest when routed through Kevin's service window."
        }
      ]
    }
  },
  analytics: {
    eyebrow: "Portfolio Analytics",
    title: "Turn operations into clear revenue, occupancy, and risk signals for the whole portfolio.",
    tagline: "Use the analytics page to compare collection pace, occupancy distribution, service load, and forward-looking portfolio insights.",
    searchPlaceholder: "Search metrics or buildings",
    secondaryAction: { label: "Schedule Review", icon: "fa-calendar-days" },
    primaryAction: { label: "Export Report", icon: "fa-file-arrow-down" },
    hero: {
      label: "Decision support",
      title: "Revenue and occupancy trends are easier to act on when every signal is visual and connected.",
      description: "This page is built to feel like a founder-grade reporting surface for landlords, managers, and portfolio owners.",
      chips: [
        { value: "+8.2%", label: "NOI trend" },
        { value: "94.7%", label: "Forecast accuracy" },
        { value: "4.6%", label: "Arrears ratio" }
      ],
      spotlights: [
        {
          label: "Portfolio story",
          value: "Collections rising",
          text: "Expected rent and collected rent are narrowing month over month as automation coverage improves."
        },
        {
          label: "Strategic note",
          value: "Occupancy focus",
          text: "The best short-term win remains reducing vacancy exposure in two underperforming properties."
        }
      ]
    }
  },
  notifications: {
    eyebrow: "Alerts And Reminders",
    title: "Centralize every alert, reminder, and automated follow-up in one operational inbox.",
    tagline: "Stay ahead of overdue rent, vacancy signals, successful payments, and maintenance escalations with smarter notifications.",
    searchPlaceholder: "Search alerts or reminder rules",
    secondaryAction: { label: "Message Tenants", icon: "fa-comment-dots" },
    primaryAction: { label: "Create Alert", icon: "fa-bell" },
    hero: {
      label: "Smart notification center",
      title: "The platform feels truly intelligent when the right signal arrives at the right moment.",
      description: "Alerts are prioritized so teams can move faster on revenue risk, vacancy pressure, and resident communication.",
      chips: [
        { value: "12 Active", label: "Live portfolio alerts" },
        { value: "6 Rules", label: "Automations currently running" },
        { value: "14 Updates", label: "Positive confirmations today" }
      ],
      spotlights: [
        {
          label: "Most urgent",
          value: "Overdue follow-up",
          text: "Two tenants have crossed the 3-day overdue threshold and are now in escalation territory."
        },
        {
          label: "Quiet win",
          value: "Owner digest",
          text: "Weekly owner reports are sending on schedule with no delivery failures this month."
        }
      ]
    }
  },
  settings: {
    eyebrow: "System Settings",
    title: "Control automations, integrations, access, and reporting rules from one polished admin view.",
    tagline: "Tune the operating system behind SmartRent without sacrificing clarity or design quality.",
    searchPlaceholder: "Search settings or integrations",
    secondaryAction: { label: "Manage Access", icon: "fa-user-shield" },
    primaryAction: { label: "Save Preferences", icon: "fa-floppy-disk" },
    hero: {
      label: "Platform configuration",
      title: "A premium dashboard should make operational controls feel as refined as the analytics.",
      description: "This page organizes automation preferences, connected tools, access policy, and reporting cadence in one place.",
      chips: [
        { value: "5 Integrations", label: "Connected systems" },
        { value: "6 Automations", label: "Actively running" },
        { value: "4 Roles", label: "Permission groups" }
      ],
      spotlights: [
        {
          label: "Platform health",
          value: "All systems green",
          text: "Payment, reporting, and communication integrations are healthy with no sync errors detected."
        },
        {
          label: "Next review",
          value: "Friday 8:00 AM",
          text: "Weekly owner reporting and automation audits are scheduled and ready to send."
        }
      ]
    }
  }
};

const baseProperties = [
  {
    name: "Riverpoint Residenc",
    location: "Westlands, Nairobi",
    units: 48,
    revenue: 1020000,
    occupancy: 96,
    status: "High Performing",
    trend: 8.4,
    occupiedUnits: 46
  },
  {
    name: "Maple Court Lofts",
    location: "Kilimani, Nairobi",
    units: 32,
    revenue: 648000,
    occupancy: 91,
    status: "Stable",
    trend: 3.1,
    occupiedUnits: 29
  },
  {
    name: "Skyline Suites",
    location: "Upper Hill, Nairobi",
    units: 18,
    revenue: 326000,
    occupancy: 72,
    status: "Needs Attention",
    trend: -6.2,
    occupiedUnits: 13
  },
  {
    name: "Bluehaven Apartments",
    location: "Syokimau, Nairobi",
    units: 64,
    revenue: 704000,
    occupancy: 81,
    status: "Vacancy Risk",
    trend: -3.8,
    occupiedUnits: 52
  },
  {
    name: "Cedar Grove Villas",
    location: "Karen, Nairobi",
    units: 12,
    revenue: 420000,
    occupancy: 100,
    status: "High Performing",
    trend: 5.7,
    occupiedUnits: 12
  }
];

const serverPropertiesNode = document.getElementById("server-properties-data");
const serverProperties = serverPropertiesNode ? JSON.parse(serverPropertiesNode.textContent) : [];
const properties = [...serverProperties, ...baseProperties];
let propertyViewMode = "grid";

const tenants = [
  {
    name: "Brian Mwangi",
    unit: "R-12",
    property: "Riverpoint Residenc",
    leaseEnd: "Jun 30, 2026",
    status: "Good Standing",
    risk: "Low",
    autopay: true,
    balance: 0
  },
  {
    name: "Naomi Wanjiku",
    unit: "MC-08",
    property: "Maple Court Lofts",
    leaseEnd: "May 18, 2026",
    status: "Renewing Soon",
    risk: "Medium",
    autopay: false,
    balance: 36000
  },
  {
    name: "Daniel Kiptoo",
    unit: "BH-21",
    property: "Bluehaven Apartments",
    leaseEnd: "May 31, 2026",
    status: "Watchlist",
    risk: "High",
    autopay: false,
    balance: 28500
  },
  {
    name: "Irene Achieng",
    unit: "CG-03",
    property: "Cedar Grove Villas",
    leaseEnd: "Sep 12, 2026",
    status: "Good Standing",
    risk: "Low",
    autopay: true,
    balance: 0
  },
  {
    name: "Mohammed Noor",
    unit: "SS-14",
    property: "Skyline Suites",
    leaseEnd: "Apr 28, 2026",
    status: "Watchlist",
    risk: "High",
    autopay: false,
    balance: 34000
  },
  {
    name: "Lucy Njeri",
    unit: "R-34",
    property: "Riverpoint Residenc",
    leaseEnd: "Aug 05, 2026",
    status: "Good Standing",
    risk: "Low",
    autopay: true,
    balance: 0
  }
];

const rentActivity = [
  {
    tenant: "Brian Mwangi",
    unit: "R-12",
    property: "Riverpoint Residenc",
    amount: 42000,
    date: "Mar 28, 2026",
    status: "Paid"
  },
  {
    tenant: "Naomi Wanjiku",
    unit: "MC-08",
    property: "Maple Court Lofts",
    amount: 36000,
    date: "Mar 29, 2026",
    status: "Pending"
  },
  {
    tenant: "Daniel Kiptoo",
    unit: "BH-21",
    property: "Bluehaven Apartments",
    amount: 28500,
    date: "Mar 26, 2026",
    status: "Overdue"
  },
  {
    tenant: "Irene Achieng",
    unit: "CG-03",
    property: "Cedar Grove Villas",
    amount: 45000,
    date: "Mar 27, 2026",
    status: "Paid"
  },
  {
    tenant: "Mohammed Noor",
    unit: "SS-14",
    property: "Skyline Suites",
    amount: 34000,
    date: "Mar 25, 2026",
    status: "Overdue"
  },
  {
    tenant: "Lucy Njeri",
    unit: "R-34",
    property: "Riverpoint Residenc",
    amount: 42000,
    date: "Mar 29, 2026",
    status: "Paid"
  },
  {
    tenant: "Asha Maina",
    unit: "BH-07",
    property: "Bluehaven Apartments",
    amount: 26000,
    date: "Mar 28, 2026",
    status: "Paid"
  },
  {
    tenant: "Kelvin Kariuki",
    unit: "SS-04",
    property: "Skyline Suites",
    amount: 31000,
    date: "Mar 29, 2026",
    status: "Pending"
  }
];

const maintenanceTickets = [
  {
    title: "Water pressure drop in master bathroom",
    unit: "R-18",
    property: "Riverpoint Residenc",
    assignee: "Kevin Otieno",
    eta: "Today, 5:30 PM",
    priority: "High"
  },
  {
    title: "Generator inspection after weekend outage",
    unit: "BH-Block C",
    property: "Bluehaven Apartments",
    assignee: "Grace Kamau",
    eta: "Tomorrow, 10:00 AM",
    priority: "Medium"
  },
  {
    title: "Window latch replacement",
    unit: "MC-11",
    property: "Maple Court Lofts",
    assignee: "Tom Muli",
    eta: "Mar 31, 9:00 AM",
    priority: "Low"
  },
  {
    title: "Kitchen extractor fan repair",
    unit: "SS-07",
    property: "Skyline Suites",
    assignee: "Mercy Kendi",
    eta: "Today, 3:00 PM",
    priority: "High"
  },
  {
    title: "Parking gate sensor recalibration",
    unit: "MC-Gate",
    property: "Maple Court Lofts",
    assignee: "Tom Muli",
    eta: "Apr 01, 11:00 AM",
    priority: "Medium"
  },
  {
    title: "Hallway lighting flicker on level 2",
    unit: "BH-Tower B",
    property: "Bluehaven Apartments",
    assignee: "Grace Kamau",
    eta: "Today, 6:15 PM",
    priority: "Low"
  }
];

const alerts = [
  {
    type: "danger",
    title: "2 tenants are now 3+ days overdue",
    description: "Bluehaven Apartments and Skyline Suites need immediate follow-up to avoid month-end rollover.",
    time: "8 minutes ago",
    icon: "fa-solid fa-circle-exclamation"
  },
  {
    type: "warning",
    title: "Vacancy risk rising at Skyline Suites",
    description: "Occupancy has slipped to 72%. Consider a short-term offer or broker push for the next 14 days.",
    time: "27 minutes ago",
    icon: "fa-solid fa-building"
  },
  {
    type: "success",
    title: "Riverpoint auto-collected 14 payments",
    description: "KSh 588,000 settled successfully this morning through recurring billing.",
    time: "1 hour ago",
    icon: "fa-solid fa-circle-check"
  },
  {
    type: "info",
    title: "Maintenance response time improved",
    description: "Average first response dropped from 5.2 hrs to 4.1 hrs over the last 30 days.",
    time: "3 hours ago",
    icon: "fa-solid fa-bolt"
  },
  {
    type: "warning",
    title: "4 leases entered the renewal window",
    description: "Renewal offers for Maple Court and Skyline Suites should go out this week to reduce churn risk.",
    time: "Yesterday",
    icon: "fa-solid fa-file-signature"
  },
  {
    type: "success",
    title: "Cedar Grove reached full occupancy",
    description: "The final reserved villa converted successfully and the building is now 100% leased.",
    time: "Yesterday",
    icon: "fa-solid fa-house"
  }
];

const occupancyBreakdown = [
  { label: "Occupied", value: 152, color: "#2f74ff" },
  { label: "Vacant", value: 12, color: "#ffb24d" },
  { label: "Reserved", value: 10, color: "#1bc6a6" }
];

const rentTrend = {
  labels: ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
  expected: [2.58, 2.64, 2.71, 2.76, 2.83, 3.12],
  collected: [2.44, 2.51, 2.63, 2.69, 2.77, 2.84]
};

const maintenanceCategories = {
  labels: ["Plumbing", "Electrical", "HVAC", "Security", "Common Area"],
  values: [4, 3, 2, 1, 4]
};

const paymentMethods = [
  { label: "Autopay", value: 68, color: "#2f74ff" },
  { label: "Bank Transfer", value: 18, color: "#1bc6a6" },
  { label: "M-Pesa", value: 10, color: "#ffb24d" },
  { label: "Cash", value: 4, color: "#ec5f67" }
];

const tenantSegments = [
  { label: "Good Standing", value: 108, color: "#2f74ff" },
  { label: "Renewing Soon", value: 28, color: "#ffb24d" },
  { label: "Watchlist", value: 16, color: "#ec5f67" }
];

const unitMix = [
  { label: "Studios", count: 28, occupied: 22, avgRent: 18000 },
  { label: "1 Bedroom", count: 74, occupied: 66, avgRent: 24000 },
  { label: "2 Bedroom", count: 54, occupied: 47, avgRent: 32000 },
  { label: "3 Bedroom", count: 18, occupied: 17, avgRent: 43000 }
];

const renewalQueue = [
  { name: "Naomi Wanjiku", unit: "MC-08", date: "Apr 18, 2026", action: "Send 12-month renewal proposal", tone: "needs-attention" },
  { name: "Mohammed Noor", unit: "SS-14", date: "Apr 28, 2026", action: "Review retention offer after payment call", tone: "vacancy-risk" },
  { name: "Asha Maina", unit: "BH-07", date: "May 04, 2026", action: "Trigger early-renewal incentive", tone: "stable" },
  { name: "Kelvin Kariuki", unit: "SS-04", date: "May 12, 2026", action: "Schedule lease conversation", tone: "needs-attention" }
];

const automationRules = [
  {
    title: "Overdue rent reminder",
    cadence: "3 days before due date, then 2 days overdue",
    channel: "Email + SMS",
    status: "Live"
  },
  {
    title: "Vacancy watch escalation",
    cadence: "Weekly every Monday at 8:00 AM",
    channel: "Manager inbox",
    status: "Live"
  },
  {
    title: "Maintenance SLA alert",
    cadence: "After 4 hours without first response",
    channel: "Email + Slack",
    status: "Live"
  },
  {
    title: "Owner performance digest",
    cadence: "Every Friday at 8:00 AM",
    channel: "Email PDF",
    status: "Scheduled"
  }
];

const vendorPerformance = [
  { name: "Kevin Otieno", specialty: "Plumbing", sla: "96%", rating: "4.8/5", note: "Fastest average resolution across urgent repairs." },
  { name: "Grace Kamau", specialty: "Electrical", sla: "93%", rating: "4.6/5", note: "Strong response quality on backup power incidents." },
  { name: "Mercy Kendi", specialty: "Appliances", sla: "89%", rating: "4.5/5", note: "Handles tenant-facing repair updates very well." },
  { name: "Tom Muli", specialty: "General Repairs", sla: "91%", rating: "4.7/5", note: "Reliable throughput on medium-priority work orders." }
];

const communicationFeed = [
  { title: "Reminder batch sent to 6 tenants", channel: "SMS", audience: "Rent due D-1", time: "Today, 7:30 AM" },
  { title: "Lease renewal draft sent to Naomi Wanjiku", channel: "Email", audience: "Single resident", time: "Today, 9:15 AM" },
  { title: "Maintenance ETA update shared with R-18", channel: "WhatsApp", audience: "Resident update", time: "Today, 10:05 AM" },
  { title: "Owner weekly digest queued", channel: "Email", audience: "Owners and investors", time: "Friday, 8:00 AM" }
];

const settingsCards = [
  {
    title: "Automatic rent reminders",
    description: "Send branded reminders before due dates and escalate overdue balances automatically.",
    enabled: true
  },
  {
    title: "Vacancy risk warnings",
    description: "Flag properties with soft occupancy or expiring leases before revenue risk compounds.",
    enabled: true
  },
  {
    title: "Owner digest reports",
    description: "Compile weekly portfolio updates with collections, occupancy, and ticket trends.",
    enabled: true
  },
  {
    title: "Manual review hold",
    description: "Pause outgoing reminders for accounts that are already in active negotiation.",
    enabled: false
  }
];

const integrations = [
  { name: "M-Pesa Collection API", status: "Connected", detail: "Realtime callback receipts and payment reconciliation are healthy." },
  { name: "Bank Settlement Feed", status: "Healthy", detail: "Daily settlement files arrive at 6:00 AM with no missing records." },
  { name: "Email Delivery Service", status: "Synced", detail: "Reminder delivery success remains above 99% this month." },
  { name: "Vendor Dispatch Portal", status: "Connected", detail: "Maintenance assignment handoff is active for all preferred vendors." },
  { name: "BI Export Pipeline", status: "Connected", detail: "Friday owner report exports are landing in the analytics bucket." }
];

const accessRoles = [
  { role: "Portfolio Manager", members: 2, permission: "Full access to all modules and reporting." },
  { role: "Leasing Coordinator", members: 3, permission: "Properties, units, tenant renewals, and alerts." },
  { role: "Finance Analyst", members: 2, permission: "Payments, exports, and reconciliation workflows." },
  { role: "Maintenance Lead", members: 4, permission: "Tickets, vendors, and service response tracking." }
];

const benchmarkCards = [
  { title: "Forecast accuracy", value: "94.7%", detail: "Revenue planning remains highly reliable across the last six months." },
  { title: "Avg. response time", value: "4.1 hrs", detail: "Maintenance first response is moving in the right direction." },
  { title: "Vacancy exposure", value: "KSh 338K", detail: "Potential monthly revenue at risk if current vacancies remain open." },
  { title: "Renewal success", value: "81%", detail: "Most targeted renewal offers are converting before lease expiry." }
];

const metricSets = {
  overview: [
    {
      label: "Monthly Collection",
      value: 2840000,
      format: "currency",
      copy: "Collected from 178 completed rent transactions this cycle.",
      trendLabel: "+12%",
      trendStyle: "positive",
      icon: "fa-coins",
      accent: true
    },
    {
      label: "Occupancy Rate",
      value: 87.4,
      format: "percent",
      copy: "Strong occupancy across stabilized properties with room to optimize two sites.",
      trendLabel: "+3.4%",
      trendStyle: "positive",
      icon: "fa-door-open",
      iconTone: "mint"
    },
    {
      label: "Open Maintenance Tickets",
      value: 14,
      format: "number",
      copy: "Most active requests are plumbing and electrical, with response time improving.",
      trendLabel: "-9%",
      trendStyle: "positive",
      icon: "fa-screwdriver-wrench",
      iconTone: "gold"
    },
    {
      label: "Late Payments",
      value: 6,
      format: "number",
      copy: "Follow-up reminders were sent automatically to minimize overdue exposure.",
      trendLabel: "-4%",
      trendStyle: "positive",
      icon: "fa-triangle-exclamation",
      iconTone: "rose"
    }
  ],
  properties: [
    {
      label: "Active Properties",
      value: 5,
      format: "number",
      copy: "Every building is tracked with occupancy, revenue, and status scoring.",
      trendLabel: "+1 new",
      trendStyle: "positive",
      icon: "fa-building",
      accent: true
    },
    {
      label: "Total Units",
      value: 174,
      format: "number",
      copy: "Mixed unit inventory spanning studios through 3-bedroom homes.",
      trendLabel: "+12 units",
      trendStyle: "positive",
      icon: "fa-layer-group",
      iconTone: "mint"
    },
    {
      label: "Occupied Units",
      value: 152,
      format: "number",
      copy: "Most occupancy softness is isolated to only two properties in the portfolio.",
      trendLabel: "+6 units",
      trendStyle: "positive",
      icon: "fa-house-user",
      iconTone: "gold"
    },
    {
      label: "Vacancy Risk Buildings",
      value: 2,
      format: "number",
      copy: "Targeted marketing and renewal work should stay focused on these assets.",
      trendLabel: "Priority",
      trendStyle: "negative",
      icon: "fa-house-crack",
      iconTone: "rose"
    }
  ],
  tenants: [
    {
      label: "Active Leases",
      value: 152,
      format: "number",
      copy: "Current residents with active occupancy contributing to monthly cash flow.",
      trendLabel: "+4%",
      trendStyle: "positive",
      icon: "fa-users",
      accent: true
    },
    {
      label: "Renewals Due Soon",
      value: 18,
      format: "number",
      copy: "Leases entering a 45-day renewal window and ready for proactive outreach.",
      trendLabel: "+3",
      trendStyle: "positive",
      icon: "fa-file-signature",
      iconTone: "gold"
    },
    {
      label: "Autopay Enrollment",
      value: 68.4,
      format: "percent",
      copy: "Recurring billing continues to improve payment timing and collection certainty.",
      trendLabel: "+5.1%",
      trendStyle: "positive",
      icon: "fa-credit-card",
      iconTone: "mint"
    },
    {
      label: "Watchlist Accounts",
      value: 7,
      format: "number",
      copy: "Accounts with higher risk due to arrears, expiring leases, or weak payment behavior.",
      trendLabel: "-2",
      trendStyle: "positive",
      icon: "fa-user-clock",
      iconTone: "rose"
    }
  ],
  payments: [
    {
      label: "Collected This Month",
      value: 2840000,
      format: "currency",
      copy: "Collection pace remains healthy and is improving across automated payment channels.",
      trendLabel: "+12%",
      trendStyle: "positive",
      icon: "fa-money-bill-wave",
      accent: true
    },
    {
      label: "Outstanding Balance",
      value: 278000,
      format: "currency",
      copy: "Open exposure is concentrated in a small set of higher-risk accounts.",
      trendLabel: "-6%",
      trendStyle: "positive",
      icon: "fa-scale-balanced",
      iconTone: "gold"
    },
    {
      label: "Overdue Accounts",
      value: 6,
      format: "number",
      copy: "Most overdue balances are already in active reminder or escalation workflows.",
      trendLabel: "-4%",
      trendStyle: "positive",
      icon: "fa-hourglass-half",
      iconTone: "rose"
    },
    {
      label: "Autopay Success",
      value: 96.2,
      format: "percent",
      copy: "Autopay continues to outperform manual settlement channels on reliability.",
      trendLabel: "+2.8%",
      trendStyle: "positive",
      icon: "fa-repeat",
      iconTone: "mint"
    }
  ],
  maintenance: [
    {
      label: "Open Tickets",
      value: 14,
      format: "number",
      copy: "Ticket load is manageable, with priority incidents escalated automatically.",
      trendLabel: "-9%",
      trendStyle: "positive",
      icon: "fa-screwdriver-wrench",
      accent: true
    },
    {
      label: "High Priority",
      value: 5,
      format: "number",
      copy: "Urgent requests are routed for same-day action and monitored tightly.",
      trendLabel: "-1",
      trendStyle: "positive",
      icon: "fa-bolt",
      iconTone: "rose"
    },
    {
      label: "SLA Hit Rate",
      value: 92.4,
      format: "percent",
      copy: "Vendor coordination and internal triage are keeping service quality strong.",
      trendLabel: "+3.2%",
      trendStyle: "positive",
      icon: "fa-thumbs-up",
      iconTone: "mint"
    },
    {
      label: "Avg. Resolution Days",
      value: 1.8,
      format: "decimal",
      copy: "Resolution speed is improving, especially on plumbing and electrical issues.",
      trendLabel: "-0.4",
      trendStyle: "positive",
      icon: "fa-clock",
      iconTone: "gold"
    }
  ],
  analytics: [
    {
      label: "NOI Trend",
      value: 8.2,
      format: "percent",
      copy: "Net operating income is trending higher as collections improve and tickets stabilize.",
      trendLabel: "+1.8%",
      trendStyle: "positive",
      icon: "fa-chart-line",
      accent: true
    },
    {
      label: "Forecast Accuracy",
      value: 94.7,
      format: "percent",
      copy: "Projected rent versus collected rent remains tightly aligned over the last two quarters.",
      trendLabel: "+2.3%",
      trendStyle: "positive",
      icon: "fa-bullseye",
      iconTone: "mint"
    },
    {
      label: "Arrears Ratio",
      value: 4.6,
      format: "percent",
      copy: "Late-payment pressure is manageable but still concentrated in two buildings.",
      trendLabel: "-0.9%",
      trendStyle: "positive",
      icon: "fa-wave-square",
      iconTone: "gold"
    },
    {
      label: "Portfolio Occupancy",
      value: 87.4,
      format: "percent",
      copy: "Occupancy continues to stabilize across the portfolio despite softer leasing in two assets.",
      trendLabel: "+3.4%",
      trendStyle: "positive",
      icon: "fa-door-open",
      iconTone: "rose"
    }
  ],
  notifications: [
    {
      label: "Active Alerts",
      value: 12,
      format: "number",
      copy: "Prioritized operational alerts requiring attention or active monitoring.",
      trendLabel: "-2",
      trendStyle: "positive",
      icon: "fa-bell",
      accent: true
    },
    {
      label: "Reminder Rules",
      value: 6,
      format: "number",
      copy: "Automation rules keep rent reminders and operational follow-ups moving without manual effort.",
      trendLabel: "+1",
      trendStyle: "positive",
      icon: "fa-robot",
      iconTone: "mint"
    },
    {
      label: "Positive Updates",
      value: 14,
      format: "number",
      copy: "Payments received, tickets resolved, and occupancy wins are feeding the activity stream.",
      trendLabel: "+6",
      trendStyle: "positive",
      icon: "fa-circle-check",
      iconTone: "gold"
    },
    {
      label: "Escalations",
      value: 3,
      format: "number",
      copy: "Only a small portion of alerts require direct intervention from management.",
      trendLabel: "-1",
      trendStyle: "positive",
      icon: "fa-triangle-exclamation",
      iconTone: "rose"
    }
  ],
  settings: [
    {
      label: "Integrations",
      value: 5,
      format: "number",
      copy: "Connected tools feeding payments, reporting, reminders, and vendor coordination.",
      trendLabel: "+1",
      trendStyle: "positive",
      icon: "fa-plug",
      accent: true
    },
    {
      label: "Active Automations",
      value: 6,
      format: "number",
      copy: "Core reminder, reporting, and escalation workflows are active and healthy.",
      trendLabel: "Stable",
      trendStyle: "positive",
      icon: "fa-gears",
      iconTone: "mint"
    },
    {
      label: "Permission Roles",
      value: 4,
      format: "number",
      copy: "Access is organized by clear role-based permissions across portfolio teams.",
      trendLabel: "Controlled",
      trendStyle: "positive",
      icon: "fa-user-shield",
      iconTone: "gold"
    },
    {
      label: "Scheduled Reports",
      value: 3,
      format: "number",
      copy: "Owner digests and analytics exports are configured for consistent delivery.",
      trendLabel: "On time",
      trendStyle: "positive",
      icon: "fa-file-lines",
      iconTone: "rose"
    }
  ]
};

const currencyFormatter = new Intl.NumberFormat("en-KE", {
  style: "currency",
  currency: "KES",
  maximumFractionDigits: 0
});

const compactCurrencyFormatter = new Intl.NumberFormat("en-KE", {
  style: "currency",
  currency: "KES",
  notation: "compact",
  maximumFractionDigits: 2
});

function formatCompactCurrency(value) {
  return compactCurrencyFormatter.format(value).replace("KES", "KSh");
}

function formatCurrency(value) {
  return currencyFormatter.format(value).replace("KES", "KSh");
}

function statusClassName(status) {
  return status.toLowerCase().replace(/\s+/g, "-");
}

function badgeTone(label) {
  const tones = {
    "High Performing": "high-performing",
    Stable: "stable",
    "Needs Attention": "needs-attention",
    "Vacancy Risk": "vacancy-risk",
    "Good Standing": "high-performing",
    "Renewing Soon": "needs-attention",
    Watchlist: "vacancy-risk",
    Live: "high-performing",
    Scheduled: "stable",
    Connected: "high-performing",
    Healthy: "stable",
    Synced: "stable"
  };

  return tones[label] || "stable";
}

function metricPlaceholder(format) {
  if (format === "currency") {
    return "KSh 0";
  }

  if (format === "percent") {
    return "0%";
  }

  if (format === "decimal") {
    return "0.0";
  }

  return "0";
}

function getMetricCardsHTML(metrics) {
  return metrics
    .map((metric) => {
      const iconToneClass = metric.iconTone ? ` metric-card__icon--${metric.iconTone}` : "";
      const accentClass = metric.accent ? " metric-card--accent" : "";

      const trendIcon = metric.trendLabel.trim().startsWith("-") ? "fa-arrow-trend-down" : "fa-arrow-trend-up";

      return `
        <article class="metric-card${accentClass}">
          <div class="metric-card__icon${iconToneClass}">
            <i class="fa-solid ${metric.icon}"></i>
          </div>
          <div class="metric-card__content">
            <span class="metric-card__label">${metric.label}</span>
            <strong class="metric-value" data-value="${metric.value}" data-format="${metric.format}">${metricPlaceholder(metric.format)}</strong>
            <p>${metric.copy}</p>
          </div>
          <span class="trend trend--${metric.trendStyle}">
            <i class="fa-solid ${trendIcon}"></i>
            ${metric.trendLabel}
          </span>
        </article>
      `;
    })
    .join("");
}

function getHeroHTML(hero) {
  return `
    <section class="hero-panel reveal">
      <div class="hero-panel__copy">
        <span class="section-label">${hero.label}</span>
        <h3>${hero.title}</h3>
        <p>${hero.description}</p>

        <div class="hero-panel__chips">
          ${hero.chips
      .map(
        (chip) => `
                <div class="hero-chip">
                  <strong>${chip.value}</strong>
                  <span>${chip.label}</span>
                </div>
              `
      )
      .join("")}
        </div>
      </div>

      <div class="hero-panel__spotlight">
        ${hero.spotlights
      .map(
        (spotlight) => `
              <div class="spotlight-card">
                <span class="spotlight-card__label">${spotlight.label}</span>
                <strong>${spotlight.value}</strong>
                <p>${spotlight.text}</p>
              </div>
            `
      )
      .join("")}
      </div>
    </section>
  `;
}

function getSidebarHTML(page) {
  return `
    <div class="sidebar__top">
      <button class="icon-button sidebar__close mobile-only" id="closeSidebar" aria-label="Close navigation">
        <i class="fa-solid fa-xmark"></i>
      </button>

      <a href="${routeMap.overview}" class="brand">
        <div class="brand__mark">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div>
          <h1>SmartRent</h1>
          <p>Landlord command center</p>
        </div>
      </a>
    </div>

    <nav class="sidebar__nav" aria-label="Primary">
      ${navItems
      .map(
        (item) => `
            <a class="nav-link${item.key === page ? " active" : ""}" href="${item.href}" data-nav="${item.key}">
              <span class="nav-link__icon"><i class="fa-solid ${item.icon}"></i></span>
              <span>${item.label}</span>
            </a>
          `
      )
      .join("")}
    </nav>

    <div class="sidebar__footer">
      <div class="sidebar-card">
        <div class="sidebar-card__icon">
          <i class="fa-solid fa-bolt"></i>
        </div>
        <div>
          <h3>Automation boost</h3>
          <p>Rent reminders and vacancy alerts are actively reducing manual follow-up across the portfolio.</p>
        </div>
        <a href="${routeMap.notifications}" class="sidebar-card__link">Review alerts</a>
      </div>
    </div>
  `;
}

function getHeaderHTML(config) {
  return `
    <div class="topbar__intro">
      <div class="topbar__heading">
        <button class="icon-button menu-toggle mobile-only" id="openSidebar" aria-label="Open navigation">
          <i class="fa-solid fa-bars-staggered"></i>
        </button>
        <div>
          <span class="eyebrow">${config.eyebrow}</span>
          <h2>${config.title}</h2>
        </div>
      </div>
      <p class="topbar__tagline">${config.tagline}</p>
    </div>

    <div class="topbar__actions">
      <label class="search-field">
        <i class="fa-solid fa-magnifying-glass"></i>
        <input type="search" placeholder="${config.searchPlaceholder}">
      </label>

      <div class="button-row">
        <button class="btn btn--secondary" ${config.secondaryAction.label === "Add Property" ? 'data-action="add-property"' : ""}>
          <i class="fa-solid ${config.secondaryAction.icon}"></i>
          <span>${config.secondaryAction.label}</span>
        </button>
        <button class="btn btn--primary" ${config.primaryAction.label === "Add Property" ? 'data-action="add-property"' : ""}>
          <i class="fa-solid ${config.primaryAction.icon}"></i>
          <span>${config.primaryAction.label}</span>
        </button>
      </div>

      <div class="profile-chip">
        <div class="profile-chip__avatar">AK</div>
        <div>
          <strong>Alice K.</strong>
          <span>Portfolio Manager</span>
        </div>
        <button class="icon-button" aria-label="Open profile menu">
          <i class="fa-solid fa-chevron-down"></i>
        </button>
      </div>
    </div>
  `;
}

function getOverviewTemplate() {
  return `
    ${getHeroHTML(pageConfigs.overview.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.overview)}
    </section>

    <section class="analytics-layout">
      <div class="analytics-layout__main">
        <article class="panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">Collections analytics</span>
              <h3>Expected rent vs collected rent</h3>
            </div>
            <span class="panel-pill">Last 6 months</span>
          </div>
          <div class="chart-area chart-area--large">
            <canvas id="rentChart"></canvas>
          </div>
        </article>

        <article class="panel reveal">
          <div class="panel__header panel__header--stack">
            <div>
              <span class="section-label">Properties and units</span>
              <h3>Portfolio performance preview</h3>
              <p class="section-copy">Review top-performing buildings and vacancy signals before you dive into the dedicated properties page.</p>
            </div>
            <a href="${routeMap.properties}" class="panel-pill">Open properties</a>
          </div>
          <div class="properties-grid" id="propertyGrid"></div>
        </article>
      </div>

      <aside class="analytics-layout__side">
        <article class="panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">Occupancy mix</span>
              <h3>Portfolio unit status</h3>
            </div>
          </div>
          <div class="occupancy-card">
            <div class="chart-area chart-area--doughnut">
              <canvas id="occupancyChart"></canvas>
            </div>
            <div class="occupancy-legend" id="occupancyLegend"></div>
          </div>
        </article>

        <article class="panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">Smart alerts</span>
              <h3>Live reminders and portfolio signals</h3>
            </div>
            <a href="${routeMap.notifications}" class="panel-pill">See all</a>
          </div>
          <div class="alerts-list" id="alertsList"></div>
        </article>

        <article class="panel insight-panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">AI insight</span>
              <h3 id="insightTitle">Portfolio recommendation</h3>
            </div>
            <div class="insight-badge">
              <i class="fa-solid fa-wand-magic"></i>
              Smart recommendation
            </div>
          </div>
          <p class="insight-copy" id="insightCopy"></p>
          <div class="insight-actions">
            <a href="${routeMap.tenants}" class="btn btn--primary btn--full">Launch retention campaign</a>
            <a href="${routeMap.analytics}" class="btn btn--ghost btn--full">Review portfolio plan</a>
          </div>
        </article>
      </aside>
    </section>

    <section class="operations-layout">
      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Rent activity</span>
            <h3>Recent payment activity</h3>
          </div>
          <a href="${routeMap.payments}" class="panel-pill panel-pill--success">Open payments</a>
        </div>
        <div class="table-wrap">
          <table class="activity-table">
            <thead>
              <tr>
                <th>Tenant</th>
                <th>Unit</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id="activityTableBody"></tbody>
          </table>
        </div>
      </article>

      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Maintenance</span>
            <h3>Current tickets</h3>
          </div>
          <a href="${routeMap.maintenance}" class="panel-pill panel-pill--warm">Open maintenance</a>
        </div>
        <div class="ticket-list" id="ticketList"></div>
      </article>
    </section>
  `;
}

function getPropertiesTemplate() {
  return `
    <section class="panel reveal">
      <div class="panel__header panel__header--stack">
        <div>
          <span class="section-label">Property management</span>
          <h3>Buildings, units, and revenue health</h3>
          <p class="section-copy">Search and filter the full portfolio to find high-performing assets, stable buildings, and sites needing immediate action.</p>
        </div>

        <div class="property-controls">
          <label class="search-field search-field--compact">
            <i class="fa-solid fa-magnifying-glass"></i>
            <input type="search" id="propertySearch" placeholder="Search property or location">
          </label>

          <label class="select-field">
            <span>Status</span>
            <select id="propertyFilter" aria-label="Filter properties by status">
              <option value="all">All status levels</option>
              <option value="High Performing">High Performing</option>
              <option value="Stable">Stable</option>
              <option value="Needs Attention">Needs Attention</option>
              <option value="Vacancy Risk">Vacancy Risk</option>
            </select>
          </label>

          <label class="select-field select-field--view">
            <span>View</span>
            <select id="propertyViewSelect" aria-label="Choose property view">
              <option value="grid">Grid</option>
              <option value="list">List</option>
            </select>
          </label>
        </div>
      </div>

      <div class="properties-grid" id="propertyGrid"></div>
    </section>

    ${getHeroHTML(pageConfigs.properties.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.properties)}
    </section>

    <section class="content-grid">
      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Unit mix</span>
            <h3>Inventory by bedroom type</h3>
          </div>
          <span class="panel-pill">174 units</span>
        </div>
        <div class="unit-list" id="unitList"></div>
      </article>

      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Occupancy distribution</span>
            <h3>Occupied, vacant, and reserved units</h3>
          </div>
        </div>
        <div class="occupancy-card">
          <div class="chart-area chart-area--doughnut">
            <canvas id="occupancyChart"></canvas>
          </div>
          <div class="occupancy-legend" id="occupancyLegend"></div>
        </div>
      </article>
    </section>
  `;
}

function getTenantsTemplate() {
  return `
    ${getHeroHTML(pageConfigs.tenants.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.tenants)}
    </section>

    <section class="panel reveal">
      <div class="panel__header">
        <div>
          <span class="section-label">Tenant directory</span>
          <h3>Lease and relationship overview</h3>
        </div>
        <span class="panel-pill">152 active leases</span>
      </div>
      <div class="resource-grid" id="tenantGrid"></div>
    </section>

    <section class="content-grid">
      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Tenant health</span>
            <h3>Portfolio resident segments</h3>
          </div>
        </div>
        <div class="occupancy-card">
          <div class="chart-area chart-area--doughnut">
            <canvas id="tenantStatusChart"></canvas>
          </div>
          <div class="occupancy-legend" id="tenantStatusLegend"></div>
        </div>
      </article>

      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Renewal queue</span>
            <h3>Upcoming lease decisions</h3>
          </div>
          <span class="panel-pill panel-pill--warm">45-day horizon</span>
        </div>
        <div class="note-list" id="renewalList"></div>
      </article>
    </section>
  `;
}

function getPaymentsTemplate() {
  return `
    ${getHeroHTML(pageConfigs.payments.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.payments)}
    </section>

    <section class="content-grid content-grid--equal">
      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Collection trend</span>
            <h3>Expected rent vs collected rent</h3>
          </div>
          <span class="panel-pill">Last 6 months</span>
        </div>
        <div class="chart-area chart-area--large">
          <canvas id="rentChart"></canvas>
        </div>
      </article>

      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Settlement mix</span>
            <h3>Payment channel breakdown</h3>
          </div>
        </div>
        <div class="occupancy-card">
          <div class="chart-area chart-area--doughnut">
            <canvas id="paymentMethodChart"></canvas>
          </div>
          <div class="occupancy-legend" id="paymentMethodLegend"></div>
        </div>
      </article>
    </section>

    <section class="panel reveal">
      <div class="panel__header">
        <div>
          <span class="section-label">Payment activity</span>
          <h3>Full rent transaction feed</h3>
        </div>
        <span class="panel-pill panel-pill--success">91.1% collected</span>
      </div>

      <div class="table-wrap">
        <table class="activity-table">
          <thead>
            <tr>
              <th>Tenant</th>
              <th>Unit</th>
              <th>Amount</th>
              <th>Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="activityTableBody"></tbody>
        </table>
      </div>
    </section>
  `;
}

function getMaintenanceTemplate() {
  return `
    ${getHeroHTML(pageConfigs.maintenance.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.maintenance)}
    </section>

    <section class="content-grid">
      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Ticket queue</span>
            <h3>Current maintenance requests</h3>
          </div>
          <span class="panel-pill panel-pill--warm">14 open tickets</span>
        </div>
        <div class="ticket-list" id="ticketList"></div>
      </article>

      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Service load</span>
            <h3>Maintenance issue categories</h3>
          </div>
          <span class="panel-pill">Current month</span>
        </div>
        <div class="chart-area chart-area--medium">
          <canvas id="maintenanceChart"></canvas>
        </div>
      </article>
    </section>

    <section class="panel reveal">
      <div class="panel__header">
        <div>
          <span class="section-label">Vendor performance</span>
          <h3>Preferred service partners</h3>
        </div>
        <span class="panel-pill panel-pill--success">4 active vendors</span>
      </div>
      <div class="vendor-list" id="vendorList"></div>
    </section>
  `;
}

function getAnalyticsTemplate() {
  return `
    ${getHeroHTML(pageConfigs.analytics.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.analytics)}
    </section>

    <section class="analytics-layout">
      <div class="analytics-layout__main">
        <article class="panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">Revenue analytics</span>
              <h3>Expected rent vs collected rent</h3>
            </div>
            <span class="panel-pill">Last 6 months</span>
          </div>
          <div class="chart-area chart-area--large">
            <canvas id="rentChart"></canvas>
          </div>
        </article>

        <article class="panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">Operational load</span>
              <h3>Maintenance issue categories</h3>
            </div>
            <span class="panel-pill panel-pill--warm">Avg. resolution 1.8 days</span>
          </div>
          <div class="chart-area chart-area--medium">
            <canvas id="maintenanceChart"></canvas>
          </div>
        </article>
      </div>

      <aside class="analytics-layout__side">
        <article class="panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">Occupancy mix</span>
              <h3>Portfolio unit status</h3>
            </div>
          </div>
          <div class="occupancy-card">
            <div class="chart-area chart-area--doughnut">
              <canvas id="occupancyChart"></canvas>
            </div>
            <div class="occupancy-legend" id="occupancyLegend"></div>
          </div>
        </article>

        <article class="panel reveal">
          <div class="panel__header">
            <div>
              <span class="section-label">Benchmark notes</span>
              <h3>Performance highlights</h3>
            </div>
          </div>
          <div class="resource-grid resource-grid--single" id="benchmarkList"></div>
        </article>
      </aside>
    </section>

    <section class="panel insight-panel reveal">
      <div class="panel__header">
        <div>
          <span class="section-label">AI insight</span>
          <h3 id="insightTitle">Portfolio recommendation</h3>
        </div>
        <div class="insight-badge">
          <i class="fa-solid fa-wand-magic"></i>
          Smart recommendation
        </div>
      </div>
      <p class="insight-copy" id="insightCopy"></p>
      <div class="insight-actions insight-actions--inline">
        <a href="${routeMap.properties}" class="btn btn--primary">Open property plan</a>
        <a href="${routeMap.notifications}" class="btn btn--ghost">Check automations</a>
      </div>
    </section>
  `;
}

function getNotificationsTemplate() {
  return `
    ${getHeroHTML(pageConfigs.notifications.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.notifications)}
    </section>

    <section class="content-grid">
      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Alert inbox</span>
            <h3>Prioritized portfolio alerts</h3>
          </div>
          <span class="panel-pill">Live feed</span>
        </div>
        <div class="alerts-list" id="alertsList"></div>
      </article>

      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Automation rules</span>
            <h3>Reminder and escalation workflows</h3>
          </div>
          <span class="panel-pill panel-pill--success">6 rules active</span>
        </div>
        <div class="automation-list" id="automationList"></div>
      </article>
    </section>

    <section class="panel reveal">
      <div class="panel__header">
        <div>
          <span class="section-label">Communication feed</span>
          <h3>Recent reminders and outbound updates</h3>
        </div>
      </div>
      <div class="communication-list" id="communicationList"></div>
    </section>
  `;
}

function getSettingsTemplate() {
  return `
    ${getHeroHTML(pageConfigs.settings.hero)}

    <section class="stats-grid reveal">
      ${getMetricCardsHTML(metricSets.settings)}
    </section>

    <section class="settings-grid reveal" id="settingsGrid"></section>

    <section class="content-grid">
      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Integrations</span>
            <h3>Connected systems and health</h3>
          </div>
        </div>
        <div class="integration-list" id="integrationList"></div>
      </article>

      <article class="panel reveal">
        <div class="panel__header">
          <div>
            <span class="section-label">Access control</span>
            <h3>Role-based permissions</h3>
          </div>
        </div>
        <div class="access-list" id="accessList"></div>
      </article>
    </section>
  `;
}

function getPageTemplate(page) {
  const templates = {
    overview: getOverviewTemplate,
    properties: getPropertiesTemplate,
    tenants: getTenantsTemplate,
    payments: getPaymentsTemplate,
    maintenance: getMaintenanceTemplate,
    analytics: getAnalyticsTemplate,
    notifications: getNotificationsTemplate,
    settings: getSettingsTemplate
  };

  return templates[page] ? templates[page]() : getOverviewTemplate();
}

function renderShell() {
  const sidebar = document.getElementById("sidebar");
  const header = document.getElementById("pageHeader");
  const pageContent = document.getElementById("pageContent");

  if (sidebar) {
    sidebar.innerHTML = getSidebarHTML(currentPage);
  }

  if (header) {
    header.innerHTML = getHeaderHTML(pageConfigs[currentPage]);
  }

  if (pageContent) {
    pageContent.innerHTML = getPageTemplate(currentPage);
  }
}

function renderProperties(list, options = {}) {
  const { targetId = "propertyGrid", limit = list.length } = options;
  const target = document.getElementById(targetId);

  if (!target) {
    return;
  }

  const scopedList = list.slice(0, limit);
  target.classList.toggle("properties-grid--list", propertyViewMode === "list");

  if (!scopedList.length) {
    target.innerHTML = `
      <article class="property-card">
        <div class="property-card__title">
          <h4>No properties found</h4>
          <p>Try a different search term or clear the status filter.</p>
        </div>
      </article>
    `;
    return;
  }

  if (propertyViewMode === "list") {
    target.innerHTML = `
      <div class="property-table-wrap">
        <table class="property-table">
          <thead>
            <tr>
              <th>Property</th>
              <th>Location</th>
              <th>Status</th>
              <th>Units</th>
              <th>Occupied</th>
              <th>Occupancy</th>
              <th>Revenue</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            ${scopedList
        .map((property) => {
          const trendClass = property.trend < 0 ? "property-card__trend property-card__trend--down" : "property-card__trend";
          const trendIcon = property.trend < 0 ? "fa-arrow-trend-down" : "fa-arrow-trend-up";

          return `
                  <tr>
                    <td>
                      <div class="table-tenant">
                        <strong>${property.name}</strong>
                        <span>${property.location}</span>
                      </div>
                    </td>
                    <td>${property.location}</td>
                    <td><span class="status-badge status-badge--${statusClassName(property.status)}">${property.status}</span></td>
                    <td>${property.units}</td>
                    <td>${property.occupiedUnits}</td>
                    <td>${property.occupancy}%</td>
                    <td>${formatCompactCurrency(property.revenue)}</td>
                    <td><span class="${trendClass}"><i class="fa-solid ${trendIcon}"></i>${Math.abs(property.trend)}%</span></td>
                  </tr>
                `;
        })
        .join("")}
          </tbody>
        </table>
      </div>
    `;
    return;
  }

  target.innerHTML = scopedList
    .map((property) => {
      const trendClass = property.trend < 0 ? "property-card__trend property-card__trend--down" : "property-card__trend";
      const trendIcon = property.trend < 0 ? "fa-arrow-trend-down" : "fa-arrow-trend-up";

      return `
        <article class="property-card${propertyViewMode === "list" ? " property-card--list" : ""}">
          <div class="property-card__top">
            <div class="property-card__title">
              <h4>${property.name}</h4>
              <p><i class="fa-solid fa-location-dot"></i> ${property.location}</p>
            </div>
            <span class="status-badge status-badge--${statusClassName(property.status)}">${property.status}</span>
          </div>

          <div class="property-card__meta">
            <div class="meta-stack">
              <span>Units</span>
              <strong>${property.units}</strong>
            </div>
            <div class="meta-stack">
              <span>Occupied</span>
              <strong>${property.occupiedUnits}</strong>
            </div>
          </div>

          <div class="progress-group">
            <div class="progress-group__label">
              <span>Occupancy progress</span>
              <strong>${property.occupancy}%</strong>
            </div>
            <div class="progress-bar">
              <span style="width: ${property.occupancy}%"></span>
            </div>
          </div>

          <div class="property-card__footer">
            <div>
              <span class="section-copy">Monthly revenue</span>
              <div class="property-card__revenue">${formatCompactCurrency(property.revenue)}</div>
            </div>
            <span class="${trendClass}">
              <i class="fa-solid ${trendIcon}"></i>
              ${Math.abs(property.trend)}%
            </span>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderActivity(targetId = "activityTableBody", limit = rentActivity.length) {
  const target = document.getElementById(targetId);

  if (!target) {
    return;
  }

  target.innerHTML = rentActivity
    .slice(0, limit)
    .map(
      (item) => `
        <tr>
          <td>
            <div class="table-tenant">
              <strong>${item.tenant}</strong>
              <span>${item.property}</span>
            </div>
          </td>
          <td>${item.unit}</td>
          <td>${formatCurrency(item.amount)}</td>
          <td><small>${item.date}</small></td>
          <td>
            <span class="table-status table-status--${item.status.toLowerCase()}">${item.status}</span>
          </td>
        </tr>
      `
    )
    .join("");
}

function renderTickets(targetId = "ticketList", limit = maintenanceTickets.length) {
  const target = document.getElementById(targetId);

  if (!target) {
    return;
  }

  target.innerHTML = maintenanceTickets
    .slice(0, limit)
    .map(
      (ticket) => `
        <article class="ticket-card">
          <div class="ticket-card__header">
            <div>
              <h4>${ticket.title}</h4>
              <p>${ticket.property} • ${ticket.unit}</p>
            </div>
            <span class="priority-badge priority-badge--${ticket.priority.toLowerCase()}">${ticket.priority}</span>
          </div>
          <div class="ticket-card__meta">
            <span><i class="fa-solid fa-user"></i> ${ticket.assignee}</span>
            <span><i class="fa-regular fa-clock"></i> ${ticket.eta}</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderAlerts(targetId = "alertsList", limit = alerts.length) {
  const target = document.getElementById(targetId);

  if (!target) {
    return;
  }

  target.innerHTML = alerts
    .slice(0, limit)
    .map(
      (alert) => `
        <article class="alert-item">
          <div class="alert-item__icon alert-item__icon--${alert.type}">
            <i class="${alert.icon}"></i>
          </div>
          <div>
            <h4>${alert.title}</h4>
            <p>${alert.description}</p>
            <span class="alert-item__time">${alert.time}</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderLegend(targetId, items, format = (item) => item.value) {
  const target = document.getElementById(targetId);

  if (!target) {
    return;
  }

  target.innerHTML = items
    .map(
      (item) => `
        <div class="occupancy-legend__item">
          <div class="occupancy-legend__meta">
            <span class="occupancy-dot" style="background: ${item.color}"></span>
            <span>${item.label}</span>
          </div>
          <strong>${format(item)}</strong>
        </div>
      `
    )
    .join("");
}

function renderUnitMix() {
  const target = document.getElementById("unitList");

  if (!target) {
    return;
  }

  target.innerHTML = unitMix
    .map((unit) => {
      const occupancy = Math.round((unit.occupied / unit.count) * 100);
      const tone = occupancy >= 90 ? "high-performing" : occupancy >= 80 ? "stable" : "needs-attention";

      return `
        <article class="resource-card">
          <div class="resource-card__header">
            <div>
              <h4>${unit.label}</h4>
              <p>${unit.count} units • Avg rent ${formatCurrency(unit.avgRent)}</p>
            </div>
            <span class="status-badge status-badge--${tone}">${occupancy}% leased</span>
          </div>
          <div class="progress-group">
            <div class="progress-group__label">
              <span>Leased units</span>
              <strong>${unit.occupied}/${unit.count}</strong>
            </div>
            <div class="progress-bar">
              <span style="width: ${occupancy}%"></span>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderTenants() {
  const target = document.getElementById("tenantGrid");

  if (!target) {
    return;
  }

  target.innerHTML = tenants
    .map(
      (tenant) => `
        <article class="resource-card">
          <div class="resource-card__header">
            <div>
              <h4>${tenant.name}</h4>
              <p>${tenant.property} • ${tenant.unit}</p>
            </div>
            <span class="status-badge status-badge--${badgeTone(tenant.status)}">${tenant.status}</span>
          </div>

          <div class="meta-inline">
            <span class="meta-tag">${tenant.autopay ? "Autopay" : "Manual pay"}</span>
            <span class="meta-tag">Risk: ${tenant.risk}</span>
          </div>

          <div class="resource-card__footer">
            <div>
              <span class="section-copy">Lease end</span>
              <div class="resource-card__value">${tenant.leaseEnd}</div>
            </div>
            <div class="resource-card__balance ${tenant.balance > 0 ? "resource-card__balance--warning" : ""}">
              ${tenant.balance > 0 ? formatCurrency(tenant.balance) : "No balance"}
            </div>
          </div>
        </article>
      `
    )
    .join("");
}

function renderRenewals() {
  const target = document.getElementById("renewalList");

  if (!target) {
    return;
  }

  target.innerHTML = renewalQueue
    .map(
      (renewal) => `
        <article class="note-item">
          <div class="note-item__header">
            <div>
              <h4>${renewal.name}</h4>
              <p>${renewal.unit} • Renewal due ${renewal.date}</p>
            </div>
            <span class="status-badge status-badge--${renewal.tone}">${renewal.date}</span>
          </div>
          <p>${renewal.action}</p>
        </article>
      `
    )
    .join("");
}

function renderAutomationRules() {
  const target = document.getElementById("automationList");

  if (!target) {
    return;
  }

  target.innerHTML = automationRules
    .map(
      (rule) => `
        <article class="resource-card">
          <div class="resource-card__header">
            <div>
              <h4>${rule.title}</h4>
              <p>${rule.channel}</p>
            </div>
            <span class="status-badge status-badge--${badgeTone(rule.status)}">${rule.status}</span>
          </div>
          <p>${rule.cadence}</p>
        </article>
      `
    )
    .join("");
}

function renderVendorPerformance() {
  const target = document.getElementById("vendorList");

  if (!target) {
    return;
  }

  target.innerHTML = vendorPerformance
    .map(
      (vendor) => `
        <article class="resource-card">
          <div class="resource-card__header">
            <div>
              <h4>${vendor.name}</h4>
              <p>${vendor.specialty}</p>
            </div>
            <span class="status-badge status-badge--stable">SLA ${vendor.sla}</span>
          </div>
          <div class="resource-card__footer">
            <div>
              <span class="section-copy">Resident rating</span>
              <div class="resource-card__value">${vendor.rating}</div>
            </div>
            <div class="meta-tag">${vendor.note}</div>
          </div>
        </article>
      `
    )
    .join("");
}

function renderCommunicationFeed() {
  const target = document.getElementById("communicationList");

  if (!target) {
    return;
  }

  target.innerHTML = communicationFeed
    .map(
      (item) => `
        <article class="resource-card">
          <div class="resource-card__header">
            <div>
              <h4>${item.title}</h4>
              <p>${item.channel} • ${item.audience}</p>
            </div>
            <span class="status-badge status-badge--stable">${item.time}</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderSettingsCards() {
  const target = document.getElementById("settingsGrid");

  if (!target) {
    return;
  }

  target.innerHTML = settingsCards
    .map(
      (setting) => `
        <article class="resource-card settings-card">
          <div class="toggle-row">
            <div>
              <h4>${setting.title}</h4>
              <p>${setting.description}</p>
            </div>
            <button class="toggle-btn${setting.enabled ? " is-active" : ""}" aria-pressed="${setting.enabled}" aria-label="Toggle ${setting.title}">
              <span></span>
            </button>
          </div>
        </article>
      `
    )
    .join("");
}

function renderIntegrations() {
  const target = document.getElementById("integrationList");

  if (!target) {
    return;
  }

  target.innerHTML = integrations
    .map(
      (item) => `
        <article class="resource-card">
          <div class="resource-card__header">
            <div>
              <h4>${item.name}</h4>
              <p>${item.detail}</p>
            </div>
            <span class="status-badge status-badge--${badgeTone(item.status)}">${item.status}</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderAccessRoles() {
  const target = document.getElementById("accessList");

  if (!target) {
    return;
  }

  target.innerHTML = accessRoles
    .map(
      (role) => `
        <article class="resource-card">
          <div class="resource-card__header">
            <div>
              <h4>${role.role}</h4>
              <p>${role.permission}</p>
            </div>
            <span class="status-badge status-badge--stable">${role.members} members</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderBenchmarkCards() {
  const target = document.getElementById("benchmarkList");

  if (!target) {
    return;
  }

  target.innerHTML = benchmarkCards
    .map(
      (item) => `
        <article class="resource-card">
          <div>
            <h4>${item.title}</h4>
            <p>${item.detail}</p>
          </div>
          <div class="resource-card__value">${item.value}</div>
        </article>
      `
    )
    .join("");
}

function updateInsightCard() {
  const title = document.getElementById("insightTitle");
  const copy = document.getElementById("insightCopy");

  if (!title || !copy) {
    return;
  }

  const atRisk = properties
    .filter((property) => property.occupancy < 85)
    .sort((left, right) => left.occupancy - right.occupancy)[0];

  const overdueCount = rentActivity.filter((item) => item.status === "Overdue").length;

  if (atRisk) {
    title.textContent = `${atRisk.name} needs proactive leasing support`;
    copy.textContent = `${atRisk.name} is sitting at ${atRisk.occupancy}% occupancy while ${overdueCount} rent accounts are already overdue across the portfolio. Launch a 14-day renewal and broker outreach sprint to protect April cash flow before vacancy pressure expands.`;
  } else {
    title.textContent = "Collections are outpacing expected risk";
    copy.textContent = "Occupancy is stable across the portfolio, so the next best move is increasing autopay enrollment for tenants with pending balances to tighten collection timing.";
  }
}

function bindPropertyFilters() {
  const propertySearch = document.getElementById("propertySearch");
  const propertyFilter = document.getElementById("propertyFilter");
  const propertyViewSelect = document.getElementById("propertyViewSelect");

  if (!propertySearch || !propertyFilter) {
    return;
  }

  function applyFilters() {
    const query = propertySearch.value.trim().toLowerCase();
    const status = propertyFilter.value;

    const filtered = properties.filter((property) => {
      const matchesQuery =
        property.name.toLowerCase().includes(query) ||
        property.location.toLowerCase().includes(query);
      const matchesStatus = status === "all" || property.status === status;
      return matchesQuery && matchesStatus;
    });

    renderProperties(filtered, { targetId: "propertyGrid" });
  }

  propertySearch.addEventListener("input", applyFilters);
  propertyFilter.addEventListener("change", applyFilters);
  propertyViewSelect?.addEventListener("change", () => {
    propertyViewMode = propertyViewSelect.value;
    applyFilters();
  });
}

function initHeaderActions() {
  document.querySelectorAll("[data-action='add-property']").forEach((button) => {
    button.addEventListener("click", () => {
      window.location.href = "/landlord/properties/new/";
    });
  });
}

function animateMetricValues() {
  const metrics = document.querySelectorAll(".metric-value");

  metrics.forEach((metric) => {
    const targetValue = Number(metric.dataset.value);
    const format = metric.dataset.format;
    const duration = 1400;
    const start = performance.now();

    function tick(timestamp) {
      const progress = Math.min((timestamp - start) / duration, 1);
      const current = targetValue * (1 - Math.pow(1 - progress, 3));

      if (format === "currency") {
        metric.textContent = formatCompactCurrency(current);
      } else if (format === "percent") {
        metric.textContent = `${current.toFixed(1)}%`;
      } else if (format === "decimal") {
        metric.textContent = current.toFixed(1);
      } else {
        metric.textContent = Math.round(current).toLocaleString();
      }

      if (progress < 1) {
        window.requestAnimationFrame(tick);
      }
    }

    window.requestAnimationFrame(tick);
  });
}

function initRevealAnimation() {
  const revealItems = document.querySelectorAll(".reveal");

  if (!("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.16 }
  );

  revealItems.forEach((item, index) => {
    item.style.transitionDelay = `${Math.min(index * 60, 320)}ms`;
    observer.observe(item);
  });
}

function initSidebar() {
  const openSidebarButton = document.getElementById("openSidebar");
  const closeSidebarButton = document.getElementById("closeSidebar");
  const appOverlay = document.getElementById("appOverlay");
  const navLinks = document.querySelectorAll(".nav-link");

  function openSidebar() {
    document.body.classList.add("sidebar-open");
  }

  function closeSidebar() {
    document.body.classList.remove("sidebar-open");
  }

  openSidebarButton?.addEventListener("click", openSidebar);
  closeSidebarButton?.addEventListener("click", closeSidebar);
  appOverlay?.addEventListener("click", closeSidebar);

  navLinks.forEach((link) => {
    link.addEventListener("click", closeSidebar);
  });
}

function initToggleButtons() {
  document.querySelectorAll(".toggle-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const next = !button.classList.contains("is-active");
      button.classList.toggle("is-active", next);
      button.setAttribute("aria-pressed", String(next));
    });
  });
}

function initCharts() {
  if (typeof Chart === "undefined") {
    return;
  }

  Chart.defaults.font.family = "'Manrope', sans-serif";
  Chart.defaults.color = "#596782";

  const rentCanvas = document.getElementById("rentChart");
  if (rentCanvas) {
    const rentContext = rentCanvas.getContext("2d");
    const rentGradient = rentContext.createLinearGradient(0, 0, 0, 360);
    rentGradient.addColorStop(0, "rgba(47, 116, 255, 0.28)");
    rentGradient.addColorStop(1, "rgba(47, 116, 255, 0.02)");

    new Chart(rentCanvas, {
      type: "line",
      data: {
        labels: rentTrend.labels,
        datasets: [
          {
            label: "Expected rent",
            data: rentTrend.expected,
            borderColor: "rgba(255, 178, 77, 0.95)",
            backgroundColor: "rgba(255, 178, 77, 0.08)",
            borderWidth: 2,
            borderDash: [6, 6],
            fill: false,
            tension: 0.38,
            pointRadius: 0,
            pointHoverRadius: 4
          },
          {
            label: "Collected rent",
            data: rentTrend.collected,
            borderColor: "#2f74ff",
            backgroundColor: rentGradient,
            borderWidth: 3,
            fill: true,
            tension: 0.38,
            pointBackgroundColor: "#ffffff",
            pointBorderColor: "#2f74ff",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false
        },
        plugins: {
          legend: {
            labels: {
              usePointStyle: true,
              pointStyle: "circle",
              padding: 20
            }
          },
          tooltip: {
            callbacks: {
              label(context) {
                return `${context.dataset.label}: KSh ${context.raw.toFixed(2)}M`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: "#7b89a4"
            }
          },
          y: {
            beginAtZero: false,
            grid: {
              color: "rgba(24, 35, 56, 0.08)"
            },
            ticks: {
              callback(value) {
                return `KSh ${value}M`;
              }
            }
          }
        }
      }
    });
  }

  const occupancyCanvas = document.getElementById("occupancyChart");
  if (occupancyCanvas) {
    new Chart(occupancyCanvas, {
      type: "doughnut",
      data: {
        labels: occupancyBreakdown.map((item) => item.label),
        datasets: [
          {
            data: occupancyBreakdown.map((item) => item.value),
            backgroundColor: occupancyBreakdown.map((item) => item.color),
            borderWidth: 0,
            hoverOffset: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "72%",
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

  const maintenanceCanvas = document.getElementById("maintenanceChart");
  if (maintenanceCanvas) {
    new Chart(maintenanceCanvas, {
      type: "bar",
      data: {
        labels: maintenanceCategories.labels,
        datasets: [
          {
            label: "Open issues",
            data: maintenanceCategories.values,
            backgroundColor: ["#2f74ff", "#4d93ff", "#1bc6a6", "#ffb24d", "#8cb8ff"],
            borderRadius: 14,
            borderSkipped: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            }
          },
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1
            },
            grid: {
              color: "rgba(24, 35, 56, 0.08)"
            }
          }
        }
      }
    });
  }

  const paymentMethodCanvas = document.getElementById("paymentMethodChart");
  if (paymentMethodCanvas) {
    new Chart(paymentMethodCanvas, {
      type: "doughnut",
      data: {
        labels: paymentMethods.map((item) => item.label),
        datasets: [
          {
            data: paymentMethods.map((item) => item.value),
            backgroundColor: paymentMethods.map((item) => item.color),
            borderWidth: 0,
            hoverOffset: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

  const tenantStatusCanvas = document.getElementById("tenantStatusChart");
  if (tenantStatusCanvas) {
    new Chart(tenantStatusCanvas, {
      type: "doughnut",
      data: {
        labels: tenantSegments.map((item) => item.label),
        datasets: [
          {
            data: tenantSegments.map((item) => item.value),
            backgroundColor: tenantSegments.map((item) => item.color),
            borderWidth: 0,
            hoverOffset: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }
}

function hydratePage() {
  if (currentPage === "overview") {
    renderProperties(properties, { targetId: "propertyGrid", limit: 3 });
    renderActivity("activityTableBody", 5);
    renderTickets("ticketList", 4);
    renderAlerts("alertsList", 4);
  }

  if (currentPage === "properties") {
    renderProperties(properties, { targetId: "propertyGrid" });
    renderUnitMix();
  }

  if (currentPage === "tenants") {
    renderTenants();
    renderRenewals();
  }

  if (currentPage === "payments") {
    renderActivity("activityTableBody", rentActivity.length);
    renderLegend("paymentMethodLegend", paymentMethods, (item) => `${item.value}%`);
  }

  if (currentPage === "maintenance") {
    renderTickets("ticketList", maintenanceTickets.length);
    renderVendorPerformance();
  }

  if (currentPage === "analytics") {
    renderBenchmarkCards();
  }

  if (currentPage === "notifications") {
    renderAlerts("alertsList", alerts.length);
    renderAutomationRules();
    renderCommunicationFeed();
  }

  if (currentPage === "settings") {
    renderSettingsCards();
    renderIntegrations();
    renderAccessRoles();
  }

  renderLegend("occupancyLegend", occupancyBreakdown, (item) => item.value);
  renderLegend("tenantStatusLegend", tenantSegments, (item) => item.value);
  updateInsightCard();
  bindPropertyFilters();
  initToggleButtons();
  animateMetricValues();
  initRevealAnimation();
  initSidebar();
  initCharts();
}

function initDashboard() {
  renderShell();
  initHeaderActions();
  hydratePage();
}

document.addEventListener("DOMContentLoaded", initDashboard);
