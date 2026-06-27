/* Summit Teachable — third-party integrations (loaded site-wide)
   - SmartSupp live chat
   - GTranslate floating language switcher
   These are isolated here so the same snippet runs identically on every page. */
(function () {
  "use strict";

  /* ---------- SmartSupp live chat ---------- */
  var _smartsupp = (window._smartsupp = window._smartsupp || {});
  _smartsupp.key = "5f577eafc561dcfb8bb776e8f1938272a17c4b64";
  (function (d) {
    var s,
      c,
      o = (window.smartsupp = function () {
        o._.push(arguments);
      });
    o._ = [];
    s = d.getElementsByTagName("script")[0];
    c = d.createElement("script");
    c.type = "text/javascript";
    c.charset = "utf-8";
    c.async = true;
    c.src = "https://www.smartsuppchat.com/loader.js?";
    s.parentNode.insertBefore(c, s);
  })(document);

  /* ---------- GTranslate floating widget ---------- */
  window.gtranslateSettings = {
    default_language: "en",
    languages: ["en", "es", "fr", "de", "pt", "it", "ar", "zh-CN", "hi", "ru"],
    wrapper_selector: ".gtranslate_wrapper",
    flag_style: "3d",
    switcher_horizontal_position: "left",
    float_switcher_open_direction: "top",
  };

  var wrapper = document.createElement("div");
  wrapper.className = "gtranslate_wrapper";
  document.body.appendChild(wrapper);

  var gt = document.createElement("script");
  gt.src = "https://cdn.gtranslate.net/widgets/latest/float.js";
  gt.defer = true;
  document.body.appendChild(gt);
})();
