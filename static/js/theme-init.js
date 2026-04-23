(function () {
  try {
    var stored = localStorage.getItem("smartrent-theme");
    if (stored === "dark" || stored === "light") {
      document.documentElement.setAttribute("data-theme", stored);
    }
  } catch (e) {
    /* ignore */
  }
})();
