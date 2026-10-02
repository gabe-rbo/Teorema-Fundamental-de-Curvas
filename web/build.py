#!/usr/bin/env python3
"""Build index.html (repository root): the website as ONE self-contained file.

All Triedro design-system CSS, the app CSS and every script are inlined, so the page
opens by double-click and is served as-is by GitHub Pages, with no relative stylesheet or
script paths to resolve (some browsers restrict those on file:// pages). KaTeX and the web fonts still
come from their CDNs and degrade gracefully when offline.

Run after editing anything under web/ or design-system/:  python3 web/build.py
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent


def build() -> str:
    html = (APP / "template.html").read_text(encoding="utf-8")

    def inline_css(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith(("http:", "https:")):
            return match.group(0)
        css = ((APP / href).resolve()).read_text(encoding="utf-8")
        return f"<style>\n{css}\n</style>"

    def inline_js(match: re.Match[str]) -> str:
        js = (APP / match.group(1)).read_text(encoding="utf-8")
        if "</script" in js.lower():
            raise ValueError(f"{match.group(1)} contains a closing script tag")
        return f"<script>\n{js}\n</script>"

    html = re.sub(r'<link rel="stylesheet" href="([^"]+)">', inline_css, html)
    html = re.sub(r'<script src="(js/[^"]+)"></script>', inline_js, html)
    return html


def main() -> None:
    out = ROOT / "index.html"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
