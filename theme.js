(function () {
  var root = document.documentElement, btn = document.getElementById("theme-toggle");
  function sync() {
    var light = root.dataset.theme === "light";
    btn.textContent = light ? "Dark mode" : "Light mode";
    btn.setAttribute("aria-pressed", light ? "true" : "false");
  }
  btn.addEventListener("click", function () {
    var light = root.dataset.theme !== "light";
    if (light) root.dataset.theme = "light"; else delete root.dataset.theme;
    try { localStorage.setItem("theme", light ? "light" : "dark"); } catch (e) {}
    sync();
  });
  sync();
})();
