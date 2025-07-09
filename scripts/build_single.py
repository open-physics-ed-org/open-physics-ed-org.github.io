#!/usr/bin/env python3
"""
Build a single Markdown file from content/ into an HTML file in docs/ using the appropriate layout and static CSS.
- By default, uses layouts/_default/baseof.html
- If the Markdown file has 'type: news' in its front matter, uses layouts/news/single.html
- Injects static CSS link(s) into the HTML head
- Usage: ./scripts/build_single.py path/to/file.md [--debug]
"""
import sys
import os
import re
from pathlib import Path
import yaml

CONTENT_DIR = Path('content')
LAYOUTS_DIR = Path('layouts')
STATIC_CSS = {
    'light': '/css/theme-light.css',
    'dark': '/css/theme-dark.css',
}
DOCS_DIR = Path('docs')

# --- Helpers ---
def parse_front_matter(md_text):
    """Extract YAML front matter and content from a Markdown file."""
    if md_text.startswith('---'):
        parts = md_text.split('---', 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1])
            content = parts[2].lstrip('\n')
            return meta, content
    return {}, md_text

def render_markdown(md_text):
    """Convert Markdown to HTML (basic, no extensions)."""
    try:
        import markdown
        return markdown.markdown(md_text, extensions=['extra', 'codehilite'])
    except ImportError:
        # fallback: very basic
        return '<pre>' + md_text + '</pre>'

def load_layout(layout_name):
    """Load a layout HTML file as a string."""
    layout_path = LAYOUTS_DIR / layout_name
    if not layout_path.exists():
        raise FileNotFoundError(f"Layout not found: {layout_path}")
    return layout_path.read_text()

def build_html(meta, content_html, layout_name):
    """Fill the layout template with meta and content."""
    html = load_layout(layout_name)
    # Insert CSS links
    css_links = f'<link rel="stylesheet" href="{STATIC_CSS["light"]}" id="theme-style">\n<link rel="stylesheet" href="{STATIC_CSS["dark"]}" media="(prefers-color-scheme: dark)">'  # noqa
    html = html.replace('</head>', f'{css_links}\n</head>')
    # Replace Hugo-style variables
    html = html.replace('{{ .Title }}', meta.get('title', 'Untitled'))
    html = html.replace('{{ .Content }}', content_html)
    # Footer (optional)
    if '{{ now.Year }}' in html:
        from datetime import datetime
        html = html.replace('{{ now.Year }}', str(datetime.now().year))
    return html

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build a single Markdown file into HTML in docs/.")
    parser.add_argument('mdfile', help='Path to the Markdown file to build')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    md_path = Path(args.mdfile)
    if not md_path.exists():
        print(f"File not found: {md_path}")
        sys.exit(1)
    md_text = md_path.read_text()
    meta, md_content = parse_front_matter(md_text)
    # Determine layout
    page_type = meta.get('type', 'base')
    if page_type == 'news':
        layout_name = 'news/single.html'
    else:
        layout_name = '_default/baseof.html'
    # Render markdown
    content_html = render_markdown(md_content)
    # Build HTML
    html = build_html(meta, content_html, layout_name)
    # Output path: preserve directory structure under docs
    rel_path = md_path.relative_to(CONTENT_DIR).with_suffix('.html')
    # Special case: content/_index.md -> docs/index.html
    if str(rel_path) == '_index.html':
        rel_path = Path('index.html')
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
        print(f"Content length: {len(md_content)} chars")
        print(f"HTML length: {len(html)} chars")
        print(f"Output directory: {out_path.parent}")
        print(f"Directory structure preserved: {rel_path}")

if __name__ == '__main__':
    main()
