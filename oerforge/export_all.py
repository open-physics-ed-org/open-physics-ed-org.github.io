"""
export_all.py

Batch export orchestrator for converting Markdown files to DOCX using Pandoc.
Logs all actions and errors to log/export.log.
"""

import os
import sys
import sqlite3
import shutil
import subprocess
import logging
import yaml

# --- Constants ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_ROOT = os.path.join(PROJECT_ROOT, "content")
BUILD_ROOT = os.path.join(PROJECT_ROOT, "build")
BUILD_FILES_ROOT = os.path.join(BUILD_ROOT, "files")
LOG_PATH = os.path.join(PROJECT_ROOT, "log", "export.log")
DB_PATH = os.path.join(PROJECT_ROOT, "db", "sqlite.db")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
)

# --- DOCX Conversion Function ---
def convert_md_to_docx(src_path, out_path, record_id=None, conn=None):
    """
    Convert a Markdown file to DOCX using Pandoc.
    Copy converted file to build/files. Update DB conversion status if record_id and conn provided.
    """
    logging.info(f"[DOCX] Starting conversion: {src_path} -> {out_path}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        subprocess.run(["pandoc", src_path, "-o", out_path], check=True)
        logging.info(f"[DOCX] Converted {src_path} to {out_path}")
        if record_id and conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE content SET converted_docx=1 WHERE id=?", (record_id,))
            conn.commit()
            logging.info(f"[DOCX] DB updated: converted_docx=1 for id {record_id}")
    except Exception as e:
        logging.error(f"[DOCX] Pandoc conversion failed for {src_path}: {e}")

# --- Batch Export Orchestrator ---
def export_all_docx(config_path=None):
    """
    Batch process all Markdown files in the TOC and convert to DOCX.
    """
    logging.info("[EXPORT] Starting batch DOCX export.")
    if config_path is None:
        config_path = os.path.join(PROJECT_ROOT, "_content.yml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    toc = config.get("toc", [])
    def walk_toc_md_files(items):
        md_entries = []
        for item in items:
            file_path = item.get("file")
            if file_path and file_path.endswith(".md"):
                src_path = os.path.join(CONTENT_ROOT, file_path)
                out_path = os.path.join(BUILD_ROOT, os.path.splitext(file_path)[0] + ".docx")
                md_entries.append((src_path, out_path, file_path))
            children = item.get("children", [])
            if children:
                md_entries.extend(walk_toc_md_files(children))
        return md_entries
    md_files = walk_toc_md_files(toc)
    conn = None
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
    for src_path, out_path, file_path in md_files:
        if os.path.exists(src_path):
            record_id = None
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM content WHERE source_path=?", (src_path,))
                row = cursor.fetchone()
                if row:
                    record_id = row[0]
            convert_md_to_docx(src_path, out_path, record_id, conn)
        else:
            logging.warning(f"[EXPORT] Missing Markdown file: {src_path}")
    if conn:
        conn.close()
    logging.info("[EXPORT] Batch DOCX export complete.")

if __name__ == "__main__":
    export_all_docx()
