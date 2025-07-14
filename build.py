import os
import logging
from oerforge.logging_utils import setup_logging
from oerforge.db_utils import initialize_database
from oerforge.copyfile import copy_build_to_docs, copy_project_files
from oerforge.scan import scan_toc_and_populate_db

from oerforge.convert import batch_convert_all_content
from oerforge.make import build_all_markdown_files, setup_logging, find_markdown_files, create_section_index_html

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_FILES_DIR = os.path.join(PROJECT_ROOT, 'build', 'files')
BUILD_HTML_DIR = os.path.join(PROJECT_ROOT, 'build')

def log_directory_contents(directory: str) -> None:
    """Logs all files in the specified directory for debugging purposes."""
    logging.info(f"[DEBUG] Contents of {directory}:")
    for root, _, files in os.walk(directory):
        for name in files:
            logging.info(f"  {os.path.join(root, name)}")

def log_markdown_files(directory: str) -> None:
    """Logs all markdown files found in the specified directory."""
    md_files = find_markdown_files(directory)
    logging.info(f"[DEBUG] Markdown files found ({len(md_files)}):")
    for f in md_files:
        logging.info(f"  {f}")

def run_full_workflow() -> None:
    """Runs the complete OERForge build workflow."""
    setup_logging()
    logging.info("Step 1: Initializing database...")
    initialize_database()

    logging.info("Step 2: Copying project files and static assets...")
    copy_project_files()
    log_directory_contents(BUILD_FILES_DIR)

    logging.info("Step 3: Scanning TOC and populating database...")
    scan_toc_and_populate_db('_config.yml')

    logging.info("Step 4: Batch converting all content...")
    batch_convert_all_content()

    logging.info("Step 5: Building HTML and section indexes...")
    log_markdown_files(BUILD_FILES_DIR)
    build_all_markdown_files(BUILD_FILES_DIR, BUILD_HTML_DIR)
    
    # Autogenerate index.html for top-level sections from the database
    def get_top_level_sections(db_path=None):
        import sqlite3
        if db_path is None:
            db_path = os.path.join(PROJECT_ROOT, 'open-physics-ed-org.github.io', 'db', 'sqlite.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            query = "SELECT title, output_path FROM content WHERE is_autobuilt=1 AND output_path LIKE '%/index.html'"
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            result = [(row[0], os.path.dirname(row[1])) for row in rows]
            logging.info(f"get_top_level_sections result: {result}")
            return result
        except Exception as e:
            logging.error(f"[ERROR] get_top_level_sections failed: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return []

    for section_title, output_dir in get_top_level_sections():
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        logging.info(f"[AUTO] Generating section index for: {section_title} at {output_dir}")
        create_section_index_html(section_title, output_dir)

    # Final copy: ensure build/ is copied to docs/ after all build steps
    copy_build_to_docs()

    logging.info("Workflow complete. Please check the build/, docs/, and logs directories for results.")

if __name__ == "__main__":
    run_full_workflow()