// Lightweight, vendor-neutral analytics event abstraction.
//
// Page views are already tracked by Cloudflare Web Analytics (cookieless,
// automatic, no banner). Cloudflare's free beacon does NOT accept custom
// events, so this file provides a clean seam for event tracking without
// committing to a new vendor: `window.careeroTrack(name, props)`.
//
// TODO: to actually record events (CTA clicks, guide views, comparison CTA
// clicks), forward these to an events-capable vendor once approved. Until
// then this is a safe no-op (optionally logs in debug mode).
(function () {
  "use strict";

  window.careeroTrack = function (name, props) {
    try {
      if (window.__CAREERO_DEBUG__ && window.console) {
        console.log("[careero:track]", name, props || {});
      }
      // Placeholder for a future events endpoint / vendor:
      // navigator.sendBeacon('/e', JSON.stringify({ name, props }));
    } catch (_) {
      /* never let analytics break the page */
    }
  };

  // Auto-track CTA clicks and any outbound link to the app.
  document.addEventListener(
    "click",
    function (e) {
      var el =
        e.target &&
        e.target.closest &&
        e.target.closest("[data-cta], a[href^='https://app.careero.app']");
      if (!el) return;
      window.careeroTrack("cta_click", {
        cta: el.getAttribute("data-cta") || "app-link",
        href: el.getAttribute("href") || "",
        page: location.pathname,
      });
    },
    { passive: true },
  );
})();
