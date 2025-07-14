"""
make.py - Markdown to Accessible HTML Conversion and Site Build Utilities

This script provides functions to convert Markdown files in build/files to accessible standalone HTML pages in build/,
manage WCAG accessibility reports, mirror build/ to docs/, and generate navigation and index pages using a SQLite database.

Features:
- Converts all .md files (recursively, skipping hidden files) to HTML
- Uses highlight.js for code highlighting and injects ARIA attributes
- Injects MathJax from CDN for math rendering
- Renders admonitions as <div class="admonition TYPE"> blocks
- Mirrors directory structure from build/files to build/
- Overwrites HTML files, never overwrites figures or markdown
- Logs events to project root (overwrites each run), errors also printed to console
"""

import os
import logging
import yaml
import re
import shutil
import sqlite3
from oerforge.scan import get_descendants_for_parent

# --- Project Paths and Constants ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_FILES_DIR = os.path.join(PROJECT_ROOT, 'build', 'files')
BUILD_HTML_DIR = os.path.join(PROJECT_ROOT, 'build')
LOG_PATH = os.path.join(PROJECT_ROOT, 'log', 'build.log')

# =========================
# Logging Setup
# =========================

from oerforge.logging_utils import setup_logging

# =========================
# Utility Functions
# =========================

def slugify(title: str) -> str:
    """
    Convert a title to a slug suitable for folder names.

    Args:
        title (str): The title to slugify.

    Returns:
        str: Slugified string.
    """
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def load_yaml_config(config_path: str) -> dict:
    """
    Load and parse the YAML config file.

    Args:
        config_path (str): Path to the YAML config file.

    Returns:
        dict: Parsed YAML configuration.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logging.info(f"Loaded YAML config from {config_path}")
        return config
    except Exception as e:
        logging.error(f"Failed to load YAML config: {e}")
        return {}

def find_markdown_files(root_dir):
    """
    Recursively find all non-hidden .md files in root_dir.

    Args:
        root_dir (str): Root directory to search.

    Returns:
        list: List of markdown file paths.
    """
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
    """
    Ensure the output directory for the HTML file exists, mirroring build/files structure.

    Args:
        md_path (str): Path to the markdown file.
    """
    rel_path = os.path.relpath(md_path, BUILD_FILES_DIR)
    output_dir = os.path.join(BUILD_HTML_DIR, os.path.dirname(rel_path))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

# =========================
# Template Loading and Rendering
# =========================

def load_template(template_path: str) -> str:
    """
    Load the HTML template from the given path.

    Args:
        template_path (str): Path to the HTML template.

    Returns:
        str: Template content.
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template: str, title: str, content: str) -> str:
    """
    Render the template with the given title and content.

    Args:
        template (str): Template string.
        title (str): Page title.
        content (str): Page content.

    Returns:
        str: Rendered HTML.
    """
    return template.replace('{{ title }}', title).replace('{{ content }}', content)

# =========================
# HTML Page Construction
# =========================

def create_header(title: str, nav_html: str) -> str:
    """
    Generate the header HTML, including nav menu and theme toggle button.

    Args:
        title (str): Page title.
        nav_html (str): Navigation HTML.

    Returns:
        str: Header HTML.
    """
    theme_toggle = '<button id="theme-toggle" aria-label="Switch theme" style="float:right; margin:0.5em 1em; font-size:1.5em;">🌙</button>'
    return f'<header class="site-header">\n{theme_toggle}\n<h1 class="site-title">{title}</h1>\n{nav_html}\n</header>'

def create_footer() -> str:
    """
    Generate the footer HTML, reading content from _config.yml if available.

    Returns:
        str: Footer HTML.
    """
    import html
    config_path = os.path.join(PROJECT_ROOT, "_config.yml")
    config = load_yaml_config(config_path)
    footer = config.get("footer", "<!-- footer content here -->")
    if isinstance(footer, dict):
        footer_content = footer.get("text", "")
    else:
        footer_content = str(footer)
    safe_footer = html.escape(footer_content, quote=False)
    safe_footer = re.sub(r'&lt;a ([^&]*)&gt;(.*?)&lt;/a&gt;', r'<a \1>\2</a>', safe_footer)
    for tag in ["<br>", "<br/>", "<strong>", "</strong>", "<em>", "</em>"]:
        safe_footer = safe_footer.replace(html.escape(tag, quote=False), tag)
    return f'<footer>\n{safe_footer}\n</footer>'

