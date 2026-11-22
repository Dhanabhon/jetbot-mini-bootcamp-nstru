// Windows / macOS picker. <html data-os> (set early in head_custom.html) decides which
// [data-os] blocks the CSS shows; without JS both stay visible and the picker stays hidden.
(function () {
  var KEY = "os";
  var root = document.documentElement;

  function apply(os) {
    root.dataset.os = os;
    document.querySelectorAll(".os-switch input").forEach(function (input) {
      input.checked = input.value === os;
    });
  }

  function save(os) {
    try {
      // picking the detected OS means "back to default", so don't pin it
      if (os === root.dataset.osDetected) localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, os);
    } catch (e) {} // storage blocked: the choice still applies to this page
  }

  document.addEventListener("change", function (event) {
    if (!event.target.matches(".os-switch input")) return;
    apply(event.target.value);
    save(event.target.value);
  });

  // another tab changed the choice
  window.addEventListener("storage", function (event) {
    if (event.key === KEY) apply(event.newValue || root.dataset.osDetected);
  });

  // the picker lives in the site header, so show it only on pages that have per-OS steps
  var hasOsContent = document.querySelector("main [data-os]") !== null;
  document.querySelectorAll(".os-switch").forEach(function (el) {
    el.hidden = !hasOsContent;
  });
  if (root.dataset.os) apply(root.dataset.os); // else head script didn't run: keep both OS blocks visible
})();
