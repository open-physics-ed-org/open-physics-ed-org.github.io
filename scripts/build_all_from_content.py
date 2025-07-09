#!/usr/bin/env python3
"""
Process all files referenced in _content.yml and build them into HTML in docs/ using site meta, menu, and footer.
Usage: ./scripts/build_all_from_content.py [--debug]
"""
import sys
from pathlib import Path
import yaml
import argparse
import subprocess

CONTENT_YML = Path('_content.yml')
SCRIPT = 'scripts/build_with_content.py'


def load_content_yml():
    if not CONTENT_YML.exists():
        raise FileNotFoundError(f"_content.yml not found")
    with open(CONTENT_YML) as f:
        return yaml.safe_load(f)

def collect_files_from_content(content):
    files = set()
    for section in content:
        # Main page for section
        main_page = section.get('main_page')
        if main_page:
            files.add(Path('content') / main_page)
        # Articles in folder
        articles = section.get('articles')
        if articles and articles.get('folder'):
            folder = Path('content') / articles['folder']
            if folder.exists():
                for f in folder.glob('*.md'):
                    files.add(f)
    return sorted(files)

def build_file(mdfile, debug=False):
    cmd = [sys.executable, SCRIPT, str(mdfile)]
    if debug:
        cmd.append('--debug')
    print(f"[INFO] Building {mdfile} ...")
    result = subprocess.run(cmd, capture_output=not debug, text=True)
    if debug:
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    elif result.returncode == 0:
        print(f"[OK] {mdfile} built.")
    else:
        print(f"[ERROR] Failed to build {mdfile}: {result.stderr}")

def main():
    parser = argparse.ArgumentParser(description="Build all files referenced in _content.yml into HTML in docs/.")
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    site_content = load_content_yml()
    content = site_content.get('content', [])
    files = collect_files_from_content(content)
    if not files:
        print("No files found to build.")
        sys.exit(0)
    print(f"[INFO] Found {len(files)} files to build.")
    for f in files:
        build_file(f, debug=args.debug)

if __name__ == '__main__':
    main()
