// Studio Isora — UI interactions for the landing template.

(function () {
  const nav = document.querySelector(".nav");
  const toggle = document.getElementById("navToggle");
  const navList = document.getElementById("navList");
  let sectionObserver = null;

  function setFooterYear() {
    const year = document.getElementById("year");
    if (year) year.textContent = new Date().getFullYear();
  }

  function bindNavToggle() {
    if (!toggle || !nav || toggle.dataset.bound === "true") return;
    toggle.dataset.bound = "true";

    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
  }

  function bindNavListClose() {
    if (!navList || !nav || navList.dataset.bound === "true") return;
    navList.dataset.bound = "true";

    navList.addEventListener("click", (e) => {
      if (e.target.matches("a") && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
      }
    });
  }

  function bindActiveSectionObserver() {
    if (sectionObserver) sectionObserver.disconnect();

    const links = Array.from(document.querySelectorAll(".nav__link"));
    const sections = links
      .map((a) => document.querySelector(a.getAttribute("href")))
      .filter(Boolean);

    if (!("IntersectionObserver" in window) || !sections.length) return;

    sectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = "#" + entry.target.id;
            links.forEach((l) => l.classList.toggle("is-active", l.getAttribute("href") === id));
          }
        });
      },
      { rootMargin: "-40% 0px -55% 0px", threshold: 0 }
    );

    sections.forEach((s) => sectionObserver.observe(s));
  }

  function initInteractions() {
    bindNavToggle();
    bindNavListClose();
    bindActiveSectionObserver();
    setFooterYear();
  }

  async function boot() {
    if (window.Content) {
      try {
        await window.Content.init({ interval: 2000 });
        window.Content.onUpdate(() => initInteractions());
      } catch {
        return;
      }
    }

    initInteractions();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
