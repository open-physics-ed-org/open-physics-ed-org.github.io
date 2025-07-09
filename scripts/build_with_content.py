#!/usr/bin/env python3
"""
Process _content.yml to inject site title, footer, and menu into HTML pages when building from Markdown.
Usage: ./scripts/build_with_content.py path/to/file.md [--debug]
"""
import sys
import os
from pathlib import Path
import yaml
import argparse
import re

CONTENT_YML = Path('_content.yml')
CONTENT_DIR = Path('content')
LAYOUTS_DIR = Path('layouts')
STATIC_CSS = {
    'light': '/css/theme-light.css',
    'dark': '/css/theme-dark.css',
}
DOCS_DIR = Path('docs')

def load_content_yml():
    if not CONTENT_YML.exists():
        raise FileNotFoundError(f"_content.yml not found")
    with open(CONTENT_YML) as f:
        return yaml.safe_load(f)

def parse_front_matter(md_text):
    if md_text.startswith('---'):
        parts = md_text.split('---', 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1])
            content = parts[2].lstrip('\n')
            return meta, content
    return {}, md_text

def render_markdown(md_text):
    try:
        import markdown
        return markdown.markdown(md_text, extensions=['extra', 'codehilite'])
    except ImportError:
        return '<pre>' + md_text + '</pre>'

def load_layout(layout_name):
    layout_path = LAYOUTS_DIR / layout_name
    if not layout_path.exists():
        raise FileNotFoundError(f"Layout not found: {layout_path}")
    return layout_path.read_text()

def build_menu(menu):
    # menu: list of dicts with name, url
    def is_external(url):
        return url.startswith('http://') or url.startswith('https://') or url.startswith('//')
    items = []
    for item in sorted(menu, key=lambda x: x.get('weight', 0)):
        url = item["url"]
        if is_external(url):
            link = f'<a href="{url}" target="_blank" rel="noopener">{item["name"]}</a>'
        else:
            # Always use relative links for internal pages
            rel_url = url if url.startswith('/') else '/' + url
            link = f'<a href="{rel_url}">{item["name"]}</a>'
        items.append(f'<li>{link}</li>')
    return '<ul style="display: flex; gap: 2rem; list-style: none; margin: 0; padding: 0; justify-content: center;">' + ''.join(items) + '</ul>'

def build_html(meta, content_html, layout_name, site, menu_html, footer_html):
    html = load_layout(layout_name)
    css_links = f'<link rel="stylesheet" href="{STATIC_CSS["light"]}" id="theme-style">\n<link rel="stylesheet" href="{STATIC_CSS["dark"]}" media="(prefers-color-scheme: dark)">'  # noqa
    html = html.replace('</head>', f'{css_links}\n</head>')
    html = html.replace('{{ .Title }}', meta.get('title', site.get('title', 'Untitled')))
    html = html.replace('{{ .Content }}', content_html)
    # Insert menu
    html = re.sub(r'<nav[^>]*>.*?</nav>', f'<nav style="padding: 1rem 0; border-bottom: 1px solid #eee; background: #f8f8f8;">{menu_html}</nav>', html, flags=re.DOTALL)
    # Insert footer
    html = re.sub(r'<footer[^>]*>.*?</footer>', f'<footer style="text-align: center; margin: 2rem 0 1rem 0; color: #888; font-size: 0.9rem;">{footer_html}</footer>', html, flags=re.DOTALL)
    # Footer year
    if '{{ now.Year }}' in html:
        from datetime import datetime
        html = html.replace('{{ now.Year }}', str(datetime.now().year))
    return html

def main():
    parser = argparse.ArgumentParser(description="Build a single Markdown file into HTML in docs/ using _content.yml for site meta.")
    parser.add_argument('mdfile', help='Path to the Markdown file to build')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    site_content = load_content_yml()
    site = site_content.get('site', {})
    menu = site_content.get('menu', [])
    footer_html = site.get('footer', '')
    menu_html = build_menu(menu)

    md_path = Path(args.mdfile)
    if not md_path.exists():
        print(f"File not found: {md_path}")
        sys.exit(1)
    md_text = md_path.read_text()
    meta, md_content = parse_front_matter(md_text)
    page_type = meta.get('type', 'base')
    if page_type == 'news':
        layout_name = 'news/single.html'
    else:
        layout_name = '_default/baseof.html'
    content_html = render_markdown(md_content)
    html = build_html(meta, content_html, layout_name, site, menu_html, footer_html)
    rel_path = md_path.relative_to(CONTENT_DIR).with_suffix('.html')
    out_path = DOCS_DIR / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"[OK] Built {out_path}")
    if args.debug:
        print("--- Debug Info ---")
        print(f"Input file: {md_path}")
        print(f"Output file: {out_path}")
        print(f"Layout used: {layout_name}")
        print(f"Meta: {meta}")
        print(f"Site meta: {site}")
        print(f"Menu: {menu}")
        print(f"Footer: {footer_html}")
        print(f"Content length: {len(md_content)} chars")
        print(f"HTML length: {len(html)} chars")
        print(f"Output directory: {out_path.parent}")
        print(f"Directory structure preserved: {rel_path}")

if __name__ == '__main__':
    main()
