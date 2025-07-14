"""
scan.py: Asset database logic for pages and files only.
"""
import os
import sqlite3
import re

# ----
# Logging Helper for scan.py
# ----
def log_event(message, level="INFO"):
    """
    Logs an event to both stdout and scan.log in the project root.
    """
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{level}] {message}\n"
    print(log_line, end="")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(project_root, 'scan.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_line)
    except Exception as e:
        print(f"[ERROR] Could not write to scan.log: {e}")

def batch_read_files(file_paths):
    """
    Reads multiple files and returns their contents as a dict: {path: content}
    Supports markdown (.md), notebook (.ipynb), docx (.docx), and other file types.
    """
    contents = {}
    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == '.md':
                contents[path] = read_markdown_file(path)
            elif ext == '.ipynb':
                contents[path] = read_notebook_file(path)
            elif ext == '.docx':
                contents[path] = read_docx_file(path)
            else:
                contents[path] = None
        except Exception as e:
            log_event(f"Could not read {path}: {e}", level="ERROR")
            contents[path] = None
    return contents

def read_markdown_file(path):
    """
    Reads a markdown (.md) file and returns its content as a string.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        log_event(f"Could not read markdown file {path}: {e}", level="ERROR")
        return None

def read_notebook_file(path):
    """
    Reads a Jupyter notebook (.ipynb) file and returns its content as a dict.
    """
    import json
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_event(f"Could not read notebook file {path}: {e}", level="ERROR")
        return None

def read_docx_file(path):
    """
    Reads a docx file and returns its text content as a string.
    Requires python-docx to be installed.
    """
    try:
        from docx import Document
        doc = Document(path)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return '\n'.join(text)
    except ImportError:
        log_event("python-docx is not installed. Run 'pip install python-docx' in your environment.", level="ERROR")
        return None
    except Exception as e:
        log_event(f"Could not read docx file {path}: {e}", level="ERROR")
        return None

def batch_extract_assets(contents_dict, content_type, **kwargs):
    """
    Extracts assets from multiple file contents in one pass.
    contents_dict: {path: content}
    content_type: 'markdown', 'notebook', 'docx', etc.
    Returns a dict: {path: [asset_records]}
    """
    from oerforge.db_utils import insert_records, link_files_to_pages, get_db_connection
    assets = {}
    # Helper: MIME type mapping (media, document, and data types)
    mime_map = {
        # Images
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        # Video
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska',
        # Audio
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        # Documents
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        # Data files
        '.csv': 'text/csv',
        '.tsv': 'text/tab-separated-values',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.npy': 'application/octet-stream',
        '.txt': 'text/plain',
        '.zip': 'application/zip',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
        '.rst': 'text/x-rst',
        # Markdown/Notebook
        '.md': 'text/markdown',
        '.ipynb': 'application/x-ipynb+json',
    }
    # Insert each source file as a page if not present
    import threading
    import time
    conn = get_db_connection()
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Opened DB connection in batch_extract_assets at {time.time()}", level="DEBUG")
    cursor = conn.cursor()
    # Add mime_type column to content if not present
    cursor.execute("PRAGMA table_info(content)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'mime_type' not in columns:
        try:
            cursor.execute("ALTER TABLE content ADD COLUMN mime_type TEXT")
        except Exception:
            pass
    for source_path in contents_dict:
        ext = os.path.splitext(source_path)[1].lower()
        mime_type = mime_map.get(ext, '')
        cursor.execute("SELECT id FROM content WHERE source_path=?", (source_path,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO content (source_path, output_path, is_autobuilt, mime_type) VALUES (?, ?, ?, ?)", (source_path, None, 0, mime_type))
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Committing DB in batch_extract_assets at {time.time()}", level="DEBUG")
    try:
        conn.commit()
    except Exception as e:
        import traceback
        log_event(f"[ERROR][{os.getpid()}][{threading.get_ident()}] Commit failed in batch_extract_assets: {e}\n{traceback.format_exc()}", level="ERROR")
        raise
    # Extract assets for each file type
    for path, content in contents_dict.items():
        ext = os.path.splitext(path)[1].lower()
        if content_type == 'markdown':
            assets[path] = [a for a in extract_linked_files_from_markdown_content(content, page_id=None)
                            if mime_map.get(os.path.splitext(a.get('path',''))[1].lower())]
        elif content_type == 'notebook':
            if content and isinstance(content, dict) and 'cells' in content:
                cell_assets = []
                for cell in content['cells']:
                    cell_assets.extend([a for a in extract_linked_files_from_notebook_cell_content(cell, nb_path=path)
                                       if mime_map.get(os.path.splitext(a.get('path',''))[1].lower())])
                assets[path] = cell_assets
            else:
                assets[path] = []
        elif content_type == 'docx':
            assets[path] = [a for a in extract_linked_files_from_docx_content(path, page_id=None)
                            if mime_map.get(os.path.splitext(a.get('path',''))[1].lower())] if content else []
        else:
            assets[path] = []
    # Insert asset records into files table
    file_records = []
    file_page_links = []
    for source_path, asset_list in assets.items():
        for asset in asset_list:
            asset_path = asset.get('path', '')
            asset_ext = os.path.splitext(asset_path)[1].lower()
            mime_type = mime_map.get(asset_ext, '')
            file_record = {
                'filename': os.path.basename(asset_path),
                'extension': asset_ext,
                'mime_type': mime_type,
                'is_image': int(asset_ext in ['.png','.jpg','.jpeg','.gif','.svg']),
                'is_remote': int(asset_path.startswith('http')),
                'url': asset_path,
                'referenced_page': source_path,
                'relative_path': asset_path,
                'absolute_path': None,
                'cell_type': asset.get('type', None),
                'is_code_generated': None,
                'is_embedded': None
            }
            file_records.append(file_record)
    file_ids = insert_records('files', file_records, conn=conn, cursor=cursor)
    # Link files to pages
    idx = 0
    for source_path, asset_list in assets.items():
        for _ in asset_list:
            file_page_links.append((file_ids[idx], source_path))
            idx += 1
    if file_page_links:
        link_files_to_pages(file_page_links, conn=conn, cursor=cursor)
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Closing DB connection in batch_extract_assets at {time.time()}", level="DEBUG")
    conn.close()
    return assets

def extract_linked_files_from_markdown_content(md_text, page_id=None):
    """
    Extracts asset links from markdown text.
    Returns a list of file records.
    """
    import re
    asset_pattern = re.compile(r'!\[[^\]]*\]\(([^)]+)\)|\[[^\]]*\]\(([^)]+)\)')
    assets = []
    for match in asset_pattern.finditer(md_text):
        asset_path = match.group(1) or match.group(2)
        if asset_path:
            assets.append({
                'type': 'asset',
                'path': asset_path,
                'page_id': page_id
            })
    return assets

def extract_linked_files_from_notebook_cell_content(cell, nb_path=None):
    """
    Extracts asset links from a notebook cell.
    Returns a list of file records.
    """
    assets = []
    # Extract markdown-linked images
    if cell.get('cell_type') == 'markdown':
        source = cell.get('source', [])
        if isinstance(source, list):
            text = ''.join(source)
        else:
            text = str(source)
        assets.extend(extract_linked_files_from_markdown_content(text, page_id=None))
        for asset in assets:
            asset['notebook'] = nb_path
    # Extract embedded/code-produced images from outputs
    if cell.get('cell_type') == 'code' and 'outputs' in cell:
        for idx, output in enumerate(cell['outputs']):
            # Typical image output: {'data': {'image/png': ...}, ...}
            if 'data' in output:
                for img_type in ['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml']:
                    if img_type in output['data']:
                        ext = {
                            'image/png': '.png',
                            'image/jpeg': '.jpg',
                            'image/gif': '.gif',
                            'image/svg+xml': '.svg',
                        }[img_type]
                        nb_name = os.path.basename(nb_path) if nb_path else 'notebook'
                        rel_path = f'notebook_embedded/{nb_name}/cell{idx}{ext}'
                        assets.append({
                            'type': 'asset',
                            'path': rel_path,
                            'notebook': nb_path,
                            'filename': f'cell{idx}{ext}',
                            'extension': ext,
                            'is_embedded': True,
                            'is_code_generated': True
                        })
    return assets

def extract_linked_files_from_docx_content(docx_path, page_id=None):
    """
    Extracts asset links from a docx file.
    Returns a list of file records.
    """
    assets = []
    try:
        from docx import Document
        doc = Document(docx_path)
        import re
        asset_pattern = re.compile(r'(https?://[^\s]+|assets/[^\s]+|images/[^\s]+)')
        # Extract text-based links as before
        for para in doc.paragraphs:
            matches = asset_pattern.findall(para.text)
            for asset_path in matches:
                assets.append({
                    'type': 'asset',
                    'path': asset_path,
                    'page_id': page_id
                })
        # Extract embedded images
        for rel in doc.part.rels.values():
            if rel.reltype == 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image':
                img_part = rel.target_part
                img_name = os.path.basename(img_part.partname)
                img_ext = os.path.splitext(img_name)[1].lower()
                # Use a relative path for DB, e.g. 'docx_embedded/<docx_filename>/<img_name>'
                rel_path = f'docx_embedded/{os.path.basename(docx_path)}/{img_name}'
                assets.append({
                    'type': 'asset',
                    'path': rel_path,
                    'page_id': page_id,
                    'filename': img_name,
                    'extension': img_ext,
                    'is_embedded': True
                })
    except Exception as e:
        log_event(f"Could not extract assets from docx {docx_path}: {e}", level="ERROR")
    return assets

def populate_site_info_from_config(config_path):
    """
    Reads _config.yml and populates the site_info table with site and footer info.
    """
    import yaml
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, 'db', 'sqlite.db')
    full_config_path = os.path.join(project_root, config_path)
    with open(full_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    site = config.get('site', {})
    footer = config.get('footer', {})
    theme = site.get('theme', {})
    # Read header.html contents
    header_html_path = os.path.join(project_root, 'static', 'templates', 'header.html')
    try:
        with open(header_html_path, 'r', encoding='utf-8') as hf:
            header_html = hf.read()
    except Exception:
        header_html = ''
    log_event(f"[DEBUG] header_html read from file (first 500 chars): {repr(header_html)[:500]}", level="DEBUG")
    import threading
    import time
    conn = sqlite3.connect(db_path)
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Opened DB connection in populate_site_info_from_config at {time.time()}", level="DEBUG")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM site_info")
    cursor.execute(
        """
        INSERT INTO site_info (title, author, description, logo, favicon, theme_default, theme_light, theme_dark, language, github_url, footer_text, header)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            site.get('title', ''),
            site.get('author', ''),
            site.get('description', ''),
            site.get('logo', ''),
            site.get('favicon', ''),
            theme.get('default', ''),
            theme.get('light', ''),
            theme.get('dark', ''),
            site.get('language', ''),
            site.get('github_url', ''),
            footer.get('text', ''),
            header_html
        )
    )
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Committing DB in populate_site_info_from_config at {time.time()}", level="DEBUG")
    try:
        conn.commit()
    except Exception as e:
        import traceback
        log_event(f"[ERROR][{os.getpid()}][{threading.get_ident()}] Commit failed in populate_site_info_from_config: {e}\n{traceback.format_exc()}", level="ERROR")
        raise
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Closing DB connection in populate_site_info_from_config at {time.time()}", level="DEBUG")
    conn.close()

# ----
# Conversion Capability Helper
# ----

def get_possible_conversions(extension):
    """
    Returns a dict of possible conversions for a given file extension.
    Keys are can_convert_md, can_convert_tex, can_convert_pdf, can_convert_docx, can_convert_ppt, can_convert_jupyter, can_convert_ipynb.
    Values are booleans (True/False) indicating if conversion is possible.
    """
    ext = extension.lower()
    # Default all to False
    flags = {
        'can_convert_md': False,
        'can_convert_tex': False,
        'can_convert_pdf': False,
        'can_convert_docx': False,
        'can_convert_ppt': False,
        'can_convert_jupyter': False,
        'can_convert_ipynb': False
    }
    if ext == '.ipynb':
        flags['can_convert_md'] = True
        flags['can_convert_docx'] = True
        flags['can_convert_tex'] = True
        flags['can_convert_jupyter'] = True
        flags['can_convert_pdf'] = True
    elif ext == '.md':
        flags['can_convert_docx'] = True
        flags['can_convert_pdf'] = True
        flags['can_convert_tex'] = True
        flags['can_convert_jupyter'] = True
    elif ext == '.docx':
        flags['can_convert_md'] = True
        flags['can_convert_tex'] = True
        flags['can_convert_pdf'] = True
        flags['can_convert_docx'] = True
        flags['can_convert_jupyter'] = True
    return flags

