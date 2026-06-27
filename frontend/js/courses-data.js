/* Summit Teachable — course catalogue.
   Cards render into any element with id="courseGrid". On index.html only the
   first 3 are shown (data-limit="3"). "Buy" links go to the Django storefront
   at /buy/<slug>/ (Netlify redirects /buy/* to the dashboard host). */
(function () {
  "use strict";

  // In production the marketing site is on summitteachable.com and Netlify
  // redirects /buy/* to the dashboard host. For LOCAL testing (127.0.0.1) point
  // Buy buttons straight at the Django dev server so the flow works end-to-end.
  var _host = location.hostname;
  var BUY_BASE = (_host === "localhost" || _host === "127.0.0.1" || _host === "")
    ? "http://127.0.0.1:8055/buy/"
    : "/buy/";

  var COURSES = [
    {
      title: "Stock Market Money Glitch",
      slug: "stock-money-glitch",
      level: "beginner",
      price: 1000,
      blurb: "Spot repeatable, high-probability setups in the stock market — order flow, imbalance and clean entries.",
      lessons: 8,
      hours: "4h 15m",
      glyph: '<path d="M3 3v18h18"/><rect x="6" y="10" width="3" height="6"/><rect x="11" y="6" width="3" height="11"/><rect x="16" y="13" width="3" height="4"/>',
    },
    {
      title: "$1 Million: Ultimate Beginner's Guide to Trading",
      slug: "million-beginners-guide",
      level: "beginner",
      price: 1000,
      blurb: "A from-scratch roadmap for the brand-new trader — markets, brokers and your first practice trade on the dashboard.",
      lessons: 9,
      hours: "6h 30m",
      glyph: '<path d="M12 2 2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>',
    },
    {
      title: "Futures Trading",
      slug: "futures-trading",
      level: "intermediate",
      price: 1000,
      blurb: "Leverage, contracts and margin explained and practiced hands-on — ticks, multipliers and intraday execution.",
      lessons: 6,
      hours: "5h 45m",
      glyph: '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
    },
    {
      title: "So Many Options",
      slug: "so-many-options",
      level: "intermediate",
      price: 1000,
      blurb: "Calls, puts and spreads demystified — practice covered calls, verticals and defined-risk plays.",
      lessons: 8,
      hours: "7h 10m",
      glyph: '<circle cx="12" cy="12" r="10"/><path d="M14.31 8 20.05 17.94M9.69 8h11.48M7.38 12l5.74-9.94M9.69 16 3.95 6.06M14.31 16H2.83M16.62 12l-5.74 9.94"/>',
    },
    {
      title: "Crypto & Stocks University",
      slug: "crypto-stocks-university",
      level: "beginner",
      price: 1000,
      blurb: "One curriculum, two asset classes — wallets, swaps and equities, all on the Summit platform.",
      lessons: 8,
      hours: "8h 00m",
      glyph: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    },
    {
      title: "Bear Market Money",
      slug: "bear-market-money",
      level: "advanced",
      price: 1000,
      blurb: "Profiting in down markets with hedges and shorts — borrow, margin and drawdown management.",
      lessons: 6,
      hours: "6h 50m",
      glyph: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    },
    {
      title: "Trading Psychology & Risk Management",
      slug: "trading-psychology",
      level: "intermediate",
      price: 1000,
      blurb: "Master the mental game and protect your capital — discipline, journaling and position-sizing rules.",
      lessons: 6,
      hours: "4h 40m",
      glyph: '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24A2.5 2.5 0 0 1 9.5 2z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24A2.5 2.5 0 0 0 14.5 2z"/>',
    },
  ];

  // purple-tinted cover backgrounds, varied per level
  var COVER = {
    beginner: "radial-gradient(120% 120% at 20% 0%, rgba(139,92,246,0.32), transparent 60%), linear-gradient(135deg,#1b1430,#0c1226)",
    intermediate: "radial-gradient(120% 120% at 80% 0%, rgba(167,139,250,0.26), transparent 60%), linear-gradient(135deg,#191333,#0c1226)",
    advanced: "radial-gradient(120% 120% at 50% 0%, rgba(124,58,237,0.30), transparent 60%), linear-gradient(135deg,#211842,#0c1226)",
  };

  function card(c) {
    var href = BUY_BASE + c.slug + "/";
    return [
      '<article class="course-card glass">',
      '  <div class="course-cover">',
      '    <span class="cover-bg" style="background:' + COVER[c.level] + '"></span>',
      '    <span class="lvl ' + c.level + '">' + c.level.charAt(0).toUpperCase() + c.level.slice(1) + "</span>",
      '    <span class="cover-glyph"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">' + c.glyph + "</svg></span>",
      "  </div>",
      '  <div class="course-body">',
      "    <h3>" + c.title + "</h3>",
      "    <p>" + c.blurb + "</p>",
      '    <div class="course-meta">',
      '      <span class="m"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>' + c.lessons + " lessons</span>",
      '      <span class="m"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>' + c.hours + "</span>",
      "    </div>",
      '    <div class="course-buy" style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:14px;">',
      '      <span class="course-price" style="font-weight:800;font-size:1.15rem;">$' + c.price + "</span>",
      '      <a class="btn btn-primary" href="' + href + '">Buy this course</a>',
      "    </div>",
      "  </div>",
      "</article>",
    ].join("");
  }

  var grid = document.getElementById("courseGrid");
  if (!grid) return;
  var limit = parseInt(grid.dataset.limit || "0", 10);
  var list = limit ? COURSES.slice(0, limit) : COURSES;
  grid.innerHTML = list.map(card).join("");

  // Stagger reveal for injected cards
  Array.prototype.forEach.call(grid.children, function (el, i) {
    el.classList.add("reveal", "d" + ((i % 4) + 1));
  });
})();
