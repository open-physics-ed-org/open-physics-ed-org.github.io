import os
import sqlite3
from oerforge.verify import *

def main():
    config_path = "pa11y-configs/pa11y.config.json"
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
    inject_badges_into_html(conn)
    conn.close()

if __name__ == "__main__":
    main()