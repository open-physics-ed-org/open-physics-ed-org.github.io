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
    
def convert_md_to_docx(content_record, conn):
    """
    Convert a Markdown file to DOCX using Pandoc.
    Copy converted file to build/files. Update DB conversion status.
    """
    src_path = content_record['source_path']
    print(f"[DEBUG] Starting Markdown to DOCX conversion for: {src_path}")
    # Determine output path: change extension to .docx, mirror TOC hierarchy
    rel_path = os.path.relpath(src_path, CONTENT_ROOT)
    out_path = os.path.join(BUILD_ROOT, os.path.splitext(rel_path)[0] + '.docx')
    print(f"[DEBUG] Output DOCX path: {out_path}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    abs_src_path = os.path.join(CONTENT_ROOT, rel_path)
    # Copy original .md to build/files if not already there
    build_md_path = os.path.join(BUILD_ROOT, rel_path)
    print(f"[DEBUG] Build Markdown path: {build_md_path}")
    if not os.path.exists(build_md_path):
        try:
            shutil.copy2(abs_src_path, build_md_path)
            print(f"[DEBUG] Copied original md to {build_md_path}")
            log_event(f"Copied original md to {build_md_path}", level="INFO")
        except Exception as e:
            print(f"[ERROR] Failed to copy md: {e}")
            log_event(f"Failed to copy md: {e}", level="ERROR")
            return
    # Run Pandoc to convert md to docx
    try:
        print(f"[DEBUG] Running Pandoc: pandoc {build_md_path} -o {out_path}")
        subprocess.run([
            "pandoc",
            build_md_path,
            "-o",
            out_path
        ], check=True)
        print(f"[DEBUG] Converted {build_md_path} to DOCX at {out_path}")
        log_event(f"Converted {build_md_path} to DOCX at {out_path}", level="INFO")
        # Update DB: set converted_docx = 1 for this record
        cursor = conn.cursor()
        cursor.execute("UPDATE content SET converted_docx=1 WHERE id=?", (content_record['id'],))
        conn.commit()
        print(f"[DEBUG] DB updated: converted_docx=1 for id {content_record['id']}")
        log_event(f"DB updated: converted_docx=1 for id {content_record['id']}", level="INFO")
    except Exception as e:
        print(f"[ERROR] Pandoc conversion failed: {e}")
        log_event(f"Pandoc conversion failed: {e}", level="ERROR")

def convert_md_to_pdf(content_record, conn):
    """
    Convert a Markdown file to PDF using Pandoc.
    Copy converted file to build/files. Update DB conversion status.
    """
    log_event(f"[STUB] Converting md to pdf for {content_record['source_path']}", level="DEBUG")
    pass

def convert_md_to_tex(content_record, conn):
    """
    Convert a Markdown file to LaTeX using Pandoc.
    Copy converted file to build/files. Update DB conversion status.
    """
    log_event(f"[STUB] Converting md to tex for {content_record['source_path']}", level="DEBUG")
    pass

# --- Batch Conversion Orchestrator ---
def batch_convert_all_content():
    """
    Main entry point: batch process all files in the content table.
    For each file, check conversion flags and call appropriate conversion stubs.
    Copy original files to build/files. Organize output to mirror TOC hierarchy.
    Log all errors and warnings to log/convert.log.
    """
    print("[DEBUG] Starting batch conversion for all content records.")
    log_event("Starting batch conversion for all content records.", level="INFO")
    import yaml
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "_config.yml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    toc = config.get('toc', [])

    def walk_toc_all_files(items, parent_path=""):
        file_entries = []
        for item in items:
            file_path = item.get('file')
            if file_path:
                out_path = os.path.join(BUILD_FILES_ROOT, file_path)
                src_path = os.path.join(CONTENT_ROOT, file_path)
                file_entries.append((src_path, out_path))
            children = item.get('children', [])
            if children:
                file_entries.extend(walk_toc_all_files(children, parent_path))
        return file_entries

    all_files = walk_toc_all_files(toc)
    try:
        conn = sqlite3.connect(DB_PATH)
        for src_path, out_path in all_files:
            print(f"[DEBUG] Copying {src_path} to {out_path}")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            if os.path.exists(src_path):
                shutil.copy2(src_path, out_path)
                log_event(f"Copied {src_path} to {out_path}", level="INFO")
                # Query and copy all referenced images for this file
                content_record = {'source_path': src_path}
                images = query_images_for_content(content_record, conn)
                copy_images_to_build(images, images_root=BUILD_IMAGES_ROOT, conn=conn)
                # If the file is markdown, update image links in the copied file
                if out_path.endswith('.md'):
                    update_markdown_image_links(out_path, images, images_root=BUILD_IMAGES_ROOT)
            else:
                log_event(f"[ERROR] Missing file: {src_path}", level="ERROR")
        conn.close()
    except Exception as e:
        log_event(f"Batch conversion failed: {e}", level="ERROR")

# --- Main Entry Point ---
if __name__ == "__main__":
    log_event("[convert] __main__ entry: running batch_convert_all_content()", level="INFO")
    batch_convert_all_content()

