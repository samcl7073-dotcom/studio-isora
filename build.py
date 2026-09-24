#!/usr/bin/env python3
"""
Build the Studio Isora website into dist/.

    python3 build.py

Inputs (edit these, then rebuild):
    content.json    all text on the home page, nav, contact email
    posts/*.md      blog posts (front matter: title, date, summary)
    videos.json     YouTube videos for the 'Watch the process' section
    templates/      page layouts
    styles.css, script.js, assets/   copied as-is

Output:
    dist/index.html, dist/blog/index.html, dist/blog/<slug>/index.html,
    dist/styles.css, dist/script.js, dist/assets/...

No third-party packages needed: plain Python 3.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import quote, urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
TEMPLATES = ROOT / "templates"
POSTS = ROOT / "posts"
STATIC_FILES = ["styles.css", "script.js"]
STATIC_DIRS = ["assets"]


# ---------------------------------------------------------------- markdown --

def inline_md(text: str) -> str:
    """Escape, then apply inline markdown: code, links, bold, italic."""
    codes: list[str] = []

    def stash(m):
        codes.append(f"<code>{escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = escape(text, quote=False)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{escape(m.group(2))}">{m.group(1)}</a>',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)
    return text


def markdown_to_html(md: str) -> str:
    """Small markdown subset: headings, paragraphs, lists, quotes, rules, images, code blocks."""
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    para: list[str] = []
    list_type: str | None = None
    in_code = False
    code: list[str] = []

    def flush_para():
        nonlocal para
        if para:
            out.append(f"<p>{inline_md(' '.join(para))}</p>")
            para = []

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    for line in lines:
        if in_code:
            if line.strip().startswith("```"):
                out.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
                code, in_code = [], False
            else:
                code.append(line)
            continue
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_para(); close_list(); in_code = True
            continue
        if not stripped:
            flush_para(); close_list()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para(); close_list()
            level = min(len(m.group(1)) + 1, 4)  # '#' in a post becomes h2
            out.append(f"<h{level}>{inline_md(m.group(2))}</h{level}>")
            continue
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            flush_para(); close_list(); out.append("<hr />")
            continue
        vid = youtube_id(stripped) if re.match(r"^https?://\S+$", stripped) else None
        if vid:
            flush_para(); close_list()
            out.append(youtube_embed(vid))
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)$", stripped)
        if m:
            flush_para(); close_list()
            out.append(
                f'<figure><img src="{escape(m.group(2))}" alt="{escape(m.group(1))}" loading="lazy" />'
                + (f"<figcaption>{inline_md(m.group(1))}</figcaption>" if m.group(1) else "")
                + "</figure>"
            )
            continue
        m = re.match(r"^([-*]|\d+[.)])\s+(.*)$", stripped)
        if m:
            flush_para()
            kind = "ul" if m.group(1) in "-*" else "ol"
            if list_type != kind:
                close_list(); out.append(f"<{kind}>"); list_type = kind
            out.append(f"<li>{inline_md(m.group(2))}</li>")
            continue
        if stripped.startswith(">"):
            flush_para(); close_list()
            out.append(f"<blockquote><p>{inline_md(stripped.lstrip('> '))}</p></blockquote>")
            continue
        close_list()
        para.append(stripped)

    flush_para(); close_list()
    return "\n".join(out)


# ------------------------------------------------------------------- posts --

def read_post(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    d = date.fromisoformat(meta.get("date") or path.stem[:10])
    return {
        "slug": slug,
        "title": meta.get("title", slug.replace("-", " ").title()),
        "date": d,
        "date_label": f"{d:%B} {d.day}, {d.year}",
        "summary": meta.get("summary", ""),
        "html": markdown_to_html(body),
        "file": path.name,
    }


def load_posts() -> list[dict]:
    posts = [read_post(p) for p in sorted(POSTS.glob("*.md"))]
    posts.sort(key=lambda p: (p["date"], p["file"]), reverse=True)
    return posts


# ----------------------------------------------------------------- helpers --

def youtube_id(url: str) -> str | None:
    u = urlparse(url.strip())
    host = (u.hostname or "").replace("www.", "").replace("m.", "")
    if host == "youtu.be":
        return u.path.strip("/").split("/")[0] or None
    if host.endswith("youtube.com"):
        if u.path == "/watch":
            return parse_qs(u.query).get("v", [None])[0]
        parts = u.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in ("embed", "shorts", "live"):
            return parts[1]
    return None


def youtube_embed(vid: str, title: str = "YouTube video") -> str:
    return (
        f'<div class="video-embed"><iframe src="https://www.youtube-nocookie.com/embed/{escape(vid)}" '
        f'title="{escape(title)}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        f'gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'
    )


def mailto(email: str, subject: str = "", body: str = "") -> str:
    q = []
    if subject:
        q.append("subject=" + quote(subject))
    if body:
        q.append("body=" + quote(body))
    return f"mailto:{email}" + ("?" + "&".join(q) if q else "")


def tpl(name: str) -> Template:
    return Template((TEMPLATES / name).read_text(encoding="utf-8"))


def e(s) -> str:
    return escape(str(s))


# ------------------------------------------------------------------ render --

def render_nav(c: dict) -> str:
    return "\n".join(
        f'<li><a class="nav__link" href="{e(l["href"])}">{e(l["label"])}</a></li>' for l in c["nav"]
    )


def render_post_cards(posts: list[dict]) -> str:
    return "\n".join(
        f"""<article class="post-card">
  <a href="/blog/{p['slug']}/">
    <time datetime="{p['date'].isoformat()}">{e(p['date_label'])}</time>
    <h3>{e(p['title'])}</h3>
    <p>{e(p['summary'])}</p>
    <span class="post-card__more">Read post &rarr;</span>
  </a>
