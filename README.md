# Open Physics Ed dot Org

A simple, accessible, and community-driven static site for open physics education resources, news, and community updates.

## Overview
- **Not a Hugo/Jekyll/SSG site**: This is a custom Python-based static site generator.
- **Content**: Markdown files in `content/` and `_content.yml` for structure and metadata.
- **Build**: Python scripts (`build.py`) process content and templates into static HTML in `docs/`.
- **Styling**: Custom CSS in `static/css/` (copied to `docs/css/`).
- **Logo**: Accessible logo in `static/images/logo.png` (copied to `docs/images/`).
- **Templates**: HTML templates in `layouts/`.
- **Menu & Footer**: Generated from `_content.yml`.

## Project Structure

```
_content.yml         # Site structure, menu, meta, logo, etc.
requirements.txt     # Python dependencies
build.py             # Main build script
content/             # Markdown content (pages, news, about, etc.)
docs/                # Output static site (HTML, CSS, images)
static/              # Static assets (css, images)
layouts/             # HTML templates
scripts/             # (Optional) Additional build scripts
.vscode/tasks.json   # VS Code build task (uses .venv)
.venv/               # Python virtual environment
```

## Build & Development
See `BUILD.MD` for build instructions and workflow.

---

- **Accessibility**: Color scheme, navigation, and logo are WCAG-compliant.
- **No server required**: Just open `docs/index.html` in your browser.
- **Contributions welcome!**
