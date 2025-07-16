import os
import sys
import sqlite3
import subprocess
import json
from typing import Optional, Dict, Any, List
import logging
logging.basicConfig(
    filename="log/pa11y.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# --- Config and Logging ---
def load_pa11y_config(yml_path: str = "_content.yml") -> dict:
    """Load pa11y config and logo info from _content.yml and/or pa11y-configs/wcag_logos.json."""
    import yaml
    yml_path = os.path.abspath(yml_path)
    if not os.path.exists(yml_path):
        return {}
    with open(yml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data or {}


# --- Pa11y Integration ---
def run_pa11y_on_file(html_path: str, config_path: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Run Pa11y on a single HTML file. Returns parsed JSON result, or None on error.
    """
    html_abs = os.path.abspath(html_path)
    pa11y_cmd = ["pa11y", f"file://{html_abs}", "--reporter", "json"]
    if config_path:
        pa11y_cmd.extend(["--config", os.path.abspath(config_path)])
    try:
        logging.info(f"Running Pa11y on {html_path} with command: {' '.join(pa11y_cmd)}")
        result = subprocess.run(pa11y_cmd, capture_output=True, text=True, check=True)
        logging.info(f"Pa11y output for {html_path}: {result.stdout}")
        return json.loads(result.stdout)
    except FileNotFoundError:
        logging.error("Pa11y is not installed or not found in PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Pa11y failed for {html_path}: {e.stderr}")
        try:
            return json.loads(e.stdout)
        except Exception as parse_err:
            logging.error(f"Failed to parse Pa11y JSON output after error: {parse_err}")
            return None
    except json.JSONDecodeError:
        logging.error(f"Failed to parse Pa11y JSON output for {html_path}.")
        return None

# --- DB Operations ---
def get_content_id_for_file(html_path: str, conn) -> Optional[int]:
    """Get the content_id for a given HTML file from the DB."""
    # Normalize path for DB comparison
    html_path = os.path.abspath(html_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, output_path FROM content")
    for row in cursor.fetchall():
        db_id, db_path = row
        if os.path.abspath(db_path) == html_path:
            return db_id
    logging.warning(f"No content_id found for {html_path}")
    return None

def store_accessibility_result(content_id: int, pa11y_json: List[Dict[str, Any]], badge_html: str, wcag_level: str, error_count: int, warning_count: int, notice_count: int, conn=None):
    """Store the latest accessibility result for a page in the database."""
    if conn is None:
        raise ValueError("A valid database connection is required.")
    cursor = conn.cursor()
    # Remove old result for this content_id and wcag_level
    cursor.execute("""
        DELETE FROM accessibility_results WHERE content_id = ? AND wcag_level = ?
    """, (content_id, wcag_level))
    # Insert new result
    cursor.execute("""
        INSERT INTO accessibility_results (
            content_id, pa11y_json, badge_html, wcag_level, error_count, warning_count, notice_count, checked_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        content_id,
        json.dumps(pa11y_json),
        badge_html,
        wcag_level,
        error_count,
        warning_count,
        notice_count
    ))
    conn.commit()

def get_pages_to_check(conn) -> List[Dict[str, Any]]:
    """Return a list of pages (from content table) to check for accessibility."""
    pass

# --- Badge and Report Generation ---
def generate_badge_html(wcag_level: str, error_count: int, logo_info: dict) -> str:
    """Generate badge HTML for a given WCAG level and error count, using logo info."""
    pass

def inject_badge_into_html(html_path: str, badge_html: str, report_link: str):
    """Inject the badge/button into the HTML file after <main>."""
    pass


# --- Navigation Menu Generation (ported from make.py) ---
def generate_nav_menu(context: dict) -> list:
    import os
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(PROJECT_ROOT, 'db', 'sqlite.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    menu_items = []
    rel_path = context.get('rel_path', '')
    # Query for top-level menu items (menu_context='main', parent_output_path is NULL or empty)
    sql = "SELECT title, relative_link FROM content WHERE menu_context='main' AND (parent_output_path IS NULL OR parent_output_path = '') ORDER BY \"order\";"
    cursor.execute(sql)
    rows = cursor.fetchall()
    for title, relative_link in rows:
        # For Home, always use 'index.html'
        if title and title.lower() == 'home':
            target = 'index.html'
        else:
            target = relative_link
        # Compute menu links relative to the current page's directory
        if rel_path:
            current_dir = os.path.dirname(rel_path)
            is_section_index = (
                rel_path.endswith('index.html') and
                current_dir and
                rel_path != 'index.html'
            )
            if is_section_index:
                # If this menu item is the current section, use "index.html"
                if target == rel_path or os.path.normpath(target) == os.path.normpath(rel_path):
                    link = "index.html"
                else:
                    link = "../" + target
            else:
                link = os.path.relpath(target, current_dir) if not os.path.isabs(target) else target
        else:
            link = target
        menu_items.append({'title': title, 'link': link})
    conn.close()
    return menu_items

def generate_wcag_report(html_path: str, issues: List[Dict[str, Any]], badge_html: str, config: dict):
    """Generate a detailed HTML report for the file using a Jinja2 template that extends baseof.html."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    # Determine output path: wcag_report_FILENAME.html in same dir as html_path
    html_dir = os.path.dirname(html_path)
    html_filename = os.path.basename(html_path)
    if html_filename.endswith('.html'):
        report_filename = f"wcag_report_{html_filename}"
    else:
        report_filename = f"wcag_report.html"
    report_path = os.path.join(html_dir, report_filename)

    # Setup Jinja2 environment to search both reports and partials
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../layouts'))
    template_dirs = [
        os.path.join(base_dir, 'reports'),
        os.path.join(base_dir, 'partials'),
        os.path.join(base_dir, '_default'),
    ]
    env = Environment(
        loader=FileSystemLoader(template_dirs),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('wcag_report.html')

    # Load site and footer info from _content.yml
    site_config = load_pa11y_config(os.path.abspath(os.path.join(os.path.dirname(__file__), '../_content.yml')))
    site = site_config.get('site', {})
    footer_text = site_config.get('footer', {}).get('text', '')

    # Compute relative asset paths from report location
    build_dir = os.path.abspath(os.path.join(html_dir, '..'))
    css_path = os.path.relpath(os.path.join(build_dir, 'css/theme-light.css'), html_dir)
    js_path = os.path.relpath(os.path.join(build_dir, 'js/main.js'), html_dir)
    favicon = os.path.relpath(os.path.join(build_dir, 'images/favicon.ico'), html_dir)
    logo_path = os.path.relpath(os.path.join(build_dir, 'images/logo.png'), html_dir)

    # Try to extract page title from HTML file (fallback to config or filename)
    page_title = config.get('title', html_filename)
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '<title>' in line:
                    import re
                    m = re.search(r'<title>(.*?)</title>', line)
                    if m:
                        page_title = m.group(1).strip()
                        break
    except Exception:
        pass

    # Compute relative URL from build/ root
    build_root = os.path.abspath(os.path.join(html_dir, '..'))
    relative_url = os.path.relpath(html_path, build_root)

    # Compute rel_path for the report (relative to build/)
    rel_path = os.path.relpath(report_path, build_root)
    # Generate the top menu using the same logic as make.py
    top_menu = generate_nav_menu({'rel_path': rel_path})

    context = {
        'Title': page_title,  # For {% block title %} in baseof.html
        'page_title': page_title,
        'relative_url': relative_url,
        'site': site,
        'css_path': css_path,
        'js_path': js_path,
        'favicon': favicon,
        'logo_path': logo_path,
        'wcag_level': config.get('wcag_level', 'AA'),
        'error_count': sum(1 for i in issues if i.get('type') == 'error'),
        'warning_count': sum(1 for i in issues if i.get('type') == 'warning'),
        'notice_count': sum(1 for i in issues if i.get('type') == 'notice'),
        'badge_html': badge_html,
        'issues': issues,
        'footer_text': footer_text,
        'top_menu': top_menu,
        'rel_path': rel_path,
    }

    # Render and write
    rendered = template.render(**context)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(rendered)
    logging.info(f"Generated WCAG report: {report_path}")
    return report_path

# --- Utility ---
def copy_to_docs():
    """Copy all changed files from build/ to docs/."""
    pass

# --- CLI Entry Point ---
def main():
    """Parse CLI args, run checks, store results, and generate reports as needed."""
    pass

if __name__ == "__main__":
    main()