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

# Set up logging for Pa11y debug
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "pa11y.log"),
    filemode="w",  # Overwrite log on each run
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

# --- Pa11y Integration Stubs ---
def run_pa11y_on_file(html_path: str, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
        # Try to parse stdout for accessibility issues
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
    # Remove any previous result for this content_id and wcag_level
    cursor.execute("""
        DELETE FROM accessibility_results WHERE content_id = ? AND wcag_html_level = ?
    """, (content_id, wcag_level))
    # Insert new result
    cursor.execute("""
        INSERT INTO accessibility_results (
            content_id, pa11y_json, badge_html, wcag_html_level, error_count, warning_count, notice_count, checked_at
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
    """
    Generate badge HTML for a given WCAG level and error count.
    """
    # Simple badge HTML placeholder
    color = "#4caf50" if error_count == 0 else "#f44336"
    label = f"WCAG {wcag_level.upper()}"
    status = "PASS" if error_count == 0 else f"{error_count} ERRORS"
    return f'<span style="background:{color};color:#fff;padding:2px 6px;border-radius:4px;font-size:90%">{label}: {status}</span>'

def get_pages_to_check(conn) -> List[Dict[str, Any]]:
    """
    Return a list of pages (from content table) to check for accessibility.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, output_path FROM content WHERE output_path LIKE '%.html'")
    return [{"id": row[0], "output_path": row[1]} for row in cursor.fetchall()]

def generate_compliance_table_page(conn, output_path: str):
    """
    Generate a static HTML page summarizing accessibility compliance for all pages.
    """
    # TODO: Implement compliance table generation
    pass

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
            wcag_html_level TEXT,
            error_count INTEGER,
            warning_count INTEGER,
            notice_count INTEGER,
            checked_at TEXT,
            FOREIGN KEY(content_id) REFERENCES content(id)
        )
    """)
    conn.commit()

def main():
    """
    CLI entry point. Parse args, run checks, store results, and generate reports as needed.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Accessibility verification with Pa11y")
    parser.add_argument("--config", "-c", type=str, help="Path to Pa11y config file (default: pa11y.config.json in project root if present)")
    parser.add_argument("--all", action="store_true", help="Check all HTML files in the database (batch mode)")
    parser.add_argument("--reset-results", action="store_true", help="Drop and recreate the accessibility_results table before running")
    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        default_config = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pa11y.config.json")
        if os.path.exists(default_config):
            config_path = default_config

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "sqlite.db")
    conn = sqlite3.connect(db_path)
    ensure_accessibility_results_table(conn, drop_and_recreate=args.reset_results)

    if args.all:
        # Batch mode: check all HTML files in the database
        pages = get_pages_to_check(conn)
        print(f"Checking {len(pages)} HTML files from database...")
        for page in pages:
            html_path = page["output_path"]
            if not os.path.exists(html_path):
                print(f"File not found: {html_path}")
                logging.warning(f"File not found: {html_path}")
                continue
            print(f"\n=== Checking: {html_path} ===")
            result = run_pa11y_on_file(html_path, config_path)
            print("Raw Pa11y result:", result)
            # Count errors, warnings, notices
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
            wcag_level = "strict" if config_path and "strict" in os.path.basename(config_path).lower() else "basic"
            badge_html = generate_badge_html(wcag_level, error_count)
            # Store result in DB
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
