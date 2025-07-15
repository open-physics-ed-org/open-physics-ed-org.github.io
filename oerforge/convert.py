"""
convert.py

Module for converting Jupyter notebooks (.ipynb) and Markdown files to various formats,
managing associated images, and updating a SQLite database with conversion status.

Main features:
- Executes notebooks and exports to Markdown.
- Handles image extraction, copying, and reference updates.
- Logs conversion actions and updates database flags.
- Provides stub functions for other conversions (docx, tex, pdf).

Author: [Your Name]
"""


import logging
from oerforge.logging_utils import setup_logging
from oerforge.db_utils import log_event, get_records

import sys
import os
import shutil
import sqlite3
import subprocess
from nbconvert import MarkdownExporter
from nbconvert.preprocessors import ExecutePreprocessor, ExtractOutputPreprocessor
from traitlets.config import Config
import re
from markdown_it import MarkdownIt

# --- Constants ---
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "sqlite.db")
CONTENT_ROOT = "content"
BUILD_ROOT = "build"
BUILD_FILES_ROOT = os.path.join(BUILD_ROOT, "files")
BUILD_IMAGES_ROOT = os.path.join(BUILD_ROOT, "images")
IMAGES_ROOT = BUILD_IMAGES_ROOT  # For compatibility in image functions
LOG_DIR = "log"

# --- Modular Image Handling for Markdown ---
def query_images_for_content(content_record, conn):
    """
    Query sqlite.db for all images associated with this content file.
    Returns a list of image records (dicts).
    """
    from oerforge.db_utils import get_records
    images = get_records(
        "files",
        "is_image=1 AND referenced_page=?",
        (content_record['source_path'],),
        conn=conn
    )
    log_event(f"[IMAGES] Found {len(images)} images for {content_record['source_path']}", level="DEBUG")
    return images

def copy_images_to_build(images, images_root=IMAGES_ROOT, conn=None):
    """
    Copy each image to the top-level images directory. All images go in images/ with their filename only.
    Uses the content table to resolve the correct source path for each image.
    Returns a list of new build paths (absolute paths).
    """
    os.makedirs(images_root, exist_ok=True)
    copied = []
    # Build a lookup for content source paths
    content_lookup = {}
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute("SELECT source_path FROM content")
        for row in cursor.fetchall():
            content_lookup[row[0]] = row[0]
    for img in images:
        src = img.get('relative_path') or img.get('absolute_path')
        referenced_page = img.get('referenced_page')
        log_event(f"[IMAGES][DEBUG] src={src} img={img}", level="DEBUG")
        if not src or img.get('is_remote'):
            log_event(f"[IMAGES] Skipping remote or missing image: {img.get('filename')}", level="WARNING")
            continue
        # Compute the actual source path
        if referenced_page and referenced_page in content_lookup and not os.path.isabs(src):
            # If src is relative, resolve it against the referenced_page's directory
            src_path = os.path.normpath(os.path.join(os.path.dirname(referenced_page), src))
        else:
            src_path = src
        filename = os.path.basename(src)
        dest = os.path.join(images_root, filename)
        log_event(f"[IMAGES][DEBUG] Copying {src_path} to {dest}", level="DEBUG")
        try:
            shutil.copy2(src_path, dest)
            log_event(f"[IMAGES] Copied image {src_path} to {dest}", level="INFO")
            copied.append(dest)
        except Exception as e:
            log_event(f"[IMAGES] Failed to copy {src_path} to {dest}: {e}", level="ERROR")
    return copied

def update_markdown_image_links(md_path, images, images_root=IMAGES_ROOT):
    """
    Update image links in the Markdown file to point to the copied images in the top-level images directory.
    Uses sqlite.db to look up image records for this markdown file.
    """
    if not os.path.exists(md_path):
        log_event(f"[IMAGES] Markdown file not found: {md_path}", level="WARNING")
        return
    # Compute the source_path for this markdown file
    rel_path = os.path.relpath(md_path, BUILD_FILES_ROOT)
    source_path = os.path.join(CONTENT_ROOT, rel_path)
    # Query DB for images for this markdown file
    img_map = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT relative_path, absolute_path, filename FROM files WHERE is_image=1 AND referenced_page=?", (source_path,))
        for row in cursor.fetchall():
            rel, abs_path, filename = row
            src = rel or abs_path
            if not src:
                continue
            # Always use ../../images/<filename> for image references
            rel_img_path = os.path.join('..', '..', 'images', filename)
            img_map[os.path.basename(src)] = rel_img_path
        conn.close()
    except Exception as e:
        log_event(f"[IMAGES] DB lookup failed for {md_path}: {e}", level="ERROR")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    new_lines = lines.copy()
    # For each line, replace any image markdown src with correct relative path
    for idx, line in enumerate(lines):
        matches = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', line)
        for old_src in matches:
            filename = os.path.basename(old_src)
            if filename in img_map:
                new_src = img_map[filename]
                new_lines[idx] = new_lines[idx].replace(old_src, new_src)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    log_event(f"[IMAGES] Updated image links in {md_path} to use correct relative paths (DB-driven)", level="INFO")

