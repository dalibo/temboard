import "@fortawesome/fontawesome-free/css/all.min.css";
import { Tooltip } from "bootstrap";
import $ from "jquery";
import { createApp } from "vue";

import Error from "./components/Error.vue";
import "./temboard.scss";

window.errorApp = createApp({
  components: {
    error: Error,
  },
}).mount("#errorApp");

// Error shortcuts
window.clearError = function () {
  window.errorApp.$refs.error.clear();
};

window.showError = function (error) {
  if (typeof error === "string") {
    window.errorApp.$refs.error.$refs.error.setHTML(error);
  } else {
    window.errorApp.$refs.error.fromXHR(error);
  }
};

$(() => {
  // Mark active link in sidebar
  var url = window.location;
  var element = $("ul.nav a")
    .filter(function () {
      return this.href == url || url.href.indexOf(this.href) == 0;
    })
    .addClass("active")
    .parent()
    .parent()
    .addClass("in")
    .parent();

  if (element.is("li")) {
    element.addClass("active");
  }

  // One toggled state: collapsed on desktop, open as an overlay on mobile.
  const desktopSidebar = window.matchMedia("(min-width: 992px)");
  const setSidebarState = () => {
    const isToggled = desktopSidebar.matches && localStorage.getItem("sidebarCollapsed") === "true";
    document.body.classList.toggle("sidebar-toggled", isToggled);
    $("#menu-toggle").attr("aria-expanded", desktopSidebar.matches ? !isToggled : isToggled);
    updateSidebarTooltips();
  };
  setSidebarState();
  desktopSidebar.addEventListener("change", setSidebarState);

  const toggleDesktopSidebar = () => {
    const isToggled = $(document.body).toggleClass("sidebar-toggled").hasClass("sidebar-toggled");
    localStorage.setItem("sidebarCollapsed", isToggled);
    $("#menu-toggle").attr("aria-expanded", !isToggled);
    updateSidebarTooltips();
    window.dispatchEvent(new Event("resize"));
  };

  $("#menu-collapse").click(function (event) {
    event.preventDefault();
    toggleDesktopSidebar();
  });

  $("#menu-toggle").click(function () {
    if (desktopSidebar.matches) {
      toggleDesktopSidebar();
    } else {
      const isToggled = $(document.body).toggleClass("sidebar-toggled").hasClass("sidebar-toggled");
      this.setAttribute("aria-expanded", isToggled);
    }
  });

  $(".sidebar-fixed-width a").click(function () {
    if (!desktopSidebar.matches) {
      $(document.body).removeClass("sidebar-toggled");
      $("#menu-toggle").attr("aria-expanded", "false");
    }
  });

  $(".container-fluid > .row").click(function (event) {
    if (!desktopSidebar.matches && event.target === this && $(document.body).hasClass("sidebar-toggled")) {
      $(document.body).removeClass("sidebar-toggled");
      $("#menu-toggle").attr("aria-expanded", "false");
    }
  });

  $(document).keydown(function (event) {
    if (!desktopSidebar.matches && event.key === "Escape") {
      $(document.body).removeClass("sidebar-toggled");
      $("#menu-toggle").attr("aria-expanded", "false");
    }
  });

  // Tooltip initialization
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map((el) => new Tooltip(el, { sanitize: false }));
  function updateSidebarTooltips() {
    const collapsed = desktopSidebar.matches && document.body.classList.contains("sidebar-toggled");
    document.querySelectorAll('#sidebar .nav-link[data-bs-toggle="tooltip"]').forEach((el) => {
      const tooltip = Tooltip.getInstance(el);
      if (!tooltip) return;
      if (collapsed) {
        tooltip.enable();
      } else {
        tooltip.hide();
        tooltip.disable();
      }
    });
  }
  updateSidebarTooltips();
});
