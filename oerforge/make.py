"""
make-hugo-like.py - Hugo-style Markdown to HTML Static Site Generator (function stubs)

This script provides function stubs for a Hugo-like static site generator in Python.
It assumes use of a template engine (e.g., Jinja2) that supports blocks, inheritance, and partials.
"""

import os
import logging
import yaml
import re
import shutil
import sqlite3
# from jinja2 import Environment, FileSystemLoader  # Uncomment when implementing

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_FILES_DIR = os.path.join(PROJECT_ROOT, 'build', 'files')
BUILD_HTML_DIR = os.path.join(PROJECT_ROOT, 'build')
LOG_PATH = os.path.join(PROJECT_ROOT, 'log', 'build.log')
LAYOUTS_DIR = os.path.join(PROJECT_ROOT, 'layouts')

# =========================
# Utility Functions
# =========================

def slugify(title: str) -> str:
    """Convert a title to a slug suitable for folder names."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def load_yaml_config(config_path: str) -> dict:
    """Load and parse the YAML config file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logging.info(f"Loaded YAML config from {config_path}")
        return config
    except Exception as e:
        logging.error(f"Failed to load YAML config: {e}")
        return {}

def find_markdown_files(root_dir):
    """Recursively find all non-hidden .md files in root_dir."""
    md_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for filename in filenames:
            if filename.startswith('.'):
                continue
            if filename.lower().endswith('.md'):
                md_files.append(os.path.join(dirpath, filename))
    return md_files

def ensure_output_dir(md_path):
    """Ensure the output directory for the HTML file exists, mirroring build/files structure."""
    rel_path = os.path.relpath(md_path, BUILD_FILES_DIR)
    output_dir = os.path.join(BUILD_HTML_DIR, os.path.dirname(rel_path))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

# =========================
# Template Engine Setup
# =========================

def setup_template_env():
    """Set up Jinja2 template environment."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(LAYOUTS_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return env

# =========================
# Rendering Functions
# =========================

def render_page(context: dict, template_name: str) -> str:
    """
    Render a page using Hugo-style templates (baseof.html, single.html, partials).
    """
    env = setup_template_env()
    template = env.get_template(f'_default/{template_name}')
    return template.render(**context)

# =========================
# Navigation and Partials
# =========================

def generate_nav_menu(context: dict) -> str:
    """Generate navigation menu HTML from TOC in context."""
    toc = context.get('toc', [])
    nav_html = '<nav class="site-nav" role="navigation" aria-label="Main menu"><ul>'
    for entry in toc:
        if entry.get('menu', False):
            title = entry.get('title', '')
            slug = slugify(title)
            link = entry.get('file', None)
            if link:
                link = os.path.splitext(link)[0] + '.html'
            else:
                link = slug + '/index.html'
            nav_html += f'<li><a href="{link}">{title}</a></li>'
    nav_html += '</ul></nav>'
    return nav_html

def get_header_partial(context: dict) -> str:
    """Render header partial using Jinja2."""
    env = setup_template_env()
    template = env.get_template('partials/header.html')
    return template.render(**context)

def get_footer_partial(context: dict) -> str:
    """Render footer partial using Jinja2."""
    env = setup_template_env()
    template = env.get_template('partials/footer.html')
    return template.render(**context)

# =========================
# Markdown Conversion
# =========================

def convert_markdown_to_html(md_path: str) -> str:
    """Convert markdown to HTML using Python markdown."""
    import markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    html_body = markdown.markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'meta'])
    html_body = re.sub(r'src="([^"]+)"', lambda m: f'src="build/{m.group(1)}"' if not m.group(1).startswith('build/') else m.group(0), html_body)
    # Accessibility: Add ARIA roles to elements
    html_body = html_body.replace('<table>', '<table role="table">')
    html_body = html_body.replace('<th>', '<th role="columnheader">')
    html_body = html_body.replace('<td>', '<td role="cell">')
    html_body = html_body.replace('<ul>', '<ul role="list">')
    html_body = html_body.replace('<ol>', '<ol role="list">')
    html_body = html_body.replace('<li>', '<li role="listitem">')
    html_body = html_body.replace('<nav>', '<nav role="navigation">')
    html_body = html_body.replace('<header>', '<header role="banner">')
    html_body = html_body.replace('<footer>', '<footer role="contentinfo">')
    mathjax_script = '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>'
    html_body += mathjax_script
    return html_body

# =========================
# Page Build Workflow
# =========================



def build_all_markdown_files():
    """Build all markdown files using Hugo-style rendering."""
    config_path = os.path.join(PROJECT_ROOT, '_content.yml')
    config = load_yaml_config(config_path)
    site = config.get('site', {})
    toc = config.get('toc', [])
    md_files = find_markdown_files(BUILD_FILES_DIR)
    for md_path in md_files:
        ensure_output_dir(md_path)
        rel_path = os.path.relpath(md_path, BUILD_FILES_DIR)
        html_path = os.path.join(BUILD_HTML_DIR, os.path.splitext(rel_path)[0] + '.html')
        # Extract title from markdown
        with open(md_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        match = re.search(r'^#\s+(.+)', md_text, re.MULTILINE)
        title = match.group(1).strip() if match else "Untitled"
        html_body = convert_markdown_to_html(md_path)
        nav_html = generate_nav_menu({'toc': toc})
        context = {
            'Title': title,
            'Content': html_body,
            'toc': toc,
            'nav': nav_html,
            'site': site,
            # Add more site params as needed
        }
        html_output = render_page(context, 'single.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_output)

def create_section_index_html(section_title: str, output_dir: str, context: dict):
    """Generate section index.html using section.html template."""
    # Find the section in toc
    section = next((entry for entry in context.get('toc', []) if entry.get('title') == section_title), None)
    children = []
    if section and 'children' in section:
        for entry in section['children']:
            children.append({
                'title': entry.get('title', ''),
                'slug': slugify(entry.get('title', '')),
                'link': os.path.splitext(entry.get('file', ''))[0] + '.html' if entry.get('file') else slugify(entry.get('title', '')) + '/index.html'
            })
    page_context = {
        'Title': section_title,
        'Children': children,
        'toc': context.get('toc', []),
        'nav': generate_nav_menu(context),
        'site': context.get('site', {}),
    }
    html_output = render_page(page_context, 'section.html')
    index_html_path = os.path.join(output_dir, 'index.html')
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_all_markdown_files()
