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

def store_accessibility_result(content_id: int, pa11y_json: Dict[str, Any], badge_html: str, wcag_level: str, error_count: int, warning_count: int, notice_count: int, conn=None):
    """
    Store the latest accessibility result for a page in the database.
    """
    # TODO: Implement DB insert/update
    pass

def generate_badge_html(wcag_level: str, error_count: int) -> str:
    """
    Generate badge HTML for a given WCAG level and error count.
    """
    # TODO: Implement badge generation
    pass

def get_pages_to_check(conn) -> List[Dict[str, Any]]:
    """
    Return a list of pages (from content table) to check for accessibility.
    """
    # TODO: Query DB for all pages
    pass

def generate_compliance_table_page(conn, output_path: str):
    """
    Generate a static HTML page summarizing accessibility compliance for all pages.
    """
    # TODO: Implement compliance table generation
    pass

def main():
    """
    CLI entry point. Parse args, run checks, store results, and generate reports as needed.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Accessibility verification with Pa11y")
    parser.add_argument("--config", "-c", type=str, help="Path to Pa11y config file (default: pa11y.config.json in project root if present)")
    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        default_config = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pa11y.config.json")
        if os.path.exists(default_config):
            config_path = default_config

    html_path = os.path.join("build", "index.html")
    if not os.path.exists(html_path):
        print(f"File not found: {html_path}")
        return
    result = run_pa11y_on_file(html_path, config_path)
    print("Raw Pa11y result:", result)
    if result is not None and result != []:
        # Print as pretty JSON if possible
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
