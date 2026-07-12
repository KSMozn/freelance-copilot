(function () {
  "use strict";

  var toggle = document.querySelector(".nav-burger");
  var nav = document.querySelector(".site-nav");
  var script = document.currentScript;
  var analyticsToken = script && script.dataset.cloudflareToken;

  if (location.hostname === "careero.app" && analyticsToken) {
    var beacon = document.createElement("script");
    beacon.defer = true;
    beacon.src = "https://static.cloudflareinsights.com/beacon.min.js";
    beacon.dataset.cfBeacon = JSON.stringify({ token: analyticsToken });
    document.head.appendChild(beacon);
  }

  if (!toggle || !nav) return;

  function setOpen(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute(
      "aria-label",
      open ? "Close navigation" : "Open navigation",
    );
  }

  toggle.addEventListener("click", function () {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  nav.addEventListener("click", function (event) {
    if (event.target.closest("a")) setOpen(false);
  });

  document.addEventListener("keydown", function (event) {
    if (
      event.key !== "Escape" ||
      toggle.getAttribute("aria-expanded") !== "true"
    )
      return;
    setOpen(false);
    toggle.focus();
  });
})();
