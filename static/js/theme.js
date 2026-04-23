(function (global) {
  const STORAGE_KEY = "smartrent-theme";

  function get() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function syncToggleIcons() {
    const dark = document.documentElement.getAttribute("data-theme") === "dark";
    document.querySelectorAll(".theme-toggle").forEach((btn) => {
      const icon = btn.querySelector("i");
      btn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
      btn.setAttribute("title", dark ? "Light mode" : "Dark mode");
      if (icon) {
        icon.className = dark ? "fa-solid fa-sun" : "fa-solid fa-moon";
      }
    });
  }

  function refreshCharts() {
    if (typeof Chart === "undefined") {
      return;
    }
    const rootStyles = getComputedStyle(document.documentElement);
    const color = rootStyles.getPropertyValue("--text-muted").trim() || "#596782";
    document.querySelectorAll("canvas").forEach((canvas) => {
      const chart = Chart.getChart(canvas);
      if (!chart) {
        return;
      }
      chart.options.color = color;
      const scales = chart.options.scales;
      if (scales?.x?.ticks) {
        scales.x.ticks.color = color;
      }
      if (scales?.y?.ticks) {
        scales.y.ticks.color = color;
      }
      const legend = chart.options.plugins?.legend;
      if (legend?.labels) {
        legend.labels.color = color;
      }
      chart.update("none");
    });
  }

  function set(mode) {
    if (mode !== "light" && mode !== "dark") {
      return;
    }
    document.documentElement.setAttribute("data-theme", mode);
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch (e) {
      /* ignore */
    }
    syncToggleIcons();
    refreshCharts();
    global.dispatchEvent(new CustomEvent("smartrentthemechange", { detail: { theme: mode } }));
  }

  function toggle() {
    set(get() === "dark" ? "light" : "dark");
  }

  function bindToggles() {
    document.querySelectorAll(".theme-toggle").forEach((btn) => {
      const clone = btn.cloneNode(true);
      btn.parentNode.replaceChild(clone, btn);
    });
    document.querySelectorAll(".theme-toggle").forEach((btn) => {
      btn.addEventListener("click", () => toggle());
    });
    syncToggleIcons();
  }

  global.SmartRentTheme = {
    get,
    set,
    toggle,
    bindToggles,
    refreshCharts,
    syncToggleIcons
  };
})(typeof window !== "undefined" ? window : globalThis);