</article>"""
        for p in posts
    )


def render_videos(c: dict, videos: list[dict]) -> str:
    items = []
    for v in videos:
        vid = youtube_id(v.get("youtube", ""))
        if not vid:
            print(f"  ! videos.json: skipped, not a YouTube link: {v.get('youtube')!r}")
            continue
        title = v.get("title", "")
        items.append(
            f'<figure class="video-item">{youtube_embed(vid, title or "YouTube video")}'
            + (f"<figcaption>{e(title)}</figcaption>" if title else "")
            + "</figure>"
        )
    if not items:
        return f'<p class="section__lede">{e(c["watch"]["emptyText"])}</p>'
    return f'<div class="videos">{"".join(items)}</div>'


def build():
    c = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
    videos = json.loads((ROOT / "videos.json").read_text(encoding="utf-8")).get("videos", [])
    posts = load_posts()
    site = c["site"]
    year = date.today().year
    booking = site.get("bookingUrl", "").strip()
    book_href = booking or mailto(site["email"], site["bookingSubject"])
    rollout_href = booking or mailto(site["email"], "Early rollout of Isora")
    book_target = ' target="_blank" rel="noopener"' if booking else ""

    common = {
        "site_name": e(site["name"]),
        "nav": render_nav(c),
        "email": e(site["email"]),
        "email_href": e(mailto(site["email"])),
        "book_href": e(book_href),
        "book_target": book_target,
        "copyright": e(site["copyright"]),
        "year": str(year),
        "description": e(site["description"]),
    }
    base = tpl("base.html")

    def page(title: str, description: str, body: str, body_class: str = "") -> str:
        return base.safe_substitute(
            common, title=e(title), description=e(description), body=body, body_class=body_class
        )

    def paras(items):
        return "".join(f'<p class="section__lede">{e(p)}</p>' for p in items)

    # -- home
    latest = posts[0] if posts else None
    status = (
        f'<a class="status-bar__link" href="/blog/{latest["slug"]}/"><span class="status-bar__label">Latest from the blog</span> {e(latest["title"])} &rarr;</a>'
        if latest else ""
    )
    home_body = tpl("home.html").safe_substitute(
        common,
        hero_video=e(site["heroVideo"]),
        hero_eyebrow=e(c["hero"]["eyebrow"]),
        hero_title=e(c["hero"]["title"]),
        hero_lede=e(c["hero"]["lede"]),
        hero_primary=e(c["hero"]["primaryCta"]),
        hero_secondary=e(c["hero"]["secondaryCta"]),
        status=status,
        services_eyebrow=e(c["services"]["eyebrow"]),
        services_title=e(c["services"]["title"]),
        services_lede=e(c["services"]["lede"]),
        services_items="\n".join(
            f"""<li class="step">
  <span class="step__num">{e(s['number'])}</span>
  <div><h3>{e(s['title'])}</h3><p>{e(s['description'])}</p></div>
</li>"""
            for s in c["services"]["items"]
        ),
        pipeline_eyebrow=e(c["pipeline"]["eyebrow"]),
        pipeline_title=e(c["pipeline"]["title"]),
        pipeline_items="\n".join(
            f"<li><h3>{e(p['title'])}</h3><p>{e(p['description'])}</p></li>" for p in c["pipeline"]["items"]
        ),
        tools_eyebrow=e(c["tools"]["eyebrow"]),
        tools_title=e(c["tools"]["title"]),
        tools_paragraphs=paras(c["tools"]["paragraphs"]),
        tools_cta=e(c["tools"]["cta"]),
        rollout_href=e(rollout_href),
        watch_eyebrow=e(c["watch"]["eyebrow"]),
        watch_title=e(c["watch"]["title"]),
        watch_body=render_videos(c, list(reversed(videos))),
        blog_eyebrow=e(c["blog"]["eyebrow"]),
        blog_title=e(c["blog"]["title"]),
        blog_cards=render_post_cards(posts[:3]),
        book_eyebrow=e(c["book"]["eyebrow"]),
        book_title=e(c["book"]["title"]),
        book_text=e(c["book"]["text"]),
    )
    pages = {DIST / "index.html": page(site["title"], site["description"], home_body, "home")}

    # -- blog index
    blog_body = tpl("blog_index.html").safe_substitute(
        common,
        blog_eyebrow=e(c["blog"]["eyebrow"]),
        blog_title=e(c["blog"]["title"]),
        blog_lede=e(c["blog"]["lede"]),
        blog_cards=render_post_cards(posts) or '<p class="section__lede">No posts yet.</p>',
    )
    pages[DIST / "blog" / "index.html"] = page(f"Blog — {site['name']}", c["blog"]["lede"], blog_body, "inner")

    # -- posts
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        pager = "".join([
            f'<a class="pager__older" href="/blog/{older["slug"]}/">&larr; {e(older["title"])}</a>' if older else "<span></span>",
            f'<a class="pager__newer" href="/blog/{newer["slug"]}/">{e(newer["title"])} &rarr;</a>' if newer else "<span></span>",
        ])
        body = tpl("post.html").safe_substitute(
            common,
            post_title=e(p["title"]),
            post_date=e(p["date_label"]),
            post_iso=p["date"].isoformat(),
            post_html=p["html"],
            pager=pager,
        )
        pages[DIST / "blog" / p["slug"] / "index.html"] = page(f"{p['title']} — {site['name']}", p["summary"], body, "inner")

    # -- write (overwrite in place; remove pages for deleted posts)
    DIST.mkdir(exist_ok=True)
    blog_dir = DIST / "blog"
    if blog_dir.exists():
        keep = {p["slug"] for p in posts}
        for d in blog_dir.iterdir():
            if d.is_dir() and d.name not in keep:
                try:
                    shutil.rmtree(d)
                except OSError as err:
                    print(f"  ! could not remove old post {d.name}: {err}")
    for path, html in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    for name in STATIC_FILES:
        shutil.copyfile(ROOT / name, DIST / name)
    for d in STATIC_DIRS:
        for src in (ROOT / d).rglob("*"):
            if src.is_file() and not src.name.startswith("."):
                dst = DIST / src.relative_to(ROOT)
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                    shutil.copyfile(src, dst)

    print(f"Built {len(pages)} pages into {DIST.relative_to(ROOT)}/ ({len(posts)} posts)")


if __name__ == "__main__":
    build()
