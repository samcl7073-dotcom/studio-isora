// Studio Isora — nav menu and active-section highlight.
(function () {
  const nav = document.querySelector(".nav");
  const toggle = document.getElementById("navToggle");
  const list = document.getElementById("navList");

  function setOpen(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }

  if (nav && toggle && list) {
    toggle.addEventListener("click", () => setOpen(!nav.classList.contains("is-open")));
    list.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
  }

  // Solid nav once the hero is scrolled past (home page only).
  if (document.body.classList.contains("home") && nav) {
    const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // Highlight the nav link for the section in view (home) or for the blog.
  const links = Array.from(document.querySelectorAll(".nav__link"));
  if (location.pathname.startsWith("/blog")) {
    links.forEach((l) => l.classList.toggle("is-active", l.getAttribute("href") === "/blog/"));
  } else if ("IntersectionObserver" in window) {
    const byId = new Map();
    links.forEach((l) => {
      const m = l.getAttribute("href").match(/#(.+)$/);
      const s = m && document.getElementById(m[1]);
      if (s) byId.set(s, l);
    });
    const io = new IntersectionObserver(
      (entries) => entries.forEach((en) => {
        if (en.isIntersecting) links.forEach((l) => l.classList.toggle("is-active", l === byId.get(en.target)));
      }),
      { rootMargin: "-45% 0px -50% 0px" }
    );
    byId.forEach((_, s) => io.observe(s));
  }

})();
