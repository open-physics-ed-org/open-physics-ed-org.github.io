"""
build.py: Complete asset DB and admin export workflow.
"""

import os
import subprocess
from oerforge.scan import (
    initialize_database,
    scan_and_populate_files_db,
    print_table,
    populate_site_info_from_config
)
from oerforge_admin.export_db_html import (
    export_all_tables_to_html,
    copy_static_assets_to_admin
)
from oerforge_admin.view_db import insert_autobuilt_page

def main():
    # Set project root and key paths once
    project_root = os.path.dirname(os.path.abspath(__file__))
    content_dir = os.path.join(project_root, 'content')
    admin_output_dir = os.path.join(project_root, 'build', 'admin')
    build_dir = os.path.join(project_root, 'build')
    config_path = os.path.join(project_root, '_config.yml')
    view_db_path = os.path.join(project_root, 'oerforge_admin', 'view_db.py')

    print("[DB] Initializing asset database and schema...")
    initialize_database()
    populate_site_info_from_config(config_path)

    print(f"[DB] Scanning and populating files from: {content_dir}")
    scan_and_populate_files_db(content_dir)

    print("[DB] CLI output from view_db.py --all:")
    result = subprocess.run(['python3', view_db_path, '--all'], capture_output=True, text=True)
    print(result.stdout)

    print("[ADMIN] Exporting static HTML tables to build/admin ...")
    export_all_tables_to_html(admin_output_dir)
    copy_static_assets_to_admin(build_dir)
    print(f"[ADMIN] Static admin pages and assets exported to: {admin_output_dir}")

    print("[DB] Inserting admin page records into pages table...")
    for table in ['files_table.html', 'pages_files_table.html']:
        output_path = os.path.join(admin_output_dir, table)
        insert_autobuilt_page(output_path)
    print("[DB] Admin page records inserted into pages table.")

if __name__ == "__main__":
    main()