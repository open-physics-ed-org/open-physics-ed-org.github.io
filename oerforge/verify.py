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

def generate_badge_html(wcag_level: str, error_count: int, logo_info=None) -> str:
    color = "#4caf50" if error_count == 0 else "#f44336"
    label = f"WCAG {wcag_level.upper()}"
    status = "PASS" if error_count == 0 else f"{error_count} ERRORS"
    logo_html = ""
    if logo_info and "img" in logo_info and "alt" in logo_info:
        logo_html = f'<img src="{logo_info["img"]}" alt="{logo_info["alt"]}" style="height:1.5em;vertical-align:middle;margin-right:0.5em;">'
    return f'<span style="background:{color};color:#fff;padding:2px 6px;border-radius:4px;font-size:90%">{logo_html}{label}: {status}</span>'

def get_pages_to_check(conn) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT id, output_path FROM content WHERE output_path LIKE '%.html'")
    return [{"id": row[0], "output_path": row[1]} for row in cursor.fetchall()]

def get_wcag_level_from_config(config_filename):
    mapping = {
        "pa11y.config.json": "AA",
        #"wcag.aa.json": "AA",
        #"basic.json": "A",
        #"wcag.aaa.json": "AAA",
        # Add more mappings as needed
    }
    return mapping.get(config_filename.lower(), "AA")  # Default to AA

def read_config_order_from_yaml(yaml_path: str) -> List[str]:
    """
    Stub: Read config order from a YAML file.
    Not yet implemented.
    """
    # TODO: Implement reading config order from YAML
    return []


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
    
def get_wcag_logo_info(level, logos_path=None):
    if logos_path is None:
        # Always resolve from project root
        logos_path = os.path.join(project_root, "pa11y-configs", "wcag_logos.json")
    try:
        with open(logos_path, "r") as f:
            logos = json.load(f)
        return logos.get(level)
    except Exception as e:
        logging.error(f"Could not load WCAG logo info: {e}")
        return None
    
def inject_badges_into_html(conn, badge_field="badge_html", marker="<!-- BADGE_INJECT -->"):
    """
    For each page in the DB, inject the badge_html into the HTML file.
    If marker is found, insert there; otherwise, insert before </body>.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.output_path, ar.badge_html
        FROM accessibility_results ar
        JOIN content c ON ar.content_id = c.id
        WHERE ar.badge_html IS NOT NULL AND ar.badge_html != ''
    """)
    rows = cursor.fetchall()
    for output_path, badge_html in rows:
        if not output_path or not os.path.exists(output_path):
            continue
        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()
        # Replace the missing badge message if present
        missing_div = '<div class="accessibility-badge-missing" role="status" style="color:#888;font-size:90%">\n        No accessibility verification results yet.\n      </div>'
        if missing_div in html:
            html = html.replace(missing_div, f'<div class="accessibility-badge">{badge_html}</div>')
        elif marker in html:
            html = html.replace(marker, badge_html + marker)
        elif "</body>" in html:
            html = html.replace("</body>", badge_html + "\n</body>")
        else:
            html += "\n" + badge_html
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    return True
    
def main():
    config_path = "pa11y-configs/pa11y.config.json"  # Set your config file here
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, "db", "sqlite.db")
    conn = sqlite3.connect(db_path)
    ensure_accessibility_results_table(conn)
    wcag_level = get_wcag_level_from_config(os.path.basename(config_path))
    logo_info = get_wcag_logo_info(wcag_level)
    pages = get_pages_to_check(conn)
    for page in pages:
        html_path = page["output_path"]
        if not os.path.exists(html_path):
            continue
        result = run_pa11y_on_file(html_path, config_path)
        error_count = 0
        warning_count = 0
        notice_count = 0
        if isinstance(result, list):
            for issue in result:
                t = issue.get("type")
                if t == "error":
                    error_count += 1
                elif t == "warning":
                    warning_count += 1
                elif t == "notice":
                    notice_count += 1
        badge_html = generate_badge_html(wcag_level, error_count, logo_info)
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
    conn.close()

if __name__ == "__main__":
    main()
    
    
    
    