"""
make-hugo-like.py - Hugo-style Markdown to HTML Static Site Generator (function stubs)

This script provides function stubs for a Hugo-like static site generator in Python.
It assumes use of a template engine (e.g., Jinja2) that supports blocks, inheritance, and partials.
"""

from multiprocessing import context
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

def get_top_level_menu(db_path, rel_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, output_path FROM content WHERE parent_output_path IS NULL OR parent_output_path = ''")
    menu = []
    for title, output_path in cursor.fetchall():
        # Compute link relative to current page
        link = os.path.relpath(output_path, os.path.dirname(os.path.join(BUILD_HTML_DIR, rel_path)))
        menu.append({'title': title, 'link': link})
    conn.close()
    return menu

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
    """Convert markdown to HTML using markdown-it-py, rewriting local image paths to images/filename.ext without regex."""
    from markdown_it import MarkdownIt
    from mdit_py_plugins.footnote import footnote_plugin
    from mdit_py_plugins.texmath import texmath_plugin
    import os
    import html
    def custom_image_renderer(self, tokens, idx, options, env):
        token = tokens[idx]
        src = token.attrs.get('src', '')
        # Only rewrite if not external or already in images/
        if not (src.startswith('http') or src.startswith('/') or src.startswith('images/')):
            filename = os.path.basename(src)
            src = f'images/{filename}'
        alt = html.escape(token.content)
        return f'<img src="{src}" alt="{alt}">'  # basic fallback
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": True})
    md.use(footnote_plugin)
    md.use(texmath_plugin)
    md.add_render_rule('image', custom_image_renderer)
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    html_body = md.render(md_text)
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

def get_asset_path(asset_type, asset_name, rel_path):
    depth = rel_path.count(os.sep)
    prefix = '../' * depth if depth > 0 else ''
    return f"{prefix}{asset_type}/{asset_name}"

def add_asset_paths(context, rel_path):
    context['css_path'] = get_asset_path('css', 'theme-light.css', rel_path)
    context['js_path'] = get_asset_path('js', 'main.js', rel_path)
    return context

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
        context = add_asset_paths(context, rel_path)
        db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
        top_menu = get_top_level_menu(db_path, rel_path)
        context['top_menu'] = top_menu
        html_output = render_page(context, 'single.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_output)

def create_section_index_html(section_title: str, output_dir: str, context: dict):
    """Generate section index.html using section.html template."""
    # Find the section in toc
    import logging
    logging.info(f"[DEBUG] create_section_index_html called for: {section_title} -> {output_dir}")
    try:
        section = next((entry for entry in context.get('toc', []) if entry.get('title') == section_title), None)
        children = []
        if section and 'children' in section:
            logging.info(f"[DEBUG] Section found in TOC: {section_title}")
            for entry in section['children']:
                # If child has a file, use its HTML path relative to section, else use slug/index.html
                if entry.get('file'):
                    # Remove any leading section path from file
                    file_path = entry.get('file')
                    # If file_path is like news/xxx.md, just use xxx.html
                    base_name = os.path.splitext(os.path.basename(file_path))[0] + '.html'
                    link = base_name
                else:
                    link = slugify(entry.get('title', '')) + '/index.html'
                children.append({
                    'title': entry.get('title', ''),
                    'slug': slugify(entry.get('title', '')),
                    'link': link
                })
            logging.info(f"[DEBUG] Children for {section_title}: {children}")
        else:
            logging.warning(f"[DEBUG] No children found for section: {section_title}")
            children = []
        rel_path = os.path.relpath(os.path.join(output_dir, 'index.html'), BUILD_HTML_DIR)
        page_context = {
            'Title': section_title,
            'Children': children,
            'toc': context.get('toc', []),
            'nav': generate_nav_menu(context),
            'site': context.get('site', {}),
        }
        page_context = add_asset_paths(page_context, rel_path)
        db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
        top_menu = get_top_level_menu(db_path, rel_path)
        page_context['top_menu'] = top_menu
        html_output = render_page(page_context, 'section.html')
        index_html_path = os.path.join(output_dir, 'index.html')
        os.makedirs(output_dir, exist_ok=True)
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        logging.info(f"[DEBUG] Wrote section index: {index_html_path}")
    except Exception as e:
        logging.error(f"[ERROR] Failed to write section index for {section_title} at {output_dir}: {e}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_all_markdown_files()
