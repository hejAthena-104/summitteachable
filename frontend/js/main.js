/* Summit Teachable — site interactions */
(function () {
  "use strict";

  /* ---- Sticky header shadow on scroll ---- */
  const header = document.querySelector(".site-header");
  const onScroll = () => {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 12);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---- Mobile nav toggle ---- */
  const toggle = document.querySelector(".nav-toggle");
  const drawer = document.querySelector(".mobile-nav");
  if (toggle && drawer) {
    toggle.addEventListener("click", () => {
      const open = drawer.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    drawer.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => drawer.classList.remove("open"))
    );
  }

  /* ---- Scroll reveal ---- */
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const reveals = document.querySelectorAll(".reveal");
  if (reduce || !("IntersectionObserver" in window)) {
    reveals.forEach((el) => el.classList.add("in"));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    reveals.forEach((el) => io.observe(el));
  }

  /* ---- Animated number counters ---- */
  const fmt = (n, decimals) =>
    Number(n).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });

  const animateCount = (el) => {
    const target = parseFloat(el.dataset.count);
    const decimals = parseInt(el.dataset.decimals || "0", 10);
    const dur = 1600;
    const start = performance.now();
    const step = (now) => {
      const t = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      el.textContent = fmt(target * eased, decimals);
      if (t < 1) requestAnimationFrame(step);
      else el.textContent = fmt(target, decimals);
    };
    requestAnimationFrame(step);
  };

  const counters = document.querySelectorAll("[data-count]");
  if (reduce || !("IntersectionObserver" in window)) {
    counters.forEach((el) =>
      (el.textContent = fmt(
        parseFloat(el.dataset.count),
        parseInt(el.dataset.decimals || "0", 10)
      ))
    );
  } else {
    const co = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            animateCount(e.target);
            co.unobserve(e.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach((el) => co.observe(el));
  }

  /* ---- Live-ish faux price flicker on hero terminal (demo only) ---- */
  const livePrices = document.querySelectorAll("[data-live]");
  if (livePrices.length && !reduce) {
    setInterval(() => {
      livePrices.forEach((el) => {
        const base = parseFloat(el.dataset.live);
        const drift = (Math.random() - 0.5) * (base * 0.0012);
        const val = base + drift;
        const dec = parseInt(el.dataset.dec || "2", 10);
        el.textContent = val.toLocaleString("en-US", {
          minimumFractionDigits: dec,
          maximumFractionDigits: dec,
        });
      });
    }, 2200);
  }

  /* ---- Contact form (demo handler) ---- */
  const form = document.querySelector("[data-contact-form]");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const note = form.querySelector("[data-form-note]");
      if (note) {
        note.hidden = false;
        note.textContent =
          "Thanks — your message has been queued. Our support team will reply by email shortly.";
      }
      form.reset();
    });
  }

  /* ---- Footer year ---- */
  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = new Date().getFullYear();
  });
})();