def handle_images_for_markdown(content_record, conn):
    """
    Orchestrate image handling for a Markdown file: query, copy, update links.
    """
    images = query_images_for_content(content_record, conn)
    copied = copy_images_to_build(images, images_root=BUILD_IMAGES_ROOT)
    rel_path = os.path.relpath(content_record['source_path'], CONTENT_ROOT)
    md_path = os.path.join(BUILD_FILES_ROOT, rel_path)
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    # Copy original markdown to build/files if not already there
    abs_src_path = os.path.join(CONTENT_ROOT, rel_path)
    if not os.path.exists(md_path):
        try:
            shutil.copy2(abs_src_path, md_path)
            log_event(f"Copied original md to {md_path}", level="INFO")
        except Exception as e:
            log_event(f"Failed to copy md: {e}", level="ERROR")
            return
    update_markdown_image_links(md_path, images, images_root=BUILD_IMAGES_ROOT)
    log_event(f"[IMAGES] Finished handling images for {md_path}", level="INFO")
    
def convert_md_to_docx(src_path, out_path, record_id=None, conn=None):
    """
    Convert a Markdown file to DOCX using Pandoc.
    Copy converted file to build/files. Update DB conversion status if record_id and conn provided.
    """
    import logging
    logging.info(f"[DOCX] Starting conversion: {src_path} -> {out_path}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        import subprocess
        subprocess.run(["pandoc", src_path, "-o", out_path], check=True)
        logging.info(f"[DOCX] Converted {src_path} to {out_path}")
        if record_id:
            from oerforge.db_utils import get_db_connection, log_event
            import datetime
            try:
                db_conn = conn if conn is not None else get_db_connection()
                db_cursor = db_conn.cursor()
                # Insert conversion result into conversion_results table
                db_cursor.execute(
                    "INSERT INTO conversion_results (content_id, source_format, target_format, output_path, conversion_time, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        record_id,
                        '.md',
                        '.docx',
                        out_path,
                        datetime.datetime.now().isoformat(),
                        'success'
                    )
                )
                db_conn.commit()
                log_event(f"[DOCX] conversion_results updated for id {record_id}", level="INFO")
                if conn is None:
                    db_conn.close()
            except Exception as e:
                log_event(f"[DOCX] conversion_results insert failed for id {record_id}: {e}", level="ERROR")
    except Exception as e:
        logging.error(f"[DOCX] Pandoc conversion failed for {src_path}: {e}")

def convert_md_to_pdf(src_path, out_path, record_id=None, conn=None):
    """
    Convert a Markdown file to PDF using Pandoc. (Stub)
    """
    pass

def convert_md_to_tex(src_path, out_path, record_id=None, conn=None):
    """
    Convert a Markdown file to LaTeX using Pandoc. (Stub)
    """
    pass

# --- Batch Conversion Orchestrator ---
def batch_convert_all_content(config_path=None):
    """
    Main entry point: batch process all files in the content table.
    For each file, check conversion flags and call appropriate conversion stubs.
    Copy original files to build/files. Organize output to mirror TOC hierarchy.
    Log all errors and warnings to log/convert.log.
    config_path: Optional path to _config.yml. If None, uses default location.
    """
    print("[DEBUG] Starting batch conversion for all content records.")
    log_event("Starting batch conversion for all content records.", level="INFO")
    import yaml
    # Open build log for appending
    build_log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log', 'build.log')
    build_log = open(build_log_path, 'a', encoding='utf-8')
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if config_path is None:
        config_path = os.path.join(project_root, "_content.yml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    toc = config.get('toc', [])

    # --- Generic Conversion Logic ---
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Get all enabled conversions
    cursor.execute("SELECT source_format, target_format FROM conversion_capabilities WHERE is_enabled=1")
    conversions = cursor.fetchall()
    # Get all content files with output_path
    cursor.execute("SELECT id, source_path, output_path FROM content")
    content_files = cursor.fetchall()
    for record_id, source_path, output_path in content_files:
        if not source_path or not output_path:
            log_event(f"Skipping content record id={record_id} with None source_path or output_path", level="WARNING")
            build_log.write(f"SKIP: id={record_id} source_path={source_path} output_path={output_path}\n")
            continue
        src_ext = os.path.splitext(source_path)[1]
        rel_path = os.path.relpath(source_path, CONTENT_ROOT)
        src_path = os.path.join(CONTENT_ROOT, rel_path)
        out_dir = os.path.dirname(output_path)
        os.makedirs(out_dir, exist_ok=True)
        for conv_src, conv_target in conversions:
            if src_ext == conv_src:
                # Use output_path from DB, but adjust extension for conversion
                out_name = os.path.splitext(os.path.basename(output_path))[0] + conv_target
                out_path = os.path.join(out_dir, out_name)
                # Dispatch conversion
                if conv_src == ".md" and conv_target == ".md":
                    try:
                        shutil.copy2(src_path, out_path)
                        log_event(f"Copied .md to {out_path}", level="INFO")
                        build_log.write(f"COPY: {src_path} -> {out_path}\n")
                    except Exception as e:
                        log_event(f"Failed to copy .md: {e}", level="ERROR")
                        build_log.write(f"ERROR: Failed to copy {src_path} -> {out_path}: {e}\n")
                elif conv_src == ".md" and conv_target == ".docx":
                    convert_md_to_docx(src_path, out_path, record_id, conn)
                    build_log.write(f"CONVERT: {src_path} -> {out_path} (docx)\n")
                elif conv_src == ".ipynb" and conv_target == ".jupyter":
                    log_event(f"[JUPYTER] Would convert {src_path} to JupyterBook at {out_path}", level="INFO")
                    build_log.write(f"JUPYTER: {src_path} -> {out_path}\n")
                # Add more elifs for other conversions as needed
    conn.close()
    build_log.write("Batch conversion complete.\n")
    build_log.close()

# --- Main Entry Point ---
if __name__ == "__main__":
    setup_logging()
    log_event("[convert] __main__ entry: running batch_convert_all_content()", level="INFO")
    batch_convert_all_content()

