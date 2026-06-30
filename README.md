# Studio Isora — Website Template

A cinematic, dark-themed landing page template inspired by boutique studio sites
(full-bleed hero video, minimal horizontal nav, slim credits bar). Built as
plain HTML / CSS / JS so it is easy to preview, customize, and later migrate to
a framework (Next.js, Astro, etc.).

## Structure

```
.
├── index.html      Markup for hero + About / Portfolio / Services / Careers / Contact
├── styles.css      Theme tokens, layout, components, responsive rules
├── script.js       Mobile menu toggle, active-section highlighting, footer year
└── README.md
```

## Quick start

No build step required. Open `index.html` directly or run a tiny local server:

```bash
# Python 3
python3 -m http.server 5173
# then visit http://localhost:5173
```

## Customize

- **Branding** — edit the `.brand` block in `index.html` and the `--accent`
  color token in `styles.css`.
- **Hero video** — replace the `<source>` URL inside `.hero__video` with your
  own MP4 (the `poster` attribute is shown while the video loads or on
  reduced-motion devices).
- **Sections** — duplicate `.card` items in the Portfolio grid, or edit copy in
  About / Services / Careers / Contact.
- **Fonts** — swap the Google Fonts `<link>` for your own type system.

## Next steps (when you're ready)

- Move into a framework (Next.js / Astro) for content collections, MDX case
  studies, and image optimization.
- Add a CMS (Sanity, Contentful, or local markdown) for the Portfolio entries.
- Wire up the Contact section to a form handler (Resend, Formspree, etc.).
