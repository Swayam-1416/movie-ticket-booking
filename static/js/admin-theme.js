(() => {
  const root = document.documentElement;
  const button = document.querySelector(".admin-theme-toggle");
  if (!button) return;

  const updateLabel = () => {
    const light = root.dataset.theme === "light";
    button.querySelector(".theme-icon").textContent = light ? "☾" : "☼";
    button.querySelector(".theme-label").textContent = light ? "Dark" : "Light";
    button.setAttribute("aria-label", `Switch to ${light ? "dark" : "light"} theme`);
  };

  updateLabel();
  button.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    try {
      localStorage.setItem("cinepass-theme", root.dataset.theme);
    } catch (error) {}
    updateLabel();
  });
})();
