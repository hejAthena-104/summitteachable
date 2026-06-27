/* Summit Teachable — shared footer (with the required educational/risk disclaimer).
   Injected into <footer id="footer-mount"> on every page so the disclaimer stays
   identical and is impossible to forget. */
(function () {
  "use strict";
  var mount = document.getElementById("footer-mount");
  if (!mount) return;

  mount.innerHTML = [
    '<div class="container">',
    '  <div class="footer-grid">',
    '    <div class="footer-about">',
    '      <a class="brand" href="index.html" aria-label="Summit Teachable home">',
    '        <img class="brand-logo logo-for-light" src="images/logo-dark.png" alt="Summit Teachable" width="220" height="60" onerror="this.style.display=\'none\';this.parentElement.querySelector(\'.brand-fallback\').style.display=\'flex\'" />',
    '        <img class="brand-logo logo-for-dark" src="images/white-logo.png" alt="Summit Teachable" width="220" height="60" onerror="this.style.display=\'none\'" />',
    '        <span class="brand-fallback" aria-hidden="true">',
    '          <span class="logo-mark"><svg viewBox="0 0 24 24" fill="none" stroke="#04221a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20 L9 8 L13 14 L17 5 L21 20 Z"/></svg></span>',
    '          <span style="font-family:var(--font-display);font-weight:700;font-size:19px;color:#fff;">Summit<b style="color:var(--mint);">Teachable</b></span>',
    '        </span>',
    '      </a>',
    '      <p>An educational trading platform. Structured courses plus a risk-free demo trading dashboard powered by simulated funds — so you can build real skill before real money is ever involved.</p>',
    '      <div class="footer-social">',
    socialLink("https://twitter.com", "X / Twitter", '<path d="M18 6 6 18M6 6l12 12"/>'),
    socialLink("https://youtube.com", "YouTube", '<path d="M22 12s0-3.5-.45-5.18a2.78 2.78 0 0 0-1.95-2C17.88 4.33 12 4.33 12 4.33s-5.88 0-7.6.49a2.78 2.78 0 0 0-1.95 2C2 8.5 2 12 2 12s0 3.5.45 5.18a2.78 2.78 0 0 0 1.95 2c1.72.49 7.6.49 7.6.49s5.88 0 7.6-.49a2.78 2.78 0 0 0 1.95-2C22 15.5 22 12 22 12z"/><path d="m10 15 5-3-5-3z"/>'),
    socialLink("https://instagram.com", "Instagram", '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/>'),
    socialLink("https://t.me", "Telegram", '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>'),
    '      </div>',
    '    </div>',
    footerCol("Platform", [
      ["courses.html", "Courses"],
      ["markets.html", "Markets"],
      ["/register", "Demo dashboard"],
      ["about.html", "About us"],
    ]),
    footerCol("Account", [
      ["/login", "Log in"],
      ["/register", "Create account"],
      ["contact.html", "Support"],
      ["contact.html", "Contact"],
    ]),
    footerCol("Legal", [
      ["privacy-policy.html", "Privacy policy"],
      ["terms-of-service.html", "Terms of service"],
      ["#disclaimer", "Risk disclaimer"],
    ]),
    '  </div>',
    '',
    '  <div class="disclaimer" id="disclaimer">',
    '    <span class="warn" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>',
    '    <p><strong>Educational &amp; risk disclaimer:</strong> Summit Teachable is an educational platform. The trading dashboard uses simulated demo funds only — not real money. Nothing here is financial advice. Trading real financial instruments carries significant risk; past or simulated performance is not indicative of future results. Always do your own research and consider seeking advice from a licensed professional before making any real investment decision.</p>',
    '  </div>',
    '',
    '  <div class="footer-bottom">',
    '    <span>© <span data-year>2026</span> Summit Teachable. All rights reserved. Educational use only.</span>',
    '    <span class="links">',
    '      <a href="privacy-policy.html">Privacy</a>',
    '      <a href="terms-of-service.html">Terms</a>',
    '      <a href="contact.html">Contact</a>',
    '    </span>',
    '  </div>',
    '</div>',
  ].join("\n");

  function footerCol(title, links) {
    var items = links
      .map(function (l) {
        return '<li><a href="' + l[0] + '">' + l[1] + "</a></li>";
      })
      .join("");
    return (
      '<div class="footer-col"><h4>' + title + "</h4><ul>" + items + "</ul></div>"
    );
  }
  function socialLink(href, label, path) {
    return (
      '<a href="' + href + '" aria-label="' + label + '" target="_blank" rel="noopener noreferrer">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      path + "</svg></a>"
    );
  }
})();