def get_top_level_sections(db_path=None):
    """
    Query the database for all top-level sections (is_autobuilt=1, output_path ends with 'index.html').
    Returns a list of (title, output_dir) tuples.
    """
    import sqlite3
    logging.debug(f"[DEBUG] get_top_level_sections (before db_path check): db_path={db_path}")
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
    logging.debug(f"get_top_level_sections (after db_path check): db_path={db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("[DEBUG] SELECT title, output_path FROM content WHERE is_autobuilt=1 AND output_path LIKE '%/index.html'")
    rows = cursor.fetchall()
    conn.close()
    # output_dir is the directory containing index.html
    return [(row[0], os.path.join(PROJECT_ROOT, 'build', os.path.dirname(row[1]))) for row in rows]

def render_page(title: str, content: str, header: str, footer: str, html_path: str) -> str:
    """
    Render the full HTML page using header, content, and footer.

    Args:
        title (str): Page title.
        content (str): Page content.
        header (str): Header HTML.
        footer (str): Footer HTML.
        html_path (str): Output HTML path.

    Returns:
        str: Complete HTML page.
    """
    template_path = os.path.join(PROJECT_ROOT, 'static', 'templates', 'page.html')
    template = load_template(template_path)
    meta = (
        '<meta name="description" content="A modern, open-source course in mathematical methods.">\n'
        '<meta name="author" content="Danny Caballero">\n'
        '<meta name="keywords" content="math, physics, open, oer">\n'
        '<meta name="robots" content="noindex,nofollow">\n'
    )
    def get_asset_prefix(html_path):
        if html_path:
            html_dir = os.path.dirname(html_path)
            build_dir = os.path.join(PROJECT_ROOT, 'build')
            rel_prefix = os.path.relpath(build_dir, start=html_dir)
            if rel_prefix == '.':
                return './'
            else:
                return rel_prefix.rstrip('/') + '/'
        return './'
    rel_prefix = get_asset_prefix(html_path)
    css_links = (
        f'<link rel="stylesheet" href="{rel_prefix}css/theme-light.css" id="theme-light">\n'
        f'<link rel="stylesheet" href="{rel_prefix}css/theme-dark.css" id="theme-dark" disabled>\n'
    )
    js_links = f'<script src="{rel_prefix}js/main.js" defer></script>\n'
    html = template.replace('{{ title }}', title)
    html = html.replace('{{ content }}', content)
    html = html.replace('{{ meta }}', meta)
    html = html.replace('{{ header }}', header)
    html = html.replace('{{ footer }}', footer)
    html = re.sub(r'<link[^>]+id="theme-light"[^>]*>', '', html)
    html = re.sub(r'<link[^>]+id="theme-dark"[^>]*>', '', html)
    html = re.sub(r'<script[^>]+src="(\.|/)js/main.js"[^>]*></script>', '', html)
    html = html.replace('</head>', f'{css_links}{js_links}</head>')
    return html

def generate_nav_menu(toc: list, current_folder: str = '', folder_depth: int = 0, current_html_path: str = '') -> str:
    """
    Generate navigation menu HTML from TOC.

    Args:
        toc (list): Table of contents structure.
        current_folder (str): Current folder path.
        folder_depth (int): Depth of folder nesting.
        current_html_path (str): Path to current HTML file.

    Returns:
        str: Navigation HTML.
    """
    seen_titles = set()
    nav_html = '<nav class="site-nav" role="navigation" aria-label="Main menu"><ul>'
    current_dir = os.path.dirname(current_html_path) if current_html_path else ''
    abs_current_html = os.path.abspath(current_html_path) if current_html_path else ''
    for entry in toc:
        if entry.get('menu', False):
            title = entry.get('title', '')
            if title in seen_titles:
                continue
            seen_titles.add(title)
            slug = slugify(title)
            if 'file' in entry:
                target_html = os.path.join(PROJECT_ROOT, 'build', os.path.splitext(entry['file'])[0] + '.html')
            else:
                target_html = os.path.join(PROJECT_ROOT, 'build', slug, 'index.html')
            if current_dir:
                try:
                    link = os.path.relpath(target_html, start=current_dir)
                    abs_link = os.path.abspath(os.path.join(current_dir, link))
                    mark = '✓' if os.path.exists(abs_link) else '✗'
                except Exception as e:
                    logging.error(f"[DEBUG] relpath error: {e}")
                    link = target_html
            else:
                link = target_html
            nav_html += f'<li><a href="{link}">{title}</a></li>'
    nav_html += '</ul></nav>'
    return nav_html

# =========================
# Markdown to HTML Conversion
# =========================

def fix_image_paths(html, db_path=None):
    """
    Fix image paths in HTML. Currently returns original src.

    Args:
        html (str): HTML content.
        db_path (str, optional): Path to database.

    Returns:
        str: HTML with fixed image paths.
    """
    def replace_src(match):
        src = match.group(1)
        filename = os.path.basename(src)
        return f'src="{src}"'
    html = re.sub(r'src="([^"]+)"', replace_src, html)
    return html

def convert_markdown_to_html(md_path, html_path):
    """
    Convert a markdown file to HTML, inject accessibility features, and write output.

    Args:
        md_path (str): Path to markdown file.
        html_path (str): Path to output HTML file.
    """
    print(f"[DEBUG] convert_markdown_to_html: Reading markdown file: {md_path}")
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
    except Exception as e:
        print(f"[ERROR] Failed to read {md_path}: {e}")
        return
    print(f"[DEBUG] Converting markdown to HTML for: {md_path}")
    print(f"[DEBUG] Output HTML path: {html_path}")
    import markdown
    html_body = markdown.markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables', 'toc', 'meta'])
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
    html_body = fix_image_paths(html_body)
    mathjax_script = '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>'
    html_body += mathjax_script
    match = re.search(r'^#\s+(.+)', md_text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        html_body = re.sub(r'<h1[^>]*>.*?</h1>', '', html_body, count=1)
    else:
        title = "Untitled"
    config_path = os.path.join(PROJECT_ROOT, "_config.yml")
    config = load_yaml_config(config_path)
    toc = config.get("toc", [])
    nav_html = generate_nav_menu(toc, current_html_path=html_path)
    header = create_header(title, nav_html)
    footer = create_footer()
    html_output = render_page(title, html_body, header, footer, html_path)
    print(f"[DEBUG] Writing HTML output to: {html_path}")
    try:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"[DEBUG] Wrote HTML file: {html_path}")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_preview = f.read(200)
        print(f"[DEBUG] Preview of written HTML ({html_path}):\n{html_preview}\n...")
    except Exception as e:
        print(f"[ERROR] Could not write or preview HTML {html_path}: {e}")
    logging.info(f"Wrote HTML file: {html_path}")

# --- Build Structure and TOC Functions ---
def build_all_markdown_files(source_dir, build_dir):
    import logging
    import sqlite3
    db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
    import logging
    logging.info(f"[DB-OPEN] Attempting to open database: {db_path}")
    conn = sqlite3.connect(db_path)
    logging.info(f"[DB-OPEN] Database connection established: {db_path}")
    cursor = conn.cursor()
    cursor.execute("SELECT source_path, output_path FROM content WHERE source_path LIKE '%.md' AND output_path LIKE '%.html'")
    rows = cursor.fetchall()
    logging.info(f"[DB-CLOSE] Database connection closed: {db_path}")
    conn.close()
    print(f"[DEBUG] build_all_markdown_files: Found markdown files ({len(rows)}):")
    for src_path, out_path in rows:
        if not src_path or not out_path:
            continue
        abs_src_path = os.path.join(PROJECT_ROOT, src_path) if not os.path.isabs(src_path) else src_path
        abs_out_path = os.path.join(PROJECT_ROOT, out_path) if not os.path.isabs(out_path) else out_path
        output_dir = os.path.dirname(abs_out_path)
        print(f"  [DEBUG] Will convert: {abs_src_path} -> {abs_out_path}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"  [DEBUG] Created output directory: {output_dir}")
        convert_markdown_to_html(abs_src_path, abs_out_path)
        print(f"  [DEBUG] Converted {abs_src_path} to {abs_out_path}")

def create_section_index_html(section_title, output_dir, db_path=None, parent_id=None):
    """
    Generate index.html for a section, listing all children and grandchildren recursively using the database.
    Each child/grandchild page can have a nav menu linking to top-level pages.
    """
    import os
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')

    # --- Build nav menu from TOC (same as all other pages) ---
    config_path = os.path.join(PROJECT_ROOT, "_config.yml")
    config = load_yaml_config(config_path)
    toc = config.get("toc", [])
    nav_html = generate_nav_menu(toc, current_html_path=os.path.join(output_dir, 'index.html'))

    # --- Use recursive CTE to get all descendants ---
    parent_output_path = os.path.join('build', os.path.relpath(output_dir, os.path.join(PROJECT_ROOT, 'build')), 'index.html')
    descendants = get_descendants_for_parent(parent_output_path, db_path)
    links_html = '<ul>'
    current_dir = output_dir
    for d in descendants:
        abs_target_html = os.path.join(PROJECT_ROOT, d['output_path']) if not os.path.isabs(d['output_path']) else d['output_path']
        rel_link = os.path.relpath(abs_target_html, start=current_dir)
        mark = '✓' if os.path.exists(abs_target_html) else '✗'
        indent = '&nbsp;' * (d['level'] * 4)
        links_html += f'<li>{indent}<a href="{rel_link}">{d["title"]}</a> [{mark}]</li>'
    links_html += '</ul>'
    header = create_header(section_title, nav_html)
    footer = create_footer()
    page_html = render_page(section_title, links_html, header, footer, os.path.join(output_dir, 'index.html'))
    index_html_path = os.path.join(output_dir, 'index.html')
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(page_html)
    logging.info(f"Created section index with descendant links: {index_html_path}")

def get_markdown_source_and_output_paths_from_db(db_path=None):
    """
    Get all markdown source and output paths using the database.
    Args:
        db_path (str, optional): Path to the SQLite database file.
    Returns:
        List of (source_path, output_path) tuples.
    """
    import sqlite3
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT source_path, output_path FROM content WHERE output_path LIKE '%.html'")
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]
    """
    Generate index.html for a section using the database.
    Args:
        section_title (str): Title of the section.
        output_dir (str): Output directory for the section index.
        db_path (str, optional): Path to the SQLite database file.
    """
    import sqlite3
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
    output_dir_rel = os.path.relpath(output_dir, os.path.join(PROJECT_ROOT, 'build'))
    like_pattern = output_dir_rel + '/%'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, output_path FROM content WHERE is_autobuilt=1 AND output_path LIKE ?", (like_pattern,))
    rows = cursor.fetchall()
    conn.close()
    links_html = '<ul>'
    current_dir = output_dir
    for child_title, target_html in rows:
        abs_target_html = os.path.join(PROJECT_ROOT, 'build', target_html) if not os.path.isabs(target_html) else target_html
        rel_link = os.path.relpath(abs_target_html, start=current_dir)
        mark = '✓' if os.path.exists(abs_target_html) else '✗'
        links_html += f'<li><a href="{rel_link}">{child_title}</a> [{mark}]</li>'
    links_html += '</ul>'
    header = create_header(section_title, '')
    footer = create_footer()
    page_html = render_page(section_title, links_html, header, footer, os.path.join(output_dir, 'index.html'))
    index_html_path = os.path.join(output_dir, 'index.html')
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(page_html)
    logging.info(f"Created section index with child links: {index_html_path}")

if __name__ == "__main__":
    setup_logging()
    logging.info("Logging started.")
    build_all_markdown_files(BUILD_FILES_DIR, BUILD_HTML_DIR)
    logging.info("Markdown built.")
    # Autogenerate index.html for all top-level sections from the database
    for section_title, output_dir in get_top_level_sections():
        logging.info(f"Section Title: {section_title}, Output Dir: {output_dir}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        logging.info(f"[AUTO] Generating section index for: {section_title} at {output_dir}")
        create_section_index_html(section_title, output_dir)