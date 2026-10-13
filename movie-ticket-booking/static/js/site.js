(() => {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("cinepass-theme");
  if (savedTheme === "light" || savedTheme === "dark") root.dataset.theme = savedTheme;
  const themeToggle = document.querySelector(".theme-toggle");
  const updateThemeLabel = () => {
    const light = root.dataset.theme === "light";
    if (themeToggle) {
      themeToggle.querySelector(".theme-icon").textContent = light ? "☾" : "☼";
      themeToggle.querySelector(".theme-label").textContent = light ? "Dark" : "Light";
      themeToggle.setAttribute("aria-label", `Switch to ${light ? "dark" : "light"} theme`);
    }
  };
  updateThemeLabel();
  themeToggle?.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    localStorage.setItem("cinepass-theme", root.dataset.theme);
    updateThemeLabel();
  });

  document.querySelectorAll(".toast").forEach((toast, index) => {
    window.setTimeout(() => {
      toast.classList.add("toast-out");
      window.setTimeout(() => toast.remove(), 360);
    }, 4800 + index * 350);
  });

  const search = document.querySelector("#movie-search");
  const suggestionBox = document.querySelector("#search-suggestions");
  let searchDelay;
  const closeSuggestions = () => {
    if (!suggestionBox) return;
    suggestionBox.classList.remove("is-open");
    suggestionBox.replaceChildren();
    search?.setAttribute("aria-expanded", "false");
  };
  search?.addEventListener("input", () => {
    window.clearTimeout(searchDelay);
    const query = search.value.trim();
    if (!query) return closeSuggestions();
    searchDelay = window.setTimeout(async () => {
      try {
        const response = await fetch(`/search/suggestions/?q=${encodeURIComponent(query)}`, { headers: { "X-Requested-With": "XMLHttpRequest" } });
        const data = await response.json();
        suggestionBox.replaceChildren();
        if (!data.results.length) {
          const empty = document.createElement("div");
          empty.className = "suggestion-empty";
          empty.textContent = "No movies found. Try another title.";
          suggestionBox.append(empty);
        } else {
          data.results.forEach((movie) => {
            const link = document.createElement("a");
            link.className = "suggestion-item";
            link.href = movie.url;
            link.setAttribute("role", "option");
            const title = document.createElement("strong");
            title.textContent = movie.title;
            const genre = document.createElement("span");
            genre.textContent = movie.genre;
            const arrow = document.createElement("i");
            arrow.textContent = "↗";
            link.append(title, genre, arrow);
            suggestionBox.append(link);
          });
        }
        suggestionBox.classList.add("is-open");
        search.setAttribute("aria-expanded", "true");
      } catch {
        closeSuggestions();
      }
    }, 160);
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-search-root]")) closeSuggestions();
  });
  search?.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeSuggestions();
    if (event.key === "Enter") {
      const first = suggestionBox?.querySelector("a");
      if (first) { event.preventDefault(); first.click(); }
    }
  });

  document.querySelectorAll(".payment-option input").forEach((radio) => {
    radio.addEventListener("change", () => {
      document.querySelectorAll(".payment-option").forEach((option) => option.classList.remove("selected"));
      radio.closest(".payment-option").classList.add("selected");
    });
  });

  document.querySelectorAll('a[href^="/"]:not([target])').forEach((link) => {
    link.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.hash || link.dataset.noTransition) return;
      const transition = document.querySelector(".page-transition");
      if (!transition || link.pathname === window.location.pathname) return;
      event.preventDefault();
      transition.classList.add("is-active");
      window.setTimeout(() => { window.location.href = link.href; }, 180);
    });
  });
})();
