const SmartRentMain = (() => {
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

  const paymentMethods = [
    { label: "Autopay", value: 61, color: "#2f74ff" },
    { label: "Bank Transfer", value: 21, color: "#1bc6a6" },
    { label: "Mobile Money", value: 12, color: "#ffb24d" },
    { label: "Cash", value: 6, color: "#ec5f67" }
  ];
  const rentTrend = {
    labels: ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
    expected: [2.52, 2.58, 2.66, 2.73, 2.81, 2.9],
    collected: [2.31, 2.4, 2.48, 2.6, 2.74, 2.84]
  };
  const maintenanceTickets = [
    { title: "Water pressure issue", property: "Riverpoint Residences", unit: "House 8", priority: "High", assignee: "Kevin Otieno", eta: "Today 4 PM" },
    { title: "Power socket replacement", property: "Maple Court Lofts", unit: "House 12", priority: "Medium", assignee: "Lisa Wambui", eta: "Tomorrow 11 AM" },
    { title: "Bathroom leak", property: "Skyline Suites", unit: "House 4", priority: "High", assignee: "Kevin Otieno", eta: "Today 6 PM" },
    { title: "Window latch repair", property: "Bluehaven Apartments", unit: "House 11", priority: "Low", assignee: "James Kariuki", eta: "Mon 10 AM" }
  ];
  const vendorPerformance = [
    { name: "Kevin Otieno", specialty: "Plumbing", sla: "96%", rating: "4.9/5", note: "Fastest emergency response" },
    { name: "Lisa Wambui", specialty: "Electrical", sla: "93%", rating: "4.8/5", note: "Strong resident feedback" },
    { name: "James Kariuki", specialty: "General repairs", sla: "91%", rating: "4.6/5", note: "Reliable scheduling" },
    { name: "Apex Facilities", specialty: "HVAC", sla: "89%", rating: "4.5/5", note: "Best for bulk work" }
  ];
  const maintenanceCategories = { labels: ["Plumbing", "Electrical", "Locks", "Appliances", "HVAC"], values: [5, 3, 2, 2, 2] };
  const notificationsAlerts = [
    { type: "warning", icon: "fa-solid fa-triangle-exclamation", title: "Overdue follow-up needed", description: "Two tenants have crossed the 3-day overdue threshold and now require escalation.", time: "12 min ago" },
    { type: "success", icon: "fa-solid fa-circle-check", title: "Payment confirmed", description: "Riverpoint autopay collected successfully for 14 tenants overnight.", time: "43 min ago" },
    { type: "info", icon: "fa-solid fa-bell", title: "Renewal window opened", description: "Three leases are now inside the 45-day renewal horizon and are ready for outreach.", time: "Today" }
  ];
  const automationRules = [
    { title: "Rent reminder cadence", channel: "SMS and email", status: "Live", cadence: "Runs 3 days before due date, due date, and 2 days overdue." },
    { title: "Owner digest", channel: "Weekly email", status: "Scheduled", cadence: "Summarizes collections, occupancy, and service load every Friday at 8:00 AM." },
    { title: "Maintenance escalation", channel: "Internal alert", status: "Live", cadence: "Escalates unresolved high-priority tickets after 8 hours." }
  ];
  const communicationFeed = [
    { title: "Autopay confirmation batch", channel: "Email", audience: "14 tenants", time: "8:06 AM" },
    { title: "Renewal reminder", channel: "SMS", audience: "3 tenants", time: "9:20 AM" },
    { title: "Owner summary", channel: "Email", audience: "Portfolio owners", time: "Friday 8:00 AM" }
  ];
  const settingsCards = [
    { title: "Dark mode", description: "Keep the landlord workspace visually consistent at night.", enabled: true },
    { title: "Owner digest emails", description: "Send weekly portfolio snapshots automatically.", enabled: true },
    { title: "Maintenance escalation", description: "Escalate high-priority tickets when SLA risk appears.", enabled: true },
    { title: "Autopay nudges", description: "Prompt tenants to switch from manual payment to autopay.", enabled: false }
  ];
  const integrations = [
    { name: "M-Pesa Collections", detail: "Primary recurring payment rail for tenant collections.", status: "Connected" },
    { name: "Bank Settlement Feed", detail: "Daily payout sync for verified bank transfers.", status: "Healthy" },
    { name: "Email Delivery", detail: "System reminders and owner reports.", status: "Synced" },
    { name: "SMS Messaging", detail: "Tenant reminders and renewal nudges.", status: "Healthy" }
  ];
  const accessRoles = [
    { role: "Landlord", permission: "Full portfolio control, settings, and reporting.", members: 1 },
    { role: "Portfolio Manager", permission: "Operations, leasing, and maintenance oversight.", members: 2 },
    { role: "Accountant", permission: "Collections, exports, and payment review.", members: 1 },
    { role: "Maintenance Coordinator", permission: "Tickets, vendors, and SLA monitoring.", members: 2 }
  ];

  function formatCurrency(value) {
    return currencyFormatter.format(value).replace("KES", "KSh");
  }

  function formatCompactCurrency(value) {
    return compactCurrencyFormatter.format(value).replace("KES", "KSh");
  }

  function renderLegend(targetId, items, formatter = (item) => item.value) {
    const target = document.getElementById(targetId);
    if (!target) return;
    target.innerHTML = items.map((item) => `
      <div class="occupancy-legend__item">
        <div class="occupancy-legend__meta">
          <span class="occupancy-dot" style="background:${item.color}"></span>
          <span>${item.label}</span>
        </div>
        <strong>${formatter(item)}</strong>
      </div>
    `).join("");
  }

  function initSidebar() {
    const openButton = document.getElementById("openSidebar");
    const closeButton = document.getElementById("closeSidebar");
    const overlay = document.getElementById("appOverlay");
    const close = () => document.body.classList.remove("sidebar-open");
    openButton?.addEventListener("click", () => document.body.classList.add("sidebar-open"));
    closeButton?.addEventListener("click", close);
    overlay?.addEventListener("click", close);
    document.querySelectorAll(".nav-link").forEach((link) => link.addEventListener("click", close));
  }

  function initTheme() {
    if (window.SmartRentTheme) {
      window.SmartRentTheme.bindToggles();
    }
  }

  function initRevealAnimation() {
    const revealItems = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      revealItems.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.16 });
    revealItems.forEach((item, index) => {
      item.style.transitionDelay = `${Math.min(index * 60, 320)}ms`;
      observer.observe(item);
    });
  }

  function animateMetrics() {
    document.querySelectorAll(".metric-value[data-value]").forEach((metric) => {
      const targetValue = Number(metric.dataset.value);
      const format = metric.dataset.format;
      const start = performance.now();
      const duration = 1400;
      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
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
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  function applyChartThemeDefaults() {
    if (typeof Chart === "undefined") return {};
    Chart.defaults.font.family = "'Manrope', sans-serif";
    const root = getComputedStyle(document.documentElement);
    Chart.defaults.color = root.getPropertyValue("--text-muted").trim() || "#596782";
    const stroke = root.getPropertyValue("--stroke").trim();
    if (stroke) Chart.defaults.borderColor = stroke;
    return {
      tick: root.getPropertyValue("--text-soft").trim() || "#7b89a4",
      grid: root.getPropertyValue("--stroke").trim() || "rgba(24, 35, 56, 0.08)"
    };
  }

  function renderPagination(targetId, currentPage, totalPages, onPageChange) {
    const target = document.getElementById(targetId);
    if (!target) return;
    if (totalPages <= 1) {
      target.innerHTML = "";
      return;
    }
    target.innerHTML = `
      <div class="pagination">
        <button type="button" class="pagination__btn" ${currentPage === 1 ? "disabled" : ""} data-page="${currentPage - 1}">Previous</button>
        <span class="pagination__meta">Page ${currentPage} of ${totalPages}</span>
        <button type="button" class="pagination__btn" ${currentPage === totalPages ? "disabled" : ""} data-page="${currentPage + 1}">Next</button>
      </div>
    `;
    target.querySelectorAll("[data-page]").forEach((button) => {
      button.addEventListener("click", () => onPageChange(Number(button.dataset.page)));
    });
  }

  function renderRentChart(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;
    const colors = applyChartThemeDefaults();
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 360);
    gradient.addColorStop(0, "rgba(47, 116, 255, 0.28)");
    gradient.addColorStop(1, "rgba(47, 116, 255, 0.02)");
    new Chart(canvas, {
      type: "line",
      data: {
        labels: rentTrend.labels,
        datasets: [
          { label: "Expected rent", data: rentTrend.expected, borderColor: "rgba(255, 178, 77, 0.95)", borderDash: [6, 6], borderWidth: 2, fill: false, tension: 0.38, pointRadius: 0 },
          { label: "Collected rent", data: rentTrend.collected, borderColor: "#2f74ff", backgroundColor: gradient, borderWidth: 3, fill: true, tension: 0.38, pointRadius: 4 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { labels: { usePointStyle: true, pointStyle: "circle", padding: 20 } } },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.tick } },
          y: { grid: { color: colors.grid }, ticks: { color: colors.tick, callback(value) { return `KSh ${value}M`; } } }
        }
      }
    });
  }

  function renderDoughnut(canvasId, items, cutout = "68%") {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;
    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: items.map((item) => item.label),
        datasets: [{ data: items.map((item) => item.value), backgroundColor: items.map((item) => item.color), borderWidth: 0, hoverOffset: 6 }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout, plugins: { legend: { display: false } } }
    });
  }

  function renderBarChart(canvasId, labels, values) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;
    const colors = applyChartThemeDefaults();
    new Chart(canvas, {
      type: "bar",
      data: { labels, datasets: [{ label: "Open issues", data: values, backgroundColor: ["#2f74ff", "#4d93ff", "#1bc6a6", "#ffb24d", "#8cb8ff"], borderRadius: 14, borderSkipped: false }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, ticks: { stepSize: 1, color: colors.tick }, grid: { color: colors.grid } }
        }
      }
    });
  }

  function initOverviewPage() {
    if (!document.body.dataset.page || document.body.dataset.page !== "overview") return;
    const occupancy = [
      { label: "Occupied", value: 152, color: "#2f74ff" },
      { label: "Vacant", value: 22, color: "#ffb24d" },
      { label: "Reserved", value: 0, color: "#1bc6a6" }
    ];
    renderRentChart("rentChart");
    renderDoughnut("occupancyChart", occupancy, "72%");
    renderLegend("occupancyLegend", occupancy, (item) => item.value);
  }

  function initPropertiesPage() {
    const propertyGrid = document.getElementById("propertyGrid");
    if (!propertyGrid || !document.getElementById("server-properties-data")) return;

    const propertyData = JSON.parse(document.getElementById("server-properties-data").textContent);
    const dashboardData = JSON.parse(document.getElementById("property-dashboard-data").textContent);
    let viewMode = localStorage.getItem("propertyViewMode") || "list";
    let currentPage = 1;
    const perPage = 6;

    function statusClassName(status) {
      return status.toLowerCase().replace(/\s+/g, "-");
    }

    function getActions(property, compact = false) {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";
      return `
        <div class="property-actions${compact ? " property-actions--compact" : ""}">
          <a href="${property.detailUrl}" class="btn btn--ghost btn--sm property-action-btn"><i class="fa-solid fa-eye"></i><span>View</span></a>
          <a href="${property.editUrl}" class="btn btn--secondary btn--sm property-action-btn"><i class="fa-solid fa-pen-to-square"></i><span>Edit</span></a>
          <form method="post" action="${property.deleteUrl}" class="property-actions__form" onsubmit="return confirm(${JSON.stringify(`Delete ${property.name}?`)});">
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
            <button type="submit" class="btn btn--ghost btn--sm btn--danger property-action-btn"><i class="fa-solid fa-trash-can"></i><span>Delete</span></button>
          </form>
        </div>
      `;
    }

    function renderUnitMix() {
      const target = document.getElementById("unitList");
      if (!target) return;
      target.innerHTML = dashboardData.unitMix.map((unit) => {
        const occupancy = unit.count ? Math.round((unit.occupied / unit.count) * 100) : 0;
        const tone = occupancy >= 90 ? "high-performing" : occupancy >= 80 ? "stable" : "needs-attention";
        return `
          <article class="resource-card">
            <div class="resource-card__header"><div><h4>${unit.label}</h4><p>${unit.count} units • Rent ${formatCurrency(unit.avgRent)} • Buy ${formatCurrency(unit.avgBuyingPrice)}</p></div><span class="status-badge status-badge--${tone}">${occupancy}% leased</span></div>
            <div class="progress-group"><div class="progress-group__label"><span>Leased units</span><strong>${unit.occupied}/${unit.count}</strong></div><div class="progress-bar"><span style="width:${occupancy}%"></span></div></div>
          </article>
        `;
      }).join("");
    }

    function renderList(items) {
      return `
        <div class="property-table-wrap">
          <table class="property-table">
            <thead><tr><th>Property</th><th>Location</th><th>Status</th><th>Units</th><th>Occupied</th><th>Occupancy</th><th>Revenue</th><th>Trend</th><th>Actions</th></tr></thead>
            <tbody>
              ${items.map((property) => `
                <tr>
                  <td><div class="table-tenant"><strong>${property.name}</strong><span>${property.location}</span></div></td>
                  <td>${property.location}</td>
                  <td><span class="status-badge status-badge--${statusClassName(property.status)}">${property.status}</span></td>
                  <td>${property.units}</td>
                  <td>${property.occupiedUnits}</td>
                  <td>${property.occupancy}%</td>
                  <td>${formatCompactCurrency(property.revenue)}</td>
                  <td><span class="${property.trend < 0 ? "property-card__trend property-card__trend--down" : "property-card__trend"}"><i class="fa-solid ${property.trend < 0 ? "fa-arrow-trend-down" : "fa-arrow-trend-up"}"></i>${Math.abs(property.trend)}%</span></td>
                  <td>${getActions(property, true)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderGrid(items) {
      return items.map((property) => `
        <article class="property-card">
          <div class="property-card__top"><div class="property-card__title"><h4>${property.name}</h4><p><i class="fa-solid fa-location-dot"></i> ${property.location}</p></div><span class="status-badge status-badge--${statusClassName(property.status)}">${property.status}</span></div>
          <div class="property-card__meta"><div class="meta-stack"><span>Units</span><strong>${property.units}</strong></div><div class="meta-stack"><span>Occupied</span><strong>${property.occupiedUnits}</strong></div></div>
          <div class="progress-group"><div class="progress-group__label"><span>Occupancy progress</span><strong>${property.occupancy}%</strong></div><div class="progress-bar"><span style="width:${property.occupancy}%"></span></div></div>
          <div class="property-card__footer"><div><span class="section-copy">Monthly revenue</span><div class="property-card__revenue">${formatCompactCurrency(property.revenue)}</div></div><span class="${property.trend < 0 ? "property-card__trend property-card__trend--down" : "property-card__trend"}"><i class="fa-solid ${property.trend < 0 ? "fa-arrow-trend-down" : "fa-arrow-trend-up"}"></i>${Math.abs(property.trend)}%</span></div>
          <div class="property-card__actions">${getActions(property)}</div>
        </article>
      `).join("");
    }

    function getFilteredProperties() {
      const query = (document.getElementById("propertySearch")?.value || "").trim().toLowerCase();
      const status = document.getElementById("propertyFilter")?.value || "all";
      return propertyData.filter((property) => {
        const queryMatch = property.name.toLowerCase().includes(query) || property.location.toLowerCase().includes(query);
        const statusMatch = status === "all" || property.status === status;
        return queryMatch && statusMatch;
      });
    }

    function renderProperties() {
      const items = getFilteredProperties();
      const totalPages = Math.max(1, Math.ceil(items.length / perPage));
      currentPage = Math.min(currentPage, totalPages);
      const start = (currentPage - 1) * perPage;
      const pageItems = items.slice(start, start + perPage);
      propertyGrid.classList.toggle("properties-grid--list", viewMode === "list");
      propertyGrid.innerHTML = pageItems.length ? (viewMode === "list" ? renderList(pageItems) : renderGrid(pageItems)) : `<article class="property-card"><div class="property-card__title"><h4>No properties found</h4><p>Try a different search term or clear the filter.</p></div></article>`;
      renderPagination("propertyPagination", currentPage, totalPages, (page) => {
        currentPage = page;
        renderProperties();
      });
    }

    document.getElementById("propertyViewSelect")?.addEventListener("change", (event) => {
      viewMode = event.target.value;
      localStorage.setItem("propertyViewMode", viewMode);
      currentPage = 1;
      renderProperties();
    });
    document.getElementById("propertySearch")?.addEventListener("input", () => {
      currentPage = 1;
      renderProperties();
    });
    document.getElementById("propertyFilter")?.addEventListener("change", () => {
      currentPage = 1;
      renderProperties();
    });
    const viewSelect = document.getElementById("propertyViewSelect");
    if (viewSelect) viewSelect.value = viewMode;

    renderProperties();
    renderUnitMix();
    renderDoughnut("occupancyChart", dashboardData.occupancyBreakdown, "72%");
    renderLegend("occupancyLegend", dashboardData.occupancyBreakdown, (item) => item.value);
  }

  function initTenantsPage() {
    const tenantDirectory = document.getElementById("tenantDirectory");
    if (!tenantDirectory || !document.getElementById("tenant-data")) return;
    const tenants = JSON.parse(document.getElementById("tenant-data").textContent);
    const dashboardData = JSON.parse(document.getElementById("tenant-dashboard-data").textContent);
    let viewMode = localStorage.getItem("tenantViewMode") || "list";
    let currentPage = 1;
    const perPage = 6;

    function toneForStatus(status) {
      if (status === "Good Standing") return "high-performing";
      if (status === "Renewing Soon") return "needs-attention";
      return "vacancy-risk";
    }

    function getFilteredTenants() {
      const query = (document.getElementById("tenantSearch")?.value || "").trim().toLowerCase();
      return tenants.filter((tenant) =>
        [tenant.name, tenant.property, tenant.unit, tenant.unitType].join(" ").toLowerCase().includes(query)
      );
    }

    function getTenantActions(tenant, compact = false) {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";
      return `
        <div class="property-actions${compact ? " property-actions--compact" : ""}">
          <a href="${tenant.detailUrl}" class="btn btn--ghost btn--sm property-action-btn"><i class="fa-solid fa-eye"></i><span>View</span></a>
          <a href="${tenant.editUrl}" class="btn btn--secondary btn--sm property-action-btn"><i class="fa-solid fa-pen-to-square"></i><span>Edit</span></a>
          <form method="post" action="${tenant.deleteUrl}" class="property-actions__form" onsubmit="return confirm(${JSON.stringify(`Delete ${tenant.name}?`)});">
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
            <button type="submit" class="btn btn--ghost btn--sm btn--danger property-action-btn"><i class="fa-solid fa-trash-can"></i><span>Delete</span></button>
          </form>
        </div>
      `;
    }

    function renderList(items) {
      return `
        <div class="property-table-wrap">
          <table class="property-table">
            <thead><tr><th>Tenant</th><th>Property</th><th>Unit Type</th><th>House</th><th>Lease Type</th><th>Status</th><th>Lease End</th><th>Balance</th><th>Actions</th></tr></thead>
            <tbody>
              ${items.map((tenant) => `
                <tr>
                  <td class="tenant-name-cell"><div class="table-tenant table-tenant--nowrap"><strong title="${tenant.name}">${tenant.name}</strong><span>${tenant.risk} risk</span></div></td>
                  <td>${tenant.property}</td>
                  <td>${tenant.unitType || "Not set"}</td>
                  <td>${tenant.unit}</td>
                  <td>${tenant.leaseType}</td>
                  <td><span class="status-badge status-badge--${toneForStatus(tenant.status)}">${tenant.status}</span></td>
                  <td>${tenant.lease_end}</td>
                  <td>${tenant.balance > 0 ? formatCurrency(tenant.balance) : "No balance"}</td>
                  <td>${getTenantActions(tenant, true)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderGrid(items) {
      return `<div class="resource-grid">${items.map((tenant) => `
        <article class="resource-card">
          <div class="resource-card__header"><div><h4>${tenant.name}</h4><p>${tenant.property} • ${tenant.unit}</p></div><span class="status-badge status-badge--${toneForStatus(tenant.status)}">${tenant.status}</span></div>
          <div class="meta-inline"><span class="meta-tag">${tenant.unitType || "Unit type pending"}</span><span class="meta-tag">${tenant.leaseType}</span></div>
          <div class="resource-card__footer"><div><span class="section-copy">Lease end</span><div class="resource-card__value">${tenant.lease_end}</div></div><div class="resource-card__balance${tenant.balance > 0 ? " resource-card__balance--warning" : ""}">${tenant.balance > 0 ? formatCurrency(tenant.balance) : "No balance"}</div></div>
          <div class="property-card__actions">${getTenantActions(tenant)}</div>
        </article>
      `).join("")}</div>`;
    }

    function renderTenants() {
      const filtered = getFilteredTenants();
      const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
      currentPage = Math.min(currentPage, totalPages);
      const pageItems = filtered.slice((currentPage - 1) * perPage, currentPage * perPage);
      tenantDirectory.innerHTML = pageItems.length ? (viewMode === "list" ? renderList(pageItems) : renderGrid(pageItems)) : `<article class="resource-card"><div class="resource-card__header"><div><h4>No tenants found</h4><p>Try a different search term or add a tenant to begin.</p></div></div></article>`;
      renderPagination("tenantPagination", currentPage, totalPages, (page) => {
        currentPage = page;
        renderTenants();
      });
    }

    document.getElementById("tenantViewSelect")?.addEventListener("change", (event) => {
      viewMode = event.target.value;
      localStorage.setItem("tenantViewMode", viewMode);
      currentPage = 1;
      renderTenants();
    });
    document.getElementById("tenantSearch")?.addEventListener("input", () => {
      currentPage = 1;
      renderTenants();
    });
    const viewSelect = document.getElementById("tenantViewSelect");
    if (viewSelect) viewSelect.value = viewMode;

    renderTenants();
    renderLegend("tenantStatusLegend", dashboardData.segments, (item) => item.value);
    renderDoughnut("tenantStatusChart", dashboardData.segments, "68%");
  }

  function initPaymentsPage() {
    const paymentActivity = document.getElementById("activityTableBody");
    const paymentsNode = document.getElementById("payments-dashboard-data");
    if (!paymentActivity || !paymentsNode) return;
    const paymentsData = JSON.parse(paymentsNode.textContent);
    const rows = paymentsData.payments || [];
    const search = document.getElementById("paymentSearch");
    function renderRows() {
      const query = (search?.value || "").trim().toLowerCase();
      paymentActivity.innerHTML = rows.filter((row) =>
        [row.tenant, row.property, row.unit, row.status, row.category, row.method].join(" ").toLowerCase().includes(query)
      ).map((row) => `
        <tr><td><div class="table-tenant"><strong>${row.tenant}</strong><span>${row.property}</span></div></td><td>${row.unit}</td><td>${formatCurrency(row.amount)}</td><td><small>${row.date}</small></td><td><span class="table-status table-status--${row.status.toLowerCase()}">${row.status}</span></td></tr>
      `).join("");
    }
    search?.addEventListener("input", renderRows);
    renderRows();
    renderRentChart("rentChart");
    renderDoughnut("paymentMethodChart", paymentsData.payment_methods, "68%");
    renderLegend("paymentMethodLegend", paymentsData.payment_methods, (item) => item.value);
  }

  function initMaintenancePage() {
    const ticketList = document.getElementById("ticketList");
    const maintenanceNode = document.getElementById("maintenance-dashboard-data");
    if (!ticketList || !maintenanceNode) return;
    const maintenanceData = JSON.parse(maintenanceNode.textContent);
    ticketList.innerHTML = maintenanceData.complaints.map((ticket) => `
      <article class="ticket-card"><div class="ticket-card__header"><div><h4>${ticket.title}</h4><p>${ticket.property} • ${ticket.unit}</p></div><span class="priority-badge priority-badge--${ticket.status.toLowerCase().replace(/\s+/g, "-")}">${ticket.status}</span></div><div class="ticket-card__meta"><span><i class="fa-solid fa-user"></i> ${ticket.tenant}</span><span><i class="fa-regular fa-clock"></i> ${ticket.created_at}</span></div></article>
    `).join("");
    const vendorList = document.getElementById("vendorList");
    if (vendorList) {
      vendorList.innerHTML = maintenanceData.complaints.map((item) => `
        <article class="resource-card"><div class="resource-card__header"><div><h4>${item.title}</h4><p>${item.category} • ${item.tenant}</p></div><span class="status-badge status-badge--stable">${item.status}</span></div><div class="resource-card__footer"><div><span class="section-copy">Property</span><div class="resource-card__value">${item.property}</div></div><div class="meta-tag">${item.unit}</div></div></article>
      `).join("");
    }
    renderBarChart("maintenanceChart", maintenanceData.categories.labels, maintenanceData.categories.values);
  }

  function initTenantComplaintsPage() {
    const target = document.getElementById("tenantComplaintsTable");
    const complaintsNode = document.getElementById("tenant-complaints-data");
    if (!target || !complaintsNode) return;
    const complaints = JSON.parse(complaintsNode.textContent);
    let currentPage = 1;
    const perPage = 5;

    function renderRows(items) {
      return `
        <div class="property-table-wrap">
          <table class="property-table">
            <thead><tr><th>Title</th><th>Category</th><th>Status</th><th>Date</th><th>Description</th></tr></thead>
            <tbody>
              ${items.map((item) => `
                <tr>
                  <td>${item.title}</td>
                  <td>${item.category}</td>
                  <td><span class="status-badge status-badge--stable">${item.status}</span></td>
                  <td>${item.createdAt}</td>
                  <td>${item.description}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderComplaints() {
      const totalPages = Math.max(1, Math.ceil(complaints.length / perPage));
      currentPage = Math.min(currentPage, totalPages);
      const pageItems = complaints.slice((currentPage - 1) * perPage, currentPage * perPage);
      target.innerHTML = pageItems.length ? renderRows(pageItems) : `<article class="resource-card"><h4>No complaints logged yet</h4><p>Your maintenance and repair complaints will appear here after you submit them.</p></article>`;
      renderPagination("tenantComplaintsPagination", currentPage, totalPages, (page) => {
        currentPage = page;
        renderComplaints();
      });
    }

    renderComplaints();
  }

  function initTenantAnalyticsPage() {
    const analyticsNode = document.getElementById("tenant-analytics-data");
    if (!analyticsNode) return;
    const analyticsData = JSON.parse(analyticsNode.textContent);
    renderDoughnut("tenantChargesChart", analyticsData.charts.charges, "68%");
    renderLegend("tenantChargesLegend", analyticsData.charts.charges, (item) => formatCurrency(item.value));
    renderBarChart("tenantActivityChart", analyticsData.charts.activity.labels, analyticsData.charts.activity.values);
  }

  function initTenantReceiptsPage() {
    const receiptsNode = document.getElementById("tenant-receipts-data");
    const tableTarget = document.getElementById("tenantReceiptsTable");
    if (!receiptsNode || !tableTarget) return;
    const receiptsData = JSON.parse(receiptsNode.textContent);
    const transactions = receiptsData.transactions || [];
    let currentPage = 1;
    const perPage = 6;

    function renderRows(items) {
      return `
        <div class="property-table-wrap">
          <table class="property-table">
            <thead><tr><th>Type</th><th>Amount Due</th><th>Amount Paid</th><th>Date</th><th>Actions</th></tr></thead>
            <tbody>
              ${items.map((item) => {
                const isBill = item.type === 'Bill';
                const statusClass = isBill ? (item.amount === 0 ? 'high-performing' : 'needs-attention') : 'high-performing';
                const statusText = isBill ? (item.amount === 0 ? 'Paid' : 'Unpaid') : 'Paid';
                const typeDisplay = isBill ? `<span>Bill</span><small style="color: var(--text-soft); font-size: 0.75em;">${item.category || ''}</small>` : 'Payment';
                return `
                <tr>
                  <td><span class="status-badge status-badge--${statusClass}">${statusText}</span><br><span style="font-size: 0.85em;">${typeDisplay}</span></td>
                  <td>${formatCurrency(item.originalAmount)}</td>
                  <td>${formatCurrency(item.amountPaid || 0)}</td>
                  <td>${item.date}</td>
                  <td><a href="${item.detailUrl}" class="btn btn--ghost btn--sm">View</a></td>
                </tr>
              `}).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderTransactions() {
      const totalPages = Math.max(1, Math.ceil(transactions.length / perPage));
      currentPage = Math.min(currentPage, totalPages);
      const pageItems = transactions.slice((currentPage - 1) * perPage, currentPage * perPage);
      tableTarget.innerHTML = pageItems.length ? renderRows(pageItems) : `<article class="resource-card"><h4>No transactions yet</h4><p>Bills and payments will appear here once they are recorded.</p></article>`;
      renderPagination("tenantReceiptsPagination", currentPage, totalPages, (page) => {
        currentPage = page;
        renderTransactions();
      });
    }

    renderTransactions();
  }

  function initAnalyticsPage() {
    if (!document.getElementById("benchmarkList")) return;
    const occupancy = [
      { label: "Occupied", value: 152, color: "#2f74ff" },
      { label: "Vacant", value: 22, color: "#ffb24d" },
      { label: "Reserved", value: 0, color: "#1bc6a6" }
    ];
    const benchmarks = [
      { title: "Best collection lift", detail: "Autopay adoption is driving steadier early-month receipts.", value: "+12%" },
      { title: "Vacancy focus", detail: "Skyline Suites and Bluehaven remain the biggest leasing pressure points.", value: "2 sites" },
      { title: "Service drag", detail: "Plumbing continues to be the heaviest maintenance category this month.", value: "5 tickets" }
    ];
    document.getElementById("benchmarkList").innerHTML = benchmarks.map((item) => `
      <article class="resource-card"><div><h4>${item.title}</h4><p>${item.detail}</p></div><div class="resource-card__value">${item.value}</div></article>
    `).join("");
    const title = document.getElementById("insightTitle");
    const copy = document.getElementById("insightCopy");
    if (title && copy) {
      title.textContent = "Skyline Suites needs proactive leasing support";
      copy.textContent = "Skyline Suites is sitting at 72% occupancy while overdue pressure is already concentrated in two properties. A short renewal and broker outreach sprint is the clearest near-term move to protect next month’s cash flow.";
    }
    renderRentChart("rentChart");
    renderBarChart("maintenanceChart", maintenanceCategories.labels, maintenanceCategories.values);
    renderDoughnut("occupancyChart", occupancy, "72%");
    renderLegend("occupancyLegend", occupancy, (item) => item.value);
  }

  function initNotificationsPage() {
    const alertList = document.getElementById("alertsList");
    if (!alertList) return;
    alertList.innerHTML = notificationsAlerts.map((alert) => `
      <article class="alert-item"><div class="alert-item__icon alert-item__icon--${alert.type}"><i class="${alert.icon}"></i></div><div><h4>${alert.title}</h4><p>${alert.description}</p><span class="alert-item__time">${alert.time}</span></div></article>
    `).join("");
    const automationList = document.getElementById("automationList");
    if (automationList) automationList.innerHTML = automationRules.map((rule) => `
      <article class="resource-card"><div class="resource-card__header"><div><h4>${rule.title}</h4><p>${rule.channel}</p></div><span class="status-badge status-badge--stable">${rule.status}</span></div><p>${rule.cadence}</p></article>
    `).join("");
    const communicationList = document.getElementById("communicationList");
    if (communicationList) communicationList.innerHTML = communicationFeed.map((item) => `
      <article class="resource-card"><div class="resource-card__header"><div><h4>${item.title}</h4><p>${item.channel} • ${item.audience}</p></div><span class="status-badge status-badge--stable">${item.time}</span></div></article>
    `).join("");
  }

  function initSettingsPage() {
    const settingsGrid = document.getElementById("settingsGrid");
    if (!settingsGrid) return;
    settingsGrid.innerHTML = settingsCards.map((setting) => `
      <article class="resource-card settings-card"><div class="toggle-row"><div><h4>${setting.title}</h4><p>${setting.description}</p></div><button class="toggle-btn${setting.enabled ? " is-active" : ""}" aria-pressed="${setting.enabled}" aria-label="Toggle ${setting.title}"><span></span></button></div></article>
    `).join("");
    const integrationList = document.getElementById("integrationList");
    if (integrationList) integrationList.innerHTML = integrations.map((item) => `
      <article class="resource-card"><div class="resource-card__header"><div><h4>${item.name}</h4><p>${item.detail}</p></div><span class="status-badge status-badge--stable">${item.status}</span></div></article>
    `).join("");
    const accessList = document.getElementById("accessList");
    if (accessList) accessList.innerHTML = accessRoles.map((role) => `
      <article class="resource-card"><div class="resource-card__header"><div><h4>${role.role}</h4><p>${role.permission}</p></div><span class="status-badge status-badge--stable">${role.members} members</span></div></article>
    `).join("");
    document.querySelectorAll(".toggle-btn").forEach((button) => {
      button.addEventListener("click", () => {
        const next = !button.classList.contains("is-active");
        button.classList.toggle("is-active", next);
        button.setAttribute("aria-pressed", String(next));
      });
    });
  }

  function initPropertyForm() {
    const rowsContainer = document.getElementById("unitTypeRows");
    const addRowButton = document.getElementById("addUnitTypeRow");
    const totalFormsInput = document.getElementById("id_unit_types-TOTAL_FORMS");
    const rowTemplate = document.getElementById("unitTypeRowTemplate");
    if (!rowsContainer || !totalFormsInput || !rowTemplate) return;

    function bindRemoveButtons() {
      rowsContainer.querySelectorAll(".remove-unit-type").forEach((button) => {
        button.onclick = () => {
          const row = button.closest(".unit-type-row");
          const deleteInput = row.querySelector('input[type="checkbox"]');
          if (deleteInput) deleteInput.checked = true;
          row.style.display = "none";
        };
      });
    }

    addRowButton?.addEventListener("click", () => {
      const index = Number(totalFormsInput.value);
      const html = rowTemplate.innerHTML.replaceAll("__prefix__", String(index));
      rowsContainer.insertAdjacentHTML("beforeend", html);
      totalFormsInput.value = String(index + 1);
      bindRemoveButtons();
    });

    bindRemoveButtons();
  }

  function initTenantForm() {
    const propertySelect = document.getElementById("id_property");
    const unitTypeSelect = document.getElementById("id_unit_type");
    const propertyUnitSelect = document.getElementById("id_property_unit");
    const leaseTypeSelect = document.getElementById("id_lease_type");
    const availabilityMessage = document.getElementById("unitAvailabilityMessage");
    const pricingLabel = document.getElementById("derivedPricingLabel");
    const pricingValue = document.getElementById("derivedPricingValue");
    const leaseEndField = document.getElementById("leaseEndField");
    const leaseEndInput = document.getElementById("id_lease_end");
    const leaseEndHelp = document.getElementById("leaseEndHelp");
    const unitsNode = document.getElementById("available-units-data");
    if (!propertySelect || !unitTypeSelect || !propertyUnitSelect || !unitsNode) return;
    const unitsData = JSON.parse(unitsNode.textContent);

    function renderUnitTypes() {
      const propertyData = unitsData[propertySelect.value];
      const unitTypes = propertyData ? Object.keys(propertyData.unitTypes) : [];
      const selectedType = unitTypeSelect.value;
      unitTypeSelect.innerHTML = `<option value="">Select unit type</option>${unitTypes.map((value) => `<option value="${value}">${value}</option>`).join("")}`;
      if (selectedType && unitTypes.includes(selectedType)) {
        unitTypeSelect.value = selectedType;
      }
      propertyUnitSelect.innerHTML = `<option value="">Select available house</option>`;
      if (!unitTypes.length) {
        availabilityMessage.textContent = propertySelect.value ? "No available units in this property yet." : "Choose a property to load available units.";
      } else {
        availabilityMessage.textContent = "Select a unit type to see available houses.";
      }
    }

    function renderUnits() {
      const propertyData = unitsData[propertySelect.value];
      const units = propertyData && unitTypeSelect.value ? (propertyData.unitTypes[unitTypeSelect.value] || []) : [];
      const selectedUnit = propertyUnitSelect.value;
      propertyUnitSelect.innerHTML = `<option value="">Select available house</option>${units.map((unit) => `<option value="${unit.id}" data-renting-price="${unit.rentingPrice}" data-buying-price="${unit.buyingPrice}">${unit.label}</option>`).join("")}`;
      if (selectedUnit && units.some((unit) => String(unit.id) === selectedUnit)) {
        propertyUnitSelect.value = selectedUnit;
      }
      if (!units.length) {
        availabilityMessage.textContent = unitTypeSelect.value ? `No available ${unitTypeSelect.value} units right now.` : "Select a unit type to see available houses.";
      } else {
        availabilityMessage.textContent = `${units.length} available ${unitTypeSelect.value} ${units.length === 1 ? "unit" : "units"} found.`;
      }
      updateDerivedPricing();
    }

    function updateLeaseEndState() {
      if (!leaseTypeSelect || !leaseEndInput || !leaseEndHelp || !leaseEndField) return;
      const isPurchase = leaseTypeSelect.value === "Purchase";
      leaseEndInput.required = !isPurchase;
      leaseEndField.hidden = isPurchase;
      leaseEndHelp.textContent = isPurchase
        ? "Permanent purchases can leave the lease end date blank."
        : "Required for rental leases.";
      if (isPurchase) {
        leaseEndInput.value = "";
      }
    }

    function updateDerivedPricing() {
      if (!pricingLabel || !pricingValue) return;
      const selected = propertyUnitSelect.options[propertyUnitSelect.selectedIndex];
      const hasUnit = selected && selected.value;
      const leaseType = leaseTypeSelect?.value || "Rent";
      if (!hasUnit) {
        pricingLabel.textContent = "Select property, unit type, house, and lease type";
        pricingValue.textContent = "KSh 0";
        return;
      }
      const amount = leaseType === "Purchase"
        ? Number(selected.dataset.buyingPrice || 0)
        : Number(selected.dataset.rentingPrice || 0);
      pricingLabel.textContent = leaseType === "Purchase" ? "Buying price from selected unit" : "Renting price from selected unit";
      pricingValue.textContent = formatCurrency(amount);
    }

    propertySelect.addEventListener("change", () => {
      renderUnitTypes();
    });
    unitTypeSelect.addEventListener("change", renderUnits);
    propertyUnitSelect.addEventListener("change", updateDerivedPricing);
    leaseTypeSelect?.addEventListener("change", () => {
      updateLeaseEndState();
      updateDerivedPricing();
    });

    renderUnitTypes();
    if (unitTypeSelect.value) renderUnits();
    updateLeaseEndState();
    updateDerivedPricing();
  }

  function init() {
    initSidebar();
    initTheme();
    initRevealAnimation();
    animateMetrics();
    initOverviewPage();
    initPropertiesPage();
    initTenantsPage();
    initTenantComplaintsPage();
    initTenantAnalyticsPage();
    initTenantReceiptsPage();
    initPaymentsPage();
    initMaintenancePage();
    initAnalyticsPage();
    initNotificationsPage();
    initSettingsPage();
    initPropertyForm();
    initTenantForm();
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", SmartRentMain.init);
