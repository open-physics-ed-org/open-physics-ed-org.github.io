from oerforge.verify import run_pa11y_on_file, get_content_id_for_file, store_accessibility_result, generate_wcag_report
import sqlite3

if __name__ == "__main__":
    html_file = "build/home/index.html"
    config_file = "pa11y-config/pa11y.wcag.aaa.json"
    db_path = "db/sqlite.db"
    
    # Run Pa11y
    result = run_pa11y_on_file(html_file, config_file)
    print("Pa11y result:", result)

    # Open DB connection
    conn = sqlite3.connect(db_path)
    content_id = get_content_id_for_file(html_file, conn)
    print("content_id:", content_id)

    # Example badge and counts (stub values for now)
    badge_html = "<span>Badge</span>"
    wcag_level = "AAA"
    error_count = sum(1 for i in result if i.get("type") == "error") if result else 0
    warning_count = sum(1 for i in result if i.get("type") == "warning") if result else 0
    notice_count = sum(1 for i in result if i.get("type") == "notice") if result else 0

    # Store result in DB
    if content_id is not None:
        store_accessibility_result(content_id, result, badge_html, wcag_level, error_count, warning_count, notice_count, conn)
        print("Result stored in DB.")
        # Generate report
        config = {
            'title': 'Home',
            'favicon': '/images/favion.ico',
            'css_path': '/css/theme-light.css',
            'js_path': '/js/main.js',
            'wcag_level': wcag_level
        }
        issues = result if result is not None else []
        report_path = generate_wcag_report(html_file, issues, badge_html, config)
        print(f"Report generated: {report_path}")
    else:
        print("No content_id found for file.")
    conn.close()