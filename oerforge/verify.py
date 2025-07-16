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

def generate_wcag_report(html_path: str, issues: List[Dict[str, Any]], badge_html: str, config: dict):
    """Generate a detailed HTML report for the file using a Jinja2 template."""
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
        os.path.join(base_dir, 'partials')
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

    context = {
        'title': config.get('title', html_filename),
        'favicon': site.get('favicon', config.get('favicon', '/images/favion.ico')),
        'css_path': config.get('css_path', '/css/theme-light.css'),
        'js_path': config.get('js_path', '/js/main.js'),
        'wcag_level': config.get('wcag_level', 'AA'),
        'error_count': sum(1 for i in issues if i.get('type') == 'error'),
        'warning_count': sum(1 for i in issues if i.get('type') == 'warning'),
        'notice_count': sum(1 for i in issues if i.get('type') == 'notice'),
        'badge_html': badge_html,
        'issues': issues,
        'site': site,
        'footer_text': footer_text,
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