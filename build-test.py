import os
from oerforge.db_utils import initialize_database
from oerforge.copyfile import copy_project_files
from oerforge.scan import scan_toc_and_populate_db, get_descendants_for_parent

from oerforge.convert import batch_convert_all_content
from oerforge.make import build_all_markdown_files, setup_logging, find_markdown_files

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_FILES_DIR = os.path.join(PROJECT_ROOT, 'build', 'files')
BUILD_HTML_DIR = os.path.join(PROJECT_ROOT, 'build')

def log_directory_contents(directory: str) -> None:
    """Logs all files in the specified directory for debugging purposes."""
    print(f"[DEBUG] Contents of {directory}:")
    for root, _, files in os.walk(directory):
        for name in files:
            print(f"  {os.path.join(root, name)}")

def log_markdown_files(directory: str) -> None:
    """Logs all markdown files found in the specified directory."""
    md_files = find_markdown_files(directory)
    print(f"[DEBUG] Markdown files found ({len(md_files)}):")
    for f in md_files:
        print(f"  {f}")

def run_full_workflow() -> None:
    """Runs the complete OERForge build workflow."""
    setup_logging()
    print("Step 1: Initializing database...")
    initialize_database()

    print("Step 2: Copying project files and static assets...")
    copy_project_files()
    log_directory_contents(BUILD_FILES_DIR)

    print("Step 3: Scanning TOC and populating database...")
    scan_toc_and_populate_db('_config.yml')

    print("Step 4: Batch converting all content...")
    batch_convert_all_content()

    print("Step 5: Building HTML and section indexes...")
    log_markdown_files(BUILD_FILES_DIR)
    build_all_markdown_files(BUILD_FILES_DIR, BUILD_HTML_DIR)

    print("Workflow complete. Please check the build/, docs/, and logs directories for results.")

if __name__ == "__main__":
    run_full_workflow()