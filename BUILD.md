# Open Physics Ed Static Site Build System

This document describes the structure and usage of `build.py`, the static site generator for Open Physics Ed.

## Overview

- **Purpose:** Converts Markdown content and a YAML site structure into a modern, accessible static website in `docs/`.
- **Features:**
  - Uses Markdown files and a YAML site structure (`_content.yml`)
  - Outputs to a Hugo-style directory structure in `docs/`
  - Generates accessible, WCAG-compliant navigation and layout
  - Supports news article previews on the news index page
  - Handles relative CSS paths for all output locations
  - Copies CSS assets to the correct output locations

## How It Works

- **Content:**
  - Markdown files live in `content/` (e.g., `content/about.md`, `content/news/*.md`)
  - Site structure and menu are defined in `_content.yml`
- **Layouts:**
  - HTML templates in `layouts/` (e.g., `_default/baseof.html`, `news/single.html`)
- **CSS:**
  - Modern, accessible CSS in `static/css/theme-modern.css`
  - Copied to `docs/css/theme-modern.css` and `css/theme-modern.css` on build

## Key Functions in `build.py`

- `parse_front_matter(md_text)`: Parses YAML front matter from Markdown files.
- `render_markdown(md_text)`: Converts Markdown to HTML.
- `rel_link(from_path, to_url)`: Computes correct relative links for navigation and CSS.
- `build_menu(menu, current_output_path, debug=False)`: Generates the navigation menu HTML with correct links.
- `build_html(meta, content_html, layout_name, site, menu_html, footer_html)`: Assembles the final HTML for each page, injecting CSS, menu, and footer.
- `build_file(mdfile, site, menu, footer_html, debug=False)`: Main function to build a single page. Handles special logic for news index previews.
- `collect_files_from_content(content)`: Gathers all Markdown files to be built, based on `_content.yml`.

## Special Features

### News Index Previews
- When building `content/news/_index.md`, the script:
  - Collects all news articles in `content/news/` (excluding `_index.md`)
  - Parses their front matter for `title`, `date`, `summary`
  - Renders a preview card for each article (title, date, summary, link)
  - Injects these previews into the news index page

### Accessibility & WCAG Compliance
- All navigation and news previews use semantic HTML and class-based styling
- Keyboard navigation and focus styles are provided via CSS
- Color contrast and font sizes are chosen for readability

## Usage

1. **Install dependencies:**
   - Requires Python 3 and the `markdown` and `pyyaml` packages
   - Install with: `pip install markdown pyyaml`
2. **Build the site:**
   - Run: `python3 build.py`
   - Output will be in the `docs/` directory
3. **Serve or deploy:**
   - You can serve `docs/` with any static file server

## Adding Content
- Add Markdown files to `content/` and update `_content.yml` as needed
- For news articles, include a YAML front matter with at least `title`, `date`, and `summary`

## Customization
- Edit `static/css/theme-modern.css` for site-wide styles
- Edit layouts in `layouts/` for HTML structure
- Update `build.py` for advanced logic

## License
Open Physics Ed is open source. See `LICENSE` for details.
