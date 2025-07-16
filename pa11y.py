from oerforge.verify import process_all_html_files

if __name__ == "__main__":
    config_file = "pa11y-config/pa11y.wcag.aaa.json"
    db_path = "db/sqlite.db"
    process_all_html_files(build_dir="build", config_file=config_file, db_path=db_path)