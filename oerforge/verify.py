"""
verify.py

Accessibility compliance verification using Pa11y.
- Supports single file, batch, and all-pages modes.
- Stores results in accessibility_results table.
- Generates badges and a compliance summary page.
"""

import os
import sys
import sqlite3
import subprocess
import json
import logging
from typing import Optional, Dict, Any, List

# Ensure project root is in sys.path for module imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up logging for Pa11y debug
log_dir = os.path.join(project_root, "log")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "pa11y.log")
logging.basicConfig(
    filename=log_path,
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
logging.debug("verify.py started. Logging to %s", log_path)

def run_pa11y_on_file(html_path: str, config_path: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Run Pa11y on a single HTML file. Returns parsed JSON result, or None on error.
    """
    html_abs = os.path.abspath(html_path)
    config_abs = os.path.abspath(config_path) if config_path else None
    pa11y_cmd = ["pa11y", f"file://{html_abs}", "--reporter", "json"]
    if config_abs:
        pa11y_cmd.extend(["--config", config_abs])
    logging.debug(f"Running command: {' '.join(pa11y_cmd)}")
    try:
        result = subprocess.run(pa11y_cmd, capture_output=True, text=True, check=True)
        logging.debug(f"stdout: {result.stdout}")
        logging.debug(f"stderr: {result.stderr}")
        return json.loads(result.stdout)
    except FileNotFoundError:
        logging.error("Error: pa11y is not installed or not found in PATH.")
        print("Error: pa11y is not installed or not found in PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Pa11y failed for {html_path}: {e.stderr}")
        logging.error(f"stdout: {e.stdout}")
        try:
            issues = json.loads(e.stdout)
            logging.info(f"Accessibility issues: {json.dumps(issues, indent=2)}")
            return issues
        except Exception as parse_err:
            logging.error(f"Failed to parse Pa11y JSON output after error: {parse_err}")
            return None
    except json.JSONDecodeError:
        logging.error(f"Failed to parse Pa11y JSON output for {html_path}.")
        return None

def store_accessibility_result(content_id: int, pa11y_json: Any, badge_html: str, wcag_level: str, error_count: int, warning_count: int, notice_count: int, conn=None):
    """
    Store the latest accessibility result for a page in the database.
    """
    if conn is None:
        raise ValueError("A valid database connection is required.")
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM accessibility_results WHERE content_id = ? AND wcag_level = ?
    """, (content_id, wcag_level))
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

def generate_badge_html(wcag_level: str, error_count: int) -> str:
    color = "#4caf50" if error_count == 0 else "#f44336"
    label = f"WCAG {wcag_level.upper()}"
    status = "PASS" if error_count == 0 else f"{error_count} ERRORS"
    return f'<span style="background:{color};color:#fff;padding:2px 6px;border-radius:4px;font-size:90%">{label}: {status}</span>'

def get_pages_to_check(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT id, output_path FROM content WHERE output_path LIKE '%.html'")
    return [{"id": row[0], "output_path": row[1]} for row in cursor.fetchall()]

def read_config_order_from_yaml(yaml_path: str) -> List[str]:
    """
    Stub: Read config order from a YAML file.
    Not yet implemented.
    """
    # TODO: Implement reading config order from YAML
    return []

def generate_compliance_table_page(conn, output_path: str):
    """
    Generate a static HTML page summarizing accessibility compliance for all pages.
    Uses Jinja2 template for rendering.
    """
    from oerforge.make import render_page

    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT wcag_level FROM accessibility_results ORDER BY wcag_level")
    configs = [row[0] for row in cursor.fetchall()]
    cursor.execute('''
        SELECT ar.content_id, ar.wcag_level, ar.error_count, ar.checked_at, c.title, c.output_path
        FROM accessibility_results ar
        JOIN content c ON ar.content_id = c.id
        ORDER BY c.output_path, ar.wcag_level
    ''')
    rows = cursor.fetchall()
    # Build mapping: page -> {title, output_path, last_checked, results_by_config}
    pages = {}
    for content_id, wcag_level, error_count, checked_at, title, output_path in rows:
        if output_path not in pages:
            pages[output_path] = {
                'title': title,
                'output_path': output_path,
                'last_checked': checked_at,
                'results': {}
            }
        if checked_at > pages[output_path]['last_checked']:
            pages[output_path]['last_checked'] = checked_at
        pages[output_path]['results'][wcag_level] = error_count

    # Prepare rows for the template
    table_rows = []
    for page in pages.values():
        row = {
            'title': page['title'],
            'output_path': page['output_path'],
            'configs': [],
            'last_checked': page['last_checked'],
        }
        for cname in configs:
            err = page['results'].get(cname)
            if err is None:
                row['configs'].append({'error_count': None, 'checked': False})
            else:
                row['configs'].append({'error_count': err, 'checked': err == 0})
        table_rows.append(row)

    context = {
        'configs': configs,
        'rows': table_rows,
        'title': 'Accessibility Compliance Summary',
        'site': {
            'favicon': 'static/images/favicon.ico',
            'title': 'Open Physics Ed',
            'subtitle': 'Accessible OER for Physics',
        },
        'css_path': 'css/theme-light.css',
        'js_path': 'js/main.js',
        'logo_path': 'images/logo.png',
        'top_menu': [],
    }

    html = render_page(context, 'compliance-summary.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def ensure_accessibility_results_table(conn, drop_and_recreate=False):
    cursor = conn.cursor()
    if drop_and_recreate:
        cursor.execute("DROP TABLE IF EXISTS accessibility_results")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accessibility_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            pa11y_json TEXT,
            badge_html TEXT,
            wcag_level TEXT,
            error_count INTEGER,
            warning_count INTEGER,
            notice_count INTEGER,
            checked_at TEXT,
            FOREIGN KEY(content_id) REFERENCES content(id)
        )
    """)
    conn.commit()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Accessibility verification with Pa11y")
    parser.add_argument("--config", "-c", type=str, help="Path to Pa11y config file (default: pa11y.config.json in project root if present)")
    parser.add_argument("--all", action="store_true", help="Check all HTML files in the database (batch mode)")
    parser.add_argument("--reset-results", action="store_true", help="Drop and recreate the accessibility_results table before running")
    parser.add_argument("--summary", action="store_true", help="Generate accessibility compliance summary page only")
    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        default_config = os.path.join(project_root, "pa11y.config.json")
        if os.path.exists(default_config):
            config_path = default_config

    db_path = os.path.join(project_root, "db", "sqlite.db")
    conn = sqlite3.connect(db_path)
    ensure_accessibility_results_table(conn, drop_and_recreate=args.reset_results)

    if args.summary:
        output_path = os.path.join(project_root, "build", "compliance-summary.html")
        generate_compliance_table_page(conn, output_path)
        print(f"Compliance summary page generated at {output_path}")
        conn.close()
        return

    if args.all:
        pages = get_pages_to_check(conn)
        print(f"Checking {len(pages)} HTML files from database...")
        config_name = None
        if config_path:
            config_base = os.path.basename(config_path)
            if config_base.endswith('.json'):
                config_name = config_base[:-5]
            else:
                config_name = config_base
        else:
            config_name = "default"
        for page in pages:
            html_path = page["output_path"]
            if not os.path.exists(html_path):
                print(f"File not found: {html_path}")
                continue
            print(f"\n=== Checking: {html_path} ===")
            result = run_pa11y_on_file(html_path, config_path)
            error_count = 0
            warning_count = 0
            notice_count = 0
            if isinstance(result, list):
                for issue in result:
                    if isinstance(issue, dict):
                        t = issue.get("type")
                        if t == "error":
                            error_count += 1
                        elif t == "warning":
                            warning_count += 1
                        elif t == "notice":
                            notice_count += 1
            wcag_level = config_name
            badge_html = generate_badge_html(wcag_level, error_count)
            store_accessibility_result(
                content_id=page["id"],
                pa11y_json=result if result is not None else [],
                badge_html=badge_html,
                wcag_level=wcag_level,
                error_count=error_count,
                warning_count=warning_count,
                notice_count=notice_count,
                conn=conn
            )
            if result is not None and result != []:
                try:
                    print(json.dumps(result, indent=2))
                except Exception:
                    print(result)
            elif result == []:
                print("No accessibility issues found (empty list).")
            else:
                print("No Pa11y result or error occurred.")
        conn.close()
    else:
        html_path = os.path.join("build", "index.html")
        if not os.path.exists(html_path):
            print(f"File not found: {html_path}")
            return
        result = run_pa11y_on_file(html_path, config_path)
        print("Raw Pa11y result:", result)
        if result is not None and result != []:
            try:
                print(json.dumps(result, indent=2))
            except Exception:
                print(result)
        elif result == []:
            print("No accessibility issues found (empty list).")
        else:
            print("No Pa11y result or error occurred.")

if __name__ == "__main__":
    main()