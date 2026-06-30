#!/usr/bin/env python3
"""
Pre-render Studio Isora for production.

Reads index.html + content.json, applies all data bindings statically,
and outputs a fully populated dist/ directory ready to deploy.

Usage:
    python3 build.py
"""

from __future__ import annotations

import json
import re
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SOURCE_HTML = ROOT / "index.html"
SOURCE_CONTENT = ROOT / "content.json"


def get_by_path(data: dict, path: str):
    current = data
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def strip_binding_attrs(html: str) -> str:
    return re.sub(r'\sdata-content(?:-[a-z-]+)?="[^"]*"', "", html)


def apply_content_attr(spec: str, attrs: str, data: dict) -> str:
    for pair in spec.split(","):
        colon = pair.find(":")
        if colon == -1:
            continue
        attr_name = pair[:colon].strip()
        path = pair[colon + 1 :].strip()
        value = get_by_path(data, path)
        if value is None:
            continue
        attrs = re.sub(rf'\s{re.escape(attr_name)}="[^"]*"', "", attrs)
        attrs += f' {attr_name}="{escape(str(value), quote=True)}"'
    return attrs


def apply_item_bindings(fragment: str, item: dict) -> str:
    def replace_item_text(match: re.Match) -> str:
        tag, before, field, after = match.groups()
        value = item.get(field)
        if value is None:
            return match.group(0)
        return f"<{tag}{before}{after}>{escape(str(value))}</{tag}>"

    fragment = re.sub(
        r"<(\w+)([^>]*?)\sdata-content-item=\"([^\"]+)\"([^>]*)>\s*</\1>",
        replace_item_text,
        fragment,
    )

    def replace_item_html(match: re.Match) -> str:
        tag, before, field, after = match.groups()
        value = item.get(field)
        if value is None:
            return match.group(0)
        return f"<{tag}{before}{after}>{value}</{tag}>"

    fragment = re.sub(
        r"<(\w+)([^>]*?)\sdata-content-item-html=\"([^\"]+)\"([^>]*)>\s*</\1>",
        replace_item_html,
        fragment,
    )

    def replace_item_attr_void(match: re.Match) -> str:
        tag, before, spec, after = match.groups()
        attrs = apply_content_attr(spec, before + after, item)
        attrs = strip_binding_attrs(attrs)
        return f"<{tag}{attrs} />"

    fragment = re.sub(
        r"<(\w+)([^>]*)\sdata-content-item-attr=\"([^\"]+)\"([^>]*)\s*/>",
        replace_item_attr_void,
        fragment,
    )

    def replace_item_attr_paired(match: re.Match) -> str:
        tag, before, spec, after, inner = match.groups()
        attrs = apply_content_attr(spec, before + after, item)
        attrs = strip_binding_attrs(attrs)
        return f"<{tag}{attrs}>{inner}</{tag}>"

    fragment = re.sub(
        r"<(\w+)([^>]*)\sdata-content-item-attr=\"([^\"]+)\"([^>]*)>([\s\S]*?)</\1>",
        replace_item_attr_paired,
        fragment,
    )

    def replace_item_style(match: re.Match) -> str:
        tag, before, field, after = match.groups()
        value = item.get(field)
        if value is None:
            return match.group(0)
        clean = strip_binding_attrs(before + after)
        return f'<{tag}{clean} style="background-image: url(\'{value}\')"></{tag}>'

    fragment = re.sub(
        r"<(\w+)([^>]*?)\sdata-content-item-style=\"([^\"]+)\"([^>]*)>\s*</\1>",
        replace_item_style,
        fragment,
    )

    def remove_if_false(match: re.Match) -> str:
        field = match.group(1)
        return "" if not item.get(field) else match.group(0)

    fragment = re.sub(
        r"<[^>]+data-content-item-if=\"([^\"]+)\"[^>]*>[\s\S]*?</[^>]+>",
        remove_if_false,
        fragment,
    )

    return fragment


def render_lists(html: str, data: dict) -> str:
    list_pattern = re.compile(
        r"<(\w+)([^>]*?)\sdata-content-list=\"([^\"]+)\"\s+data-content-template=\"([^\"]+)\"([^>]*)>\s*</\1>",
        re.DOTALL,
    )

    def replace_list(match: re.Match) -> str:
        tag, before, list_path, template_id, after = match.groups()
        items = get_by_path(data, list_path)
        template_match = re.search(
            rf"<template id=\"{re.escape(template_id)}\">([\s\S]*?)</template>",
            html,
        )
        if not template_match or not isinstance(items, list):
            return match.group(0)

        rendered = []
        for item in items:
            chunk = apply_item_bindings(template_match.group(1).strip(), item)
            rendered.append(chunk)

        clean = strip_binding_attrs(before + after)
        return f"<{tag}{clean}>{''.join(rendered)}</{tag}>"

    return list_pattern.sub(replace_list, html)


def apply_scalar_bindings(html: str, data: dict) -> str:
    def replace_text(match: re.Match) -> str:
        tag, before, path, after = match.groups()
        value = get_by_path(data, path)
        if value is None:
            return match.group(0)
        clean = strip_binding_attrs(before + after)
        return f"<{tag}{clean}>{escape(str(value))}</{tag}>"

    html = re.sub(
        r"<(\w+)([^>]*?)\sdata-content=\"([^\"]+)\"([^>]*)>\s*</\1>",
        replace_text,
        html,
    )

    def replace_html(match: re.Match) -> str:
        tag, before, path, after = match.groups()
        value = get_by_path(data, path)
        if value is None:
            return match.group(0)
        clean = strip_binding_attrs(before + after)
        return f"<{tag}{clean}>{value}</{tag}>"

    html = re.sub(
        r"<(\w+)([^>]*?)\sdata-content-html=\"([^\"]+)\"([^>]*)>\s*</\1>",
        replace_html,
        html,
    )

    def replace_attr_void(match: re.Match) -> str:
        tag, before, spec, after = match.groups()
        attrs = apply_content_attr(spec, before + after, data)
        attrs = strip_binding_attrs(attrs)
        return f"<{tag}{attrs} />"

    html = re.sub(
        r"<(\w+)([^>]*)\sdata-content-attr=\"([^\"]+)\"([^>]*)\s*/>",
        replace_attr_void,
        html,
    )

    def replace_attr_paired(match: re.Match) -> str:
        tag, before, spec, after = match.groups()
        attrs = apply_content_attr(spec, before + after, data)
        attrs = strip_binding_attrs(attrs)
        return f"<{tag}{attrs}></{tag}>"

    html = re.sub(
        r"<(\w+)([^>]*)\sdata-content-attr=\"([^\"]+)\"([^>]*)>\s*</\1>",
        replace_attr_paired,
        html,
    )

    def replace_attr_open(match: re.Match) -> str:
        tag, before, spec, after, inner = match.groups()
        attrs = apply_content_attr(spec, before + after, data)
        attrs = strip_binding_attrs(attrs)
        return f"<{tag}{attrs}>{inner}</{tag}>"

    html = re.sub(
        r"<(\w+)([^>]*)\sdata-content-attr=\"([^\"]+)\"([^>]*)>([\s\S]+?)</\1>",
        replace_attr_open,
        html,
    )

    return html


def apply_site_meta(html: str, data: dict) -> str:
    title = get_by_path(data, "site.title") or "Studio Isora"
    description = get_by_path(data, "site.description") or ""
    og_image = get_by_path(data, "site.ogImage") or ""

    html = re.sub(r"<title>[^<]*</title>", f"<title>{escape(title)}</title>", html)

    html = re.sub(
        r'(<meta\s+name="description"\s+content=")[^"]*(")',
        rf"\1{escape(description, quote=True)}\2",
        html,
        count=1,
    )

    html = re.sub(
        r'(<meta\s+property="og:title"\s+content=")[^"]*(")',
        rf"\1{escape(title, quote=True)}\2",
        html,
        count=1,
    )

    html = re.sub(
        r'(<meta\s+property="og:description"\s+content=")[^"]*(")',
        rf"\1{escape(description, quote=True)}\2",
        html,
        count=1,
    )

    if og_image:
        html = re.sub(
            r'(<meta\s+property="og:image"\s+content=")[^"]*(")',
            rf"\1{escape(og_image, quote=True)}\2",
            html,
            count=1,
        )
        html = re.sub(
            r'(<meta\s+name="twitter:image"\s+content=")[^"]*(")',
            rf"\1{escape(og_image, quote=True)}\2",
            html,
            count=1,
        )

    html = re.sub(
        r'(<meta\s+name="twitter:title"\s+content=")[^"]*(")',
        rf"\1{escape(title, quote=True)}\2",
        html,
        count=1,
    )

    html = re.sub(
        r'(<meta\s+name="twitter:description"\s+content=")[^"]*(")',
        rf"\1{escape(description, quote=True)}\2",
        html,
        count=1,
    )

    return html


def prepare_production_html(html: str) -> str:
    html = re.sub(
        r'\s*<link rel="preload" href="content\.json"[^>]*/>\s*',
        "\n",
        html,
    )
    html = re.sub(
        r'\s*<script src="content\.js" defer></script>\s*',
        "\n",
        html,
    )
    html = re.sub(r"\s*<template id=\"tpl-[^\"]+\">[\s\S]*?</template>\s*", "", html)
    html = re.sub(
        r'\s*<div id="content-error"[^>]*>[\s\S]*?</div>\s*',
        "\n",
        html,
    )
    return html


def build() -> None:
    content = json.loads(SOURCE_CONTENT.read_text(encoding="utf-8"))
    html = SOURCE_HTML.read_text(encoding="utf-8")

    html = render_lists(html, content)
    html = apply_scalar_bindings(html, content)
    html = apply_site_meta(html, content)
    html = strip_binding_attrs(html)
    html = prepare_production_html(html)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    (DIST / "index.html").write_text(html, encoding="utf-8")
    shutil.copy2(ROOT / "styles.css", DIST / "styles.css")
    shutil.copy2(ROOT / "script.js", DIST / "script.js")

    assets_src = ROOT / "assets"
    if assets_src.is_dir():
        shutil.copytree(assets_src, DIST / "assets")
        print("  dist/assets/     (video and media files)")

    print(f"Built production site → {DIST}/")
    print("  dist/index.html  (pre-rendered, no client-side content fetch)")
    print("  dist/styles.css")
    print("  dist/script.js")


if __name__ == "__main__":
    build()
