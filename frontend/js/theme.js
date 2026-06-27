/* Summit Teachable — light/dark theme toggle.
   Light is the default. The pre-paint inline script in each page's <head>
   applies a saved "dark" choice before first paint (no flash); this file
   injects the toggle controls into the nav and wires up persistence. */
(function () {
  "use strict";
  var root = document.documentElement;
  var KEY = "theme";

  function current() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function apply(theme) {
    if (theme === "dark") root.setAttribute("data-theme", "dark");
    else root.removeAttribute("data-theme");

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "dark" ? "#0F0A1E" : "#F5F3FB");

    try { localStorage.setItem(KEY, theme); } catch (e) {}

    document.querySelectorAll("[data-theme-toggle]").forEach(function (b) {
      var toDark = theme !== "dark";
      b.setAttribute("aria-label", toDark ? "Switch to dark mode" : "Switch to light mode");
      b.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    });
  }

  function toggle() {
    apply(current() === "dark" ? "light" : "dark");
  }

  var ICONS =
    '<span class="i-moon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></span>' +
    '<span class="i-sun" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg></span>';

  function makeBtn(extraClass, label) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "theme-toggle" + (extraClass ? " " + extraClass : "");
    b.setAttribute("data-theme-toggle", "");
    b.innerHTML = ICONS + (label ? '<span class="tt-label">' + label + "</span>" : "");
    b.addEventListener("click", toggle);
    return b;
  }

  /* Desktop control — first item in the CTA cluster */
  var cta = document.querySelector(".nav-cta");
  if (cta) cta.insertBefore(makeBtn(), cta.firstChild);

  /* Mobile control — a labelled row at the bottom of the drawer */
  var drawer = document.querySelector(".mobile-nav");
  if (drawer) drawer.appendChild(makeBtn("theme-toggle-mobile", "Toggle theme"));

  /* Sync labels + meta to whatever the pre-paint script settled on */
  apply(current());
})();
