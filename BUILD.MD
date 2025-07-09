# Build & Development Guide

## Prerequisites
- Python 3.8+
- Recommended: Use a virtual environment (`.venv`)

## Setup
1. Create and activate a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Build the Site
- **VS Code**: Use the build task (Cmd+Shift+B) — runs `.venv/bin/python3 build.py`.
- **Manual**: Run the build script directly:
   ```sh
   .venv/bin/python3 build.py
   ```
- Output is written to the `docs/` directory.

## Project Structure
- `content/` — Markdown source files for pages and news
- `_content.yml` — Site structure, menu, meta, logo, etc.
- `layouts/` — HTML templates (not Hugo, just basic HTML with placeholders)
- `static/` — Static assets (CSS, images)
- `docs/` — Output static site (HTML, CSS, images)
- `build.py` — Main build script (processes content, templates, menu, etc.)
- `.vscode/tasks.json` — VS Code build task (uses `.venv`)

## Notes
- **Not a Hugo site**: This is a custom Python static site generator.
- **Menu, logo, and footer** are injected from `_content.yml`.
- **Logo**: Accessible, WCAG-compliant, and included in every page header.
- **Color scheme**: Designed for accessibility and clarity.
- **No server required**: Open `docs/index.html` in your browser.

---

For more details, see `README.md`.
