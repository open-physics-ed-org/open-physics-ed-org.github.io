from oerforge.verify import run_pa11y_on_file, get_content_id_for_file, store_accessibility_result, generate_wcag_report, inject_badge_into_html
import sqlite3
import os

def process_all_html_files(build_dir="build", config_file=None, db_path="db/sqlite.db"):
    import fnmatch
    asset_dirs = {"css", "js", "images", "files"}
    for root, dirs, files in os.walk(build_dir):
        dirs[:] = [d for d in dirs if d not in asset_dirs]
        for filename in files:
            if fnmatch.fnmatch(filename, "*.html") and not filename.startswith("wcag_report_"):
                html_path = os.path.join(root, filename)
                print(f"Processing: {html_path}")
                result = run_pa11y_on_file(html_path, config_file)
                conn = sqlite3.connect(db_path)
                content_id = get_content_id_for_file(html_path, conn)
                badge_html = "<span>Badge</span>"
                wcag_level = "AAA"
                error_count = sum(1 for i in result if i.get("type") == "error") if result else 0
                warning_count = sum(1 for i in result if i.get("type") == "warning") if result else 0
                notice_count = sum(1 for i in result if i.get("type") == "notice") if result else 0
                if content_id is not None:
                    store_accessibility_result(content_id, result, badge_html, wcag_level, error_count, warning_count, notice_count, conn)
                    config = {
                        'title': os.path.splitext(filename)[0].capitalize(),
                        'wcag_level': wcag_level
                    }
                    issues = result if result is not None else []
                    report_path = generate_wcag_report(html_path, issues, badge_html, config)
                    report_link = os.path.basename(report_path)
                    inject_badge_into_html(html_path, badge_html, report_link)
                conn.close()

if __name__ == "__main__":
    config_file = "pa11y-config/pa11y.wcag.aaa.json"
    db_path = "db/sqlite.db"
    process_all_html_files(build_dir="build", config_file=config_file, db_path=db_path)