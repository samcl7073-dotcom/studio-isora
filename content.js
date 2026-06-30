// Studio Isora — content loader with hot-reload support (dev only).
// Edit content.json to update copy; the UI refreshes automatically on localhost.

window.Content = (function () {
  let content = null;
  let lastSerialized = "";
  const listeners = [];

  function isDevHost() {
    const host = window.location.hostname;
    return host === "localhost" || host === "127.0.0.1";
  }

  function getByPath(obj, path) {
    return path.split(".").reduce((acc, key) => (acc == null ? acc : acc[key]), obj);
  }

  function showContentError() {
    const main = document.getElementById("main");
    const errorEl = document.getElementById("content-error");
    if (!errorEl) return;

    errorEl.hidden = false;

    if (main) {
      Array.from(main.children).forEach((child) => {
        if (child !== errorEl) child.setAttribute("hidden", "");
      });
    }
  }

  function hideContentError() {
    const main = document.getElementById("main");
    const errorEl = document.getElementById("content-error");
    if (!errorEl) return;

    errorEl.hidden = true;

    if (main) {
      Array.from(main.children).forEach((child) => {
        if (child !== errorEl) child.removeAttribute("hidden");
      });
    }
  }

  function applyScalarBindings(root, data) {
    root.querySelectorAll("[data-content]").forEach((el) => {
      const value = getByPath(data, el.getAttribute("data-content"));
      if (value != null) el.textContent = value;
    });

    root.querySelectorAll("[data-content-html]").forEach((el) => {
      const value = getByPath(data, el.getAttribute("data-content-html"));
      if (value != null) el.innerHTML = value;
    });

    root.querySelectorAll("[data-content-attr]").forEach((el) => {
      let setSrc = false;

      el.getAttribute("data-content-attr")
        .split(",")
        .forEach((pair) => {
          const colon = pair.indexOf(":");
          if (colon === -1) return;
          const attr = pair.slice(0, colon).trim();
          const path = pair.slice(colon + 1).trim();
          const value = getByPath(data, path);
          if (value != null) {
            el.setAttribute(attr, value);
            if (attr === "src") setSrc = true;
          }
        });

      if (el.tagName === "VIDEO" && setSrc) el.load();
    });
  }

  function applyItemBindings(node, item) {
    node.querySelectorAll("[data-content-item]").forEach((el) => {
      const field = el.getAttribute("data-content-item");
      if (item[field] != null) el.textContent = item[field];
    });

    node.querySelectorAll("[data-content-item-html]").forEach((el) => {
      const field = el.getAttribute("data-content-item-html");
      if (item[field] != null) el.innerHTML = item[field];
    });

    node.querySelectorAll("[data-content-item-attr]").forEach((el) => {
      el.getAttribute("data-content-item-attr")
        .split(",")
        .forEach((pair) => {
          const colon = pair.indexOf(":");
          if (colon === -1) return;
          const attr = pair.slice(0, colon).trim();
          const field = pair.slice(colon + 1).trim();
          if (item[field] != null) el.setAttribute(attr, item[field]);
        });
    });

    node.querySelectorAll("[data-content-item-style]").forEach((el) => {
      const field = el.getAttribute("data-content-item-style");
      if (item[field] != null) {
        const prop = el.getAttribute("data-content-style-prop") || "backgroundImage";
        const value =
          prop === "backgroundImage" ? `url('${item[field]}')` : item[field];
        el.style[prop] = value;
      }
    });

    node.querySelectorAll("[data-content-item-if]").forEach((el) => {
      const field = el.getAttribute("data-content-item-if");
      if (!item[field]) el.remove();
    });
  }

  function renderLists(root, data) {
    root.querySelectorAll("[data-content-list]").forEach((container) => {
      const path = container.getAttribute("data-content-list");
      const templateId = container.getAttribute("data-content-template");
      const items = getByPath(data, path);
      const template = document.getElementById(templateId);

      if (!Array.isArray(items) || !template) return;

      container.replaceChildren();
      items.forEach((item) => {
        const node = template.content.cloneNode(true);
        applyItemBindings(node, item);
        container.appendChild(node);
      });
    });
  }

  function applySiteMeta(data) {
    const title = getByPath(data, "site.title");
    const description = getByPath(data, "site.description");

    if (title) document.title = title;

    const meta = document.querySelector('meta[name="description"]');
    if (meta && description) meta.setAttribute("content", description);

    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle && title) ogTitle.setAttribute("content", title);

    const ogDescription = document.querySelector('meta[property="og:description"]');
    if (ogDescription && description) ogDescription.setAttribute("content", description);

    const ogImage = getByPath(data, "site.ogImage");
    const ogImageEl = document.querySelector('meta[property="og:image"]');
    if (ogImageEl && ogImage) ogImageEl.setAttribute("content", ogImage);
  }

  function applyAll(data) {
    applySiteMeta(data);
    applyScalarBindings(document, data);
    renderLists(document, data);
  }

  async function fetchContent() {
    const dev = isDevHost();
    const url = dev ? `content.json?t=${Date.now()}` : "content.json";
    const response = await fetch(url, dev ? { cache: "no-store" } : {});
    if (!response.ok) throw new Error(`Failed to load content.json (${response.status})`);
    return response.json();
  }

  async function refresh() {
    const next = await fetchContent();
    const serialized = JSON.stringify(next);
    if (serialized === lastSerialized) return content;

    lastSerialized = serialized;
    content = next;
    applyAll(content);
    hideContentError();
    window.dispatchEvent(new CustomEvent("content:updated", { detail: content }));
    listeners.forEach((fn) => fn(content));
    return content;
  }

  function onUpdate(fn) {
    listeners.push(fn);
    return () => {
      const index = listeners.indexOf(fn);
      if (index !== -1) listeners.splice(index, 1);
    };
  }

  async function init({ interval = 2000 } = {}) {
    try {
      await refresh();
    } catch (err) {
      showContentError();
      throw err;
    }

    if (isDevHost()) {
      setInterval(() => {
        refresh().catch(() => {
          if (!content) showContentError();
        });
      }, interval);
    }

    return content;
  }

  return { init, refresh, get: (path) => getByPath(content, path), onUpdate };
})();