def scan_toc_and_populate_db(config_path):
    """
    Walks the toc: from _config.yml, reads each file, extracts assets/images, and populates the DB with both content and asset records, maintaining TOC hierarchy.
    """
    import yaml
    from oerforge.db_utils import get_db_connection, insert_records, link_files_to_pages
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_config_path = os.path.join(project_root, config_path)
    with open(full_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    toc = config.get('toc', [])

    import threading
    import time
    conn = get_db_connection()
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Opened DB connection in scan_toc_and_populate_db at {time.time()}", level="DEBUG")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM content")
    seen_paths = set()
    file_paths = []
    # Removed outdated import of insert_file_records; link_files_to_pages is already imported above

    def walk_toc(items, parent_output_path=None, parent_slug=None):
        content_records = []
        for idx, item in enumerate(items):
            file_path = item.get('file')
            title = item.get('title', None)
            order = idx
            if file_path:
                source_path = file_path if file_path.startswith('content/') else f'content/{file_path}'
                ext = os.path.splitext(source_path)[1].lower()
                rel_path = source_path[8:] if source_path.startswith('content/') else source_path
                out_dir = os.path.dirname(rel_path)
                base_name = os.path.splitext(os.path.basename(rel_path))[0]
                output_path = os.path.join('build', out_dir, base_name + '.html') if out_dir else os.path.join('build', base_name + '.html')
                if source_path in seen_paths:
                    log_event(f"[WARN] TOC: Duplicate file path '{source_path}' in toc", level="WARN")
                    pass
                seen_paths.add(source_path)
                abs_path = os.path.join(project_root, source_path)
                if not os.path.exists(abs_path):
                    log_event(f"[ERROR] TOC: Missing file '{source_path}' (expected at {abs_path})", level="ERROR")
                    pass
                flags = get_possible_conversions(ext)
                slug = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_') if title else f'section_{idx}'
                content_record = {
                    'title': title,
                    'source_path': source_path,
                    'output_path': output_path,
                    'is_autobuilt': 0,
                    'mime_type': ext,
                    'can_convert_md': flags['can_convert_md'],
                    'can_convert_tex': flags['can_convert_tex'],
                    'can_convert_pdf': flags['can_convert_pdf'],
                    'can_convert_docx': flags['can_convert_docx'],
                    'can_convert_ppt': flags['can_convert_ppt'],
                    'can_convert_jupyter': flags['can_convert_jupyter'],
                    'can_convert_ipynb': flags['can_convert_ipynb'],
                    'parent_output_path': parent_output_path,
                    'slug': slug,
                    'order': order
                }
                content_records.append(content_record)
                file_paths.append(abs_path)
                children = item.get('children', [])
                if children:
                    child_records = walk_toc(children, parent_output_path=output_path, parent_slug=slug)
                    content_records.extend(child_records)
            elif item.get('children'):
                slug = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_') if title else f'section_{idx}'
                output_path = os.path.join('build', slug, 'index.html')
                content_record = {
                    'title': title,
                    'source_path': None,
                    'output_path': output_path,
                    'is_autobuilt': 1,
                    'mime_type': 'section',
                    'can_convert_md': False,
                    'can_convert_tex': False,
                    'can_convert_pdf': False,
                    'can_convert_docx': False,
                    'can_convert_ppt': False,
                    'can_convert_jupyter': False,
                    'can_convert_ipynb': False,
                    'parent_output_path': parent_output_path,
                    'slug': slug,
                    'order': order
                }
                content_records.append(content_record)
                children = item.get('children', [])
                if children:
                    child_records = walk_toc(children, parent_output_path=output_path, parent_slug=slug)
                    content_records.extend(child_records)
        return content_records

    # Usage in scan_toc_and_populate_db:
    all_content_records = walk_toc(toc)

    # Deduplicate by (source_path, output_path, title)
    unique_records = {}
    for rec in all_content_records:
        key = (rec.get('source_path'), rec.get('output_path'), rec.get('title'))
        if key not in unique_records:
            unique_records[key] = rec
    deduped_records = list(unique_records.values())

    # Ensure order is an integer
    for rec in deduped_records:
        try:
            rec['order'] = int(rec.get('order', 0))
        except Exception:
            rec['order'] = 0

    insert_records('content', deduped_records, db_path=os.path.join(project_root, 'db', 'sqlite.db'), conn=conn, cursor=cursor)
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Committing DB in scan_toc_and_populate_db at {time.time()}", level="DEBUG")
    try:
        conn.commit()
    except Exception as e:
        import traceback
        log_event(f"[ERROR][{os.getpid()}][{threading.get_ident()}] Commit failed in scan_toc_and_populate_db: {e}\n{traceback.format_exc()}", level="ERROR")
        raise

    # Read all files and extract assets
    rel_file_paths = [os.path.relpath(p, project_root) for p in file_paths if os.path.exists(p)]
    contents = batch_read_files(rel_file_paths)
    for path in rel_file_paths:
        ext = os.path.splitext(path)[1].lower()
        if ext == '.md':
            batch_extract_assets({path: contents[path]}, 'markdown', conn=conn, cursor=cursor)
        elif ext == '.ipynb':
            batch_extract_assets({path: contents[path]}, 'notebook', conn=conn, cursor=cursor)
        elif ext == '.docx':
            batch_extract_assets({path: contents[path]}, 'docx', conn=conn, cursor=cursor)
        # Add more types as needed
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Closing DB connection in scan_toc_and_populate_db at {time.time()}", level="DEBUG")
    conn.close()

# ----
# Recursive CTE Helper for Section Index Generation
# ----
def get_descendants_for_parent(parent_output_path, db_path):
    """
    Returns all children and grandchildren (and deeper) for a given parent_output_path,
    using a recursive CTE. Each result includes: id, title, output_path, parent_output_path, slug, level.
    """
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = '''
    WITH RECURSIVE content_hierarchy(id, title, output_path, parent_output_path, slug, level) AS (
      SELECT id, title, output_path, parent_output_path, slug, 0 as level
      FROM content
      WHERE output_path = ?
      UNION ALL
      SELECT c.id, c.title, c.output_path, c.parent_output_path, c.slug, ch.level + 1
      FROM content c
      JOIN content_hierarchy ch ON c.parent_output_path = ch.output_path
    )
    SELECT id, title, output_path, parent_output_path, slug, level FROM content_hierarchy WHERE level > 0 ORDER BY level, output_path;
    '''
    cursor.execute(query, (parent_output_path,))
    rows = cursor.fetchall()
    conn.close()
    # Return as list of dicts
    return [
        {
            'id': row[0],
            'title': row[1],
            'output_path': row[2],
            'parent_output_path': row[3],
            'slug': row[4],
            'level': row[5]
        }
        for row in rows
    ]