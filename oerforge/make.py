"""
make-hugo-like.py - Hugo-style Markdown to HTML Static Site Generator (function stubs)

This script provides function stubs for a Hugo-like static site generator in Python.
It assumes use of a template engine (e.g., Jinja2) that supports blocks, inheritance, and partials.
"""

# from multiprocessing import context  # Removed invalid import
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
    layouts_default = os.path.join(LAYOUTS_DIR, '_default')
    env = Environment(
        loader=FileSystemLoader([LAYOUTS_DIR, layouts_default]),
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
    import os
    """Generate navigation menu items for top_menu from TOC in context."""
    toc = context.get('toc', [])
    db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    menu_items = []
    # Compute relative links based on current page's rel_path if present in context
    rel_path = context.get('rel_path', '')
    for entry in toc:
        if entry.get('menu', False):
            title = entry.get('title')
            logging.info(f"[MENU] Looking up menu item: '{title}'")
            cursor.execute("SELECT output_path, source_path FROM content WHERE title=? AND (parent_output_path IS NULL OR parent_output_path = '')", (title,))
            row = cursor.fetchone()
            if row:
                output_path, source_path = row
                # Compute relative link from rel_path to menu target
                if output_path.startswith('build/'):
                    target = output_path[6:]
                else:
                    target = output_path.lstrip('/')
                # For Home, always use 'index.html'
                if title.lower() == 'home':
                    target = 'index.html'
                # If rel_path is set, compute relative path
                if rel_path:
                    import os
                    link = os.path.relpath(target, os.path.dirname(rel_path))
                else:
                    link = target
                menu_items.append({'title': title, 'link': link})
            else:
                logging.warning(f"[MENU] No DB record found for menu item: '{title}'")
    conn.close()
    return menu_items

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

def convert_markdown_to_html_text(md_text: str) -> str:
    """Convert markdown text to HTML using markdown-it-py, rewriting local image paths to images/filename.ext without regex."""
    from markdown_it import MarkdownIt
    from mdit_py_plugins.footnote import footnote_plugin
    from mdit_py_plugins.texmath import texmath_plugin
    import os
    import html
    def custom_image_renderer(self, tokens, idx, options, env):
        token = tokens[idx]
        src = token.attrs.get('src', '')
        if not (src.startswith('http') or src.startswith('/') or src.startswith('images/')):
            filename = os.path.basename(src)
            src = f'images/{filename}'
        alt = html.escape(token.content)
        return f'<img src="{src}" alt="{alt}">'  # basic fallback
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": True})
    md.use(footnote_plugin)
    md.use(texmath_plugin)
    md.add_render_rule('image', custom_image_renderer)
    html_body = md.render(md_text)
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
    context['css_path'] = get_asset_path('css', 'theme-dark.css', rel_path)
    context['js_path'] = get_asset_path('js', 'main.js', rel_path)
    # Add logo_path for correct logo asset referencing
    logo_file = context.get('site', {}).get('logo', 'static/images/logo.png')
    # Remove 'static/' prefix if present, since assets are in build/images/
    logo_name = os.path.basename(logo_file)
    context['logo_path'] = get_asset_path('images', logo_name, rel_path)
    return context

def build_all_markdown_files():
    """Build all markdown files using Hugo-style rendering, using first # header as title."""
    config_path = os.path.join(PROJECT_ROOT, '_content.yml')
    config = load_yaml_config(config_path)
    site = config.get('site', {})
    toc = config.get('toc', [])
    footer_text = config.get('footer', {}).get('text', '')
    db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT source_path, output_path, title, mime_type FROM content")
    records = cursor.fetchall()
    # Build homepage from content/index.md to build/index.html
    homepage_md = os.path.join(PROJECT_ROOT, 'content', 'index.md')
    homepage_html = os.path.join(BUILD_HTML_DIR, 'index.html')
    if os.path.exists(homepage_md):
        try:
            with open(homepage_md, 'r', encoding='utf-8') as f:
                md_text = f.read()
            # Use first # header as title
            title = "Home"
            lines = md_text.splitlines()
            body_lines = []
            found_title = False
            for line in lines:
                if not found_title and line.strip().startswith('# '):
                    title = line.strip()[2:].strip()
                    found_title = True
                    continue
                body_lines.append(line)
            body_text = '\n'.join(body_lines)
            html_body = convert_markdown_to_html_text(body_text)
            top_menu = generate_nav_menu({'toc': toc})
            rel_path = 'index.html'
            context = {
                'Title': title,
                'Content': html_body,
                'toc': toc,
                'top_menu': top_menu,
                'site': site,
                'footer_text': footer_text,
                'output_file': 'index.html',
            }
            context = add_asset_paths(context, rel_path)
            html_output = render_page(context, 'single.html')
            with open(homepage_html, 'w', encoding='utf-8') as f:
                f.write(html_output)
            logging.info(f"[AUTO] Built homepage: {homepage_html}")
        except Exception as e:
            logging.error(f"Failed to build homepage from {homepage_md}: {e}")
    # Filter for markdown files robustly by extension or mime_type
    for source_path, output_path, db_title, mime_type in records:
        # Skip records with missing source_path or output_path
        if not source_path or not output_path:
            logging.info(f"Skipping record with missing source_path or output_path: title={db_title}, source_path={source_path}, output_path={output_path}")
            continue
        ext = os.path.splitext(source_path)[1].lower()
        # You can extend this list for other MIME types as needed
        if ext == '.md' or (mime_type and 'markdown' in mime_type.lower()):
            # Read markdown from source_path
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()
            except Exception as e:
                logging.error(f"Failed to read markdown file {source_path}: {e}")
                continue
            # Extract first # header as title if not present in DB
            title = db_title or "Untitled"
            lines = md_text.splitlines()
            body_lines = []
            found_title = False
            for line in lines:
                if not found_title and line.strip().startswith('# '):
                    if not db_title:
                        title = line.strip()[2:].strip()
                    found_title = True
                    continue  # skip this line
                body_lines.append(line)
            body_text = '\n'.join(body_lines)
            html_body = convert_markdown_to_html(source_path) if not found_title else convert_markdown_to_html_text(body_text)
            top_menu = generate_nav_menu({'toc': toc})
            # Patch: output single files as folder/index.html
            md_basename = os.path.splitext(os.path.basename(source_path))[0]
            parent_dir = os.path.basename(os.path.dirname(source_path))
            # Only patch if file is in a subfolder and matches parent folder name (e.g. about.md in about/)
            if md_basename == parent_dir:
                output_dir = os.path.join(BUILD_HTML_DIR, parent_dir)
                os.makedirs(output_dir, exist_ok=True)
                output_path_final = os.path.join(output_dir, 'index.html')
                rel_path = os.path.relpath(output_path_final, BUILD_HTML_DIR)
                output_file = 'index.html'
            else:
                output_path_final = output_path
                rel_path = os.path.relpath(output_path_final, BUILD_HTML_DIR)
                output_file = os.path.basename(output_path_final)
                out_dir = os.path.dirname(output_path_final)
                os.makedirs(out_dir, exist_ok=True)
            context = {
                'Title': title,
                'Content': html_body,
                'toc': toc,
                'top_menu': top_menu,
                'site': site,
                'footer_text': footer_text,
                'output_file': output_file,
            }
            context = add_asset_paths(context, rel_path)
            html_output = render_page(context, 'single.html')
            try:
                with open(output_path_final, 'w', encoding='utf-8') as f:
                    f.write(html_output)
            except Exception as e:
                logging.error(f"Failed to write HTML file {output_path_final}: {e}")
    conn.close()

def create_section_index_html(section_title: str, output_dir: str, context: dict):
    """Generate section index.html using section.html template."""
    import logging
    logging.info(f"[DEBUG] create_section_index_html called for: {section_title} -> {output_dir}")
    try:
        section = next((entry for entry in context.get('toc', []) if entry.get('title') == section_title), None)
        children = []
        if section and 'children' in section:
            logging.info(f"[DEBUG] Section found in TOC: {section_title}")
            for entry in section['children']:
                if entry.get('file'):
                    file_path = entry.get('file')
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
        # Ensure site.title and site.subtitle are always present
        config_path = os.path.join(PROJECT_ROOT, '_content.yml')
        config = load_yaml_config(config_path)
        site = config.get('site', {})
        footer_text = config.get('footer', {}).get('text', '')
        # Add top_menu to page_context for navigation
        top_menu = generate_nav_menu({'toc': context.get('toc', [])})
        page_context = {
            'Title': section_title,
            'Children': children,
            'toc': context.get('toc', []),
            'top_menu': top_menu,
            'site': site,
            'footer_text': footer_text,
        }
        page_context = add_asset_paths(page_context, rel_path)
        try:
            env = setup_template_env()
            template = env.get_template('section.html')
            html_output = template.render(**page_context)
        except Exception as render_err:
            logging.error(f"[ERROR] Template rendering failed for {section_title}: {render_err}")
            import traceback
            logging.error(traceback.format_exc())
            html_output = None
        # Ensure output directory exists
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as dir_err:
            logging.error(f"[ERROR] Failed to create output directory {output_dir}: {dir_err}")
        # Write index.html with error logging
        if html_output:
            try:
                with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
                    f.write(html_output)
            except Exception as file_err:
                logging.error(f"[ERROR] Failed to write index.html for {section_title} in {output_dir}: {file_err}")
                import traceback
                logging.error(traceback.format_exc())
    except Exception as e:
        logging.error(f"[ERROR] Failed to create section index for {section_title}: {e}")
        import traceback
        logging.error(traceback.format_exc())
