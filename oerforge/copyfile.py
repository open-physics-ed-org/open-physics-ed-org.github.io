"""
Module to copy project content and static assets into build directories for deployment.

Features:
- Copies all contents of 'content/' to 'build/files/'
- Copies 'static/css/' to 'build/css/' and 'static/js/' to 'build/js/'
- Creates target directories if they do not exist
- Overwrites files each time it is called
- Creates 'build/.nojekyll' to prevent GitHub Pages from running Jekyll

Usage:
    from oerforge.copyfile import copy_project_files
    copy_project_files()
"""

import os
import shutil
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build')
CONTENT_SRC = os.path.join(PROJECT_ROOT, 'content')
CONTENT_DST = os.path.join(BUILD_DIR, 'files')
CSS_SRC = os.path.join(PROJECT_ROOT, 'static', 'css')
CSS_DST = os.path.join(BUILD_DIR, 'css')
JS_SRC = os.path.join(PROJECT_ROOT, 'static', 'js')
JS_DST = os.path.join(BUILD_DIR, 'js')
NOJEKYLL_PATH = os.path.join(BUILD_DIR, '.nojekyll')
LOG_PATH = os.path.join(PROJECT_ROOT, 'log/build.log')


def copytree_overwrite(src, dst):
    """
    Recursively copy src directory to dst, overwriting existing files.
    """
    logging.debug(f"Copying from {src} to {dst}")
    if os.path.exists(dst):
        logging.debug(f"Removing existing directory: {dst}")
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    logging.info(f"Copied {src} to {dst}")


def ensure_dir(path):
    """
    Ensure that a directory exists.
    """
    if not os.path.exists(path):
        logging.debug(f"Creating directory: {path}")
    os.makedirs(path, exist_ok=True)


def create_nojekyll(path):
    """
    Create an empty .nojekyll file at the given path.
    """
    with open(path, 'w') as f:
        f.write('')
    logging.info(f"Created .nojekyll at {path}")


def copy_project_files(debug: bool = False):
    """
    Copy project content and static assets to build directories.
    If debug is True, log detailed actions to projectroot/loh.
    """
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(message)s',
        filename=LOG_PATH,
        filemode='a'
    )
    logging.info("Starting copy_project_files")
    # Remove build directory if it exists (destructive)
    if os.path.exists(BUILD_DIR):
        logging.debug(f"Removing entire build directory: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)
    ensure_dir(BUILD_DIR)
    copytree_overwrite(CONTENT_SRC, CONTENT_DST)
    copytree_overwrite(CSS_SRC, CSS_DST)
    copytree_overwrite(JS_SRC, JS_DST)
    create_nojekyll(NOJEKYLL_PATH)
    logging.info("Finished copy_project_files")
