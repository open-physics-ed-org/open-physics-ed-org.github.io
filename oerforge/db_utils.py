# 
import sqlite3
import os

# ------------------------------------------------------------------------------
# Database Initialization and Utility Functions for OERForge Asset Tracking
# ------------------------------------------------------------------------------

def initialize_database():
    """
    Initializes the SQLite database for asset tracking in the OERForge project.

    This function creates the following tables:
        - files: Stores metadata about tracked files/assets.
        - pages_files: Maps files to pages where they are referenced.
        - pages: Tracks source and output paths for pages.
        - site_info: Stores site-wide metadata and configuration.

    Existing tables are dropped before creation to ensure a clean state.
    The database file is located at <project_root>/db/sqlite.db.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(project_root, 'db')
    db_path = os.path.join(db_dir, 'sqlite.db')
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS files")
    cursor.execute("DROP TABLE IF EXISTS pages_files")
    cursor.execute("DROP TABLE IF EXISTS content")
    cursor.execute("DROP TABLE IF EXISTS site_info")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            extension TEXT,
            mime_type TEXT,
            is_image BOOLEAN,
            is_remote BOOLEAN,
            url TEXT,
            referenced_page TEXT,
            relative_path TEXT,
            absolute_path TEXT,
            cell_type TEXT,
            is_code_generated BOOLEAN,
            is_embedded BOOLEAN
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            page_path TEXT,
            FOREIGN KEY(file_id) REFERENCES files(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            source_path TEXT,
            output_path TEXT,
            is_autobuilt BOOLEAN DEFAULT 0,
            mime_type TEXT,
            parent_output_path TEXT DEFAULT NULL,
            slug TEXT DEFAULT NULL,
            can_convert_md BOOLEAN DEFAULT NULL,
            can_convert_tex BOOLEAN DEFAULT NULL,
            can_convert_pdf BOOLEAN DEFAULT NULL,
            can_convert_docx BOOLEAN DEFAULT NULL,
            can_convert_ppt BOOLEAN DEFAULT NULL,
            can_convert_jupyter BOOLEAN DEFAULT NULL,
            can_convert_ipynb BOOLEAN DEFAULT NULL,
            converted_md BOOLEAN DEFAULT NULL,
            converted_pdf BOOLEAN DEFAULT NULL,
            converted_docx BOOLEAN DEFAULT NULL,
            converted_ppt BOOLEAN DEFAULT NULL,
            converted_jupyter BOOLEAN DEFAULT NULL,
            converted_ipynb BOOLEAN DEFAULT NULL,
            wcag_status_html TEXT DEFAULT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            description TEXT,
            logo TEXT,
            favicon TEXT,
            theme_default TEXT,
            theme_light TEXT,
            theme_dark TEXT,
            language TEXT,
            github_url TEXT,
            footer_text TEXT,
            header TEXT
        );
    """)

# General-purpose Query Function
# 
def get_records(table_name, where_clause=None, params=None, db_path=None, conn=None, cursor=None):
    """
    Fetch records from a table with optional WHERE clause and parameters.
    Args:
        table_name (str): Name of the table to query.
        where_clause (str, optional): SQL WHERE clause (without 'WHERE').
        params (tuple or list, optional): Parameters for the WHERE clause.
        db_path (str, optional): Path to the SQLite database file.
        conn, cursor: Optional existing connection/cursor.
    Returns:
        list of dict: List of records as dictionaries.
    """
    close_conn = False
    if conn is None or cursor is None:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        close_conn = True
    sql = f"SELECT * FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    if params is None:
        params = ()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    records = [dict(zip(col_names, row)) for row in rows]
    if close_conn:
        conn.close()
    return records

def log_event(message, level="INFO"):
    """
    Logs an event to both stdout and a log file in the project root.

    Args:
        message (str): The log message to record.
        level (str): The severity level (e.g., "INFO", "ERROR", "WARNING").

    The log file is named 'scan.log' and is located at <project_root>/scan.log.
    Each log entry is timestamped.
    """
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{level}] {message}\n"
    print(log_line, end="")
    # Write to db.log in project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(project_root, 'db.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_line)
    except Exception as e:
        print(f"[ERROR] Could not write to log file: {e}")

def get_db_connection(db_path=None):
    """
    Returns a sqlite3 connection to the database.

    Args:
        db_path (str, optional): Path to the SQLite database file.
            If None, defaults to <project_root>/db/sqlite.db.

        sqlite3.Connection: A connection object to the SQLite database.
    """
    if db_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'db', 'sqlite.db')
    return sqlite3.connect(db_path)

def insert_records(table_name, records, db_path=None, conn=None, cursor=None):
    """
    General-purpose batch insert for any table.
    Checks if table exists, inserts records, returns list of inserted row ids.
    Args:
        table_name (str): Name of the table to insert into.
        records (list of dict): Each dict contains column-value pairs.
        db_path (str, optional): Path to the SQLite database file.
        conn, cursor: Optional existing connection/cursor.
    Returns:
        list of int: List of inserted row ids.
    """
    import threading
    import time
    close_conn = False
    if conn is None or cursor is None:
        conn = get_db_connection(db_path)
        log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Opened DB connection in insert_records for table '{table_name}' at {time.time()}", level="DEBUG")
        cursor = conn.cursor()
        close_conn = True
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if cursor.fetchone() is None:
        log_event(f"[ERROR] Table '{table_name}' does not exist in the database.", level="ERROR")
        if close_conn:
            conn.close()
        return []
    row_ids = []
    for record in records:
        # Get columns for this table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall() if row[1] != 'id']
        # Build insert statement
        col_names = []
        values = []
        for col in columns:
            col_names.append(col)
            values.append(record.get(col, None))
        sql = f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({', '.join(['?' for _ in col_names])})"
        cursor.execute(sql, values)
        row_ids.append(cursor.lastrowid)
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Committing DB in insert_records for table '{table_name}' at {time.time()}", level="DEBUG")
    try:
        conn.commit()
    except Exception as e:
        import traceback
        log_event(f"[ERROR][{os.getpid()}][{threading.get_ident()}] Commit failed in insert_records: {e}\n{traceback.format_exc()}", level="ERROR")
        raise
    if close_conn:
        log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Closing DB connection in insert_records for table '{table_name}' at {time.time()}", level="DEBUG")
        conn.close()
    return row_ids

def link_files_to_pages(file_page_pairs, db_path=None, conn=None, cursor=None):
    import threading
    import time
    close_conn = False
    if conn is None or cursor is None:
        conn = get_db_connection(db_path)
        log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Opened DB connection in link_files_to_pages at {time.time()}", level="DEBUG")
        cursor = conn.cursor()
        close_conn = True
    for file_id, page_path in file_page_pairs:
        cursor.execute(
            """
            INSERT INTO pages_files (file_id, page_path)
            VALUES (?, ?)
            """,
            (file_id, page_path)
        )
    log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Committing DB in link_files_to_pages at {time.time()}", level="DEBUG")
    try:
        conn.commit()
    except Exception as e:
        import traceback
        log_event(f"[ERROR][{os.getpid()}][{threading.get_ident()}] Commit failed in link_files_to_pages: {e}\n{traceback.format_exc()}", level="ERROR")
        raise
    if close_conn:
        log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Closing DB connection in link_files_to_pages at {time.time()}", level="DEBUG")
        conn.close()


def pretty_print_table(table_name, db_path=None, conn=None, cursor=None):
    import threading
    import time
    close_conn = False
    if conn is None or cursor is None:
        # If db_path is None, default to project_root/db/sqlite.db
        if db_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'db', 'sqlite.db')
        conn = sqlite3.connect(db_path)
        log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Opened DB connection in pretty_print_table at {time.time()}", level="DEBUG")
        cursor = conn.cursor()
        close_conn = True
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]
    # Calculate column widths for pretty printing
    col_widths = [max(len(str(col)), max((len(str(row[i])) for row in rows), default=0)) for i, col in enumerate(col_names)]
    # Print header row
    header = " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(col_names))
    log_event(header, level="INFO")
    log_event("-" * len(header), level="INFO")
    # Print each row
    for row in rows:
        log_event(" | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))), level="INFO")
    if close_conn:
        log_event(f"[DEBUG][{os.getpid()}][{threading.get_ident()}] Closing DB connection in pretty_print_table at {time.time()}", level="DEBUG")
        conn.close()

