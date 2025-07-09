def rewrite_menu_url(url: str) -> str:
    """
    Normalize menu URLs for output paths.
    - 'index.html' or 'index/index.html' -> 'index.html'
    - 'section/_index.html' -> 'section/index.html'
    - 'about.html' -> 'about/index.html'
    - 'about.htm' -> 'about/index.html'
    Returns the normalized URL as a string.
    """
    if url == 'index.html' or url == 'index/index.html':
        return 'index.html'
    if url.endswith('/_index.html') or url.endswith('/_index.htm'):
        return url.rsplit('/', 1)[0] + '/index.html'
    elif url.endswith('.html') and '/' not in url:
        return url.replace('.html', '/index.html')
    elif url.endswith('.htm') and '/' not in url:
        return url.replace('.htm', '/index.html')
    return url

#!/usr/bin/env python3
"""
Open Physics Ed Static Site Builder
- Processes all Markdown files referenced in _content.yml (or a single file with --file)
- Injects site meta, menu, and footer from _content.yml
- Preserves directory structure in docs/
- Computes correct relative menu links for each page
- Supports --debug for verbose output

Usage:
  ./build.py [--debug] [--file path/to/file.md]
"""
import sys
import os
import argparse
from pathlib import Path
import yaml
import re

try:
    import markdown
except ImportError:
    print("Please install the 'markdown' package.")
    sys.exit(1)

CONTENT_YML = Path('_content.yml')
CONTENT_DIR = Path('content')
DOCS_DIR = Path('docs')
LAYOUTS_DIR = Path('layouts')

def load_content_yml() -> dict:
    """
    Load and parse the _content.yml file for site structure and metadata.
    Returns a dictionary with site, menu, and content structure.
    """
    with open(CONTENT_YML) as f:
        return yaml.safe_load(f)

def parse_front_matter(md_text: str) -> tuple[dict, str]:
    """
    Extract YAML front matter and Markdown content from a Markdown file.
    Returns a tuple (meta, content), where meta is a dict and content is the Markdown string.
    """
    if md_text.startswith('---'):
        parts = md_text.split('---', 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1])
            content = parts[2].lstrip('\n')
            return meta, content
    return {}, md_text

def render_markdown(md_text: str) -> str:
    """
    Convert Markdown text to HTML using the markdown package.
    Returns the HTML string.
    """
    return markdown.markdown(md_text, extensions=['extra', 'codehilite'])

def load_layout(layout_name: str) -> str:
    """
    Load the HTML layout template by name from the layouts directory.
    Returns the template as a string.
    """
    layout_path = LAYOUTS_DIR / layout_name
    if not layout_path.exists():
        raise FileNotFoundError(f"Layout not found: {layout_path}")
    return layout_path.read_text()

def rel_link(from_path: str, to_url: str) -> str:
    """
    Compute a relative URL from one output path to another, or return external URLs unchanged.
    Returns the relative or absolute URL as a string.
    """
    def is_external(url: str) -> bool:
        return url.startswith('http://') or url.startswith('https://') or url.startswith('//')
    if is_external(to_url):
        return to_url
    # Always treat menu URLs as relative paths, never absolute
    to_url = to_url.lstrip('/')
    rel = os.path.relpath(to_url, os.path.dirname(from_path))
    return rel

def build_menu(menu: list[dict], current_output_path: str, debug: bool = False) -> str:
    """
    Build the HTML for the site menu, computing correct relative links for each item.
    Returns the menu HTML as a string.
    """
    items = []
    for item in sorted(menu, key=lambda x: x.get('weight', 0)):
        url = item["url"]
        url_out = rewrite_menu_url(url)
        rel_url = rel_link(current_output_path, url_out)
        if url.startswith('http://') or url.startswith('https://') or url.startswith('//'):
            link = f'<a href="{url}" target="_blank" rel="noopener">{item["name"]}</a>'
        else:
            link = f'<a href="{rel_url}">{item["name"]}</a>'
        items.append(f'<li class="site-menu-item">{link}</li>')
        if debug:
            print(f"[DEBUG] Menu: {item['name']} url={url} url_out={url_out} rel_url={rel_url} from={current_output_path}")
    return '<ul class="site-menu-list">' + ''.join(items) + '</ul>'

def build_html(meta, content_html, layout_name, site, menu_html, footer_html):
    html = load_layout(layout_name)
    # Compute correct relative path to theme-modern.css and images/logo.png
    output_path = meta.get('output_path', 'index.html')
    css_modern = rel_link(output_path, 'css/theme-modern.css')
    logo_rel = rel_link(output_path, 'images/logo.png')
    css_links = f'<link rel="stylesheet" href="{css_modern}" id="theme-modern">'
    # Accessible toggle button and script (data-theme switching)
    theme_toggle = '''
    <button id="theme-toggle" aria-label="Switch to dark mode" style="position:absolute;top:1.5rem;right:2rem;z-index:1000;background:var(--button-bg,#eee);color:var(--button-fg,#222);border:none;padding:0.5em 1em;border-radius:2em;cursor:pointer;font-size:1.2em;box-shadow:0 2px 8px rgba(0,0,0,0.10);" tabindex="0">
      <span id="theme-toggle-icon" aria-hidden="true">🌙</span>
      <span class="sr-only">Toggle theme</span>
    </button>
    <script>
    (function() {
      const btn = document.getElementById('theme-toggle');
      const icon = document.getElementById('theme-toggle-icon');
      function setTheme(theme) {
        if (theme === 'dark') {
          document.documentElement.setAttribute('data-theme', 'dark');
          icon.textContent = '☀️';
          btn.setAttribute('aria-label', 'Switch to light mode');
        } else {
          document.documentElement.setAttribute('data-theme', 'light');
          icon.textContent = '🌙';
          btn.setAttribute('aria-label', 'Switch to dark mode');
        }
        localStorage.setItem('theme', theme);
      }
      function getPreferredTheme() {
        const stored = localStorage.getItem('theme');
        if (stored === 'light' || stored === 'dark') return stored;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      function toggleTheme() {
        const current = getPreferredTheme();
        setTheme(current === 'dark' ? 'light' : 'dark');
      }
      document.addEventListener('DOMContentLoaded', function() {
        setTheme(getPreferredTheme());
        btn.addEventListener('click', toggleTheme);
        btn.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleTheme(); }
        });
      });
    })();
    </script>
    <style>
    .sr-only { position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0; }
    #theme-toggle { transition: background 0.2s, color 0.2s; }
    #theme-toggle:focus { outline: 2px solid #005fcc; outline-offset: 2px; }
    </style>
    '''
    html = html.replace('</head>', f'{css_links}\n{theme_toggle}\n</head>')
    # Inject site title everywhere
    site_title = site.get('title', 'Untitled')
    site_subtitle = site.get('subtitle', '')
    html = html.replace('{{ .SiteTitle }}', site_title)
    # Only inject subtitle if present
    if site_subtitle:
        html = html.replace('{{ .SiteSubtitle }}', f'<div class="site-subtitle">{site_subtitle}</div>')
    else:
        html = html.replace('{{ .SiteSubtitle }}', '')
    html = html.replace('{{ .LogoPath }}', logo_rel)
    html = html.replace('{{ .Title }}', meta.get('title', site_title))
    html = html.replace('{{ .Content }}', content_html)
    html = re.sub(r'<nav[^>]*>.*?</nav>', f'<nav class="site-menu" role="navigation" aria-label="Main menu">{menu_html}</nav>', html, flags=re.DOTALL)
    html = re.sub(r'<footer[^>]*>.*?</footer>', f'<footer style="text-align: center; margin: 2rem 0 1rem 0; color: #888; font-size: 0.9rem;">{footer_html}</footer>', html, flags=re.DOTALL)
    if '{{ now.Year }}' in html:
        from datetime import datetime
        html = html.replace('{{ now.Year }}', str(datetime.now().year))
    return html

def collect_files_from_content(content):
    files = set()
    # Always include homepage (content/_index.md)
    homepage = CONTENT_DIR / '_index.md'
    if homepage.exists():
        files.add(homepage)
    else:
        print(f"[ERROR] Homepage _index.md not found in content/")
        sys.exit(1)
    for section in content:
        main_page = section.get('main_page')
        if main_page:
            main_path = CONTENT_DIR / main_page
            if not main_path.exists():
                print(f"[ERROR] Main page {main_page} not found in content/")
                sys.exit(1)
            files.add(main_path)
        articles = section.get('articles')
        if articles and articles.get('folder'):
            folder = CONTENT_DIR / articles['folder']
            if not folder.exists():
                print(f"[ERROR] Articles folder {folder} not found.")
                sys.exit(1)
            # Require _index.md in every top-level folder
            index_md = folder / '_index.md'
            if not index_md.exists():
                print(f"[ERROR] Missing _index.md in {folder}. Every section folder must have an _index.md.")
                sys.exit(1)
            for f in folder.glob('*.md'):
                files.add(f)
    return sorted(files)

def build_file(mdfile, site, menu, footer_html, debug=False):
    md_path = Path(mdfile)
    if not md_path.exists():
        print(f"[ERROR] File not found: {md_path}")
        return
    md_text = md_path.read_text()
    meta, md_content = parse_front_matter(md_text)
    page_type = meta.get('type', 'base')
    if page_type == 'news':
        layout_name = 'news/single.html'
    else:
        layout_name = '_default/baseof.html'
    rel_path = md_path.relative_to(CONTENT_DIR)
    # Special handling for news index: embed news article previews
    is_news_index = (rel_path.parts == ("news", "_index.md"))
    content_html = render_markdown(md_content)
    if is_news_index:
        # Collect all news articles (exclude _index.md)
        news_dir = CONTENT_DIR / "news"
        news_files = [f for f in news_dir.glob("*.md") if f.name != "_index.md"]
        previews = []
        for nf in sorted(news_files, reverse=True):
            nmeta, ncontent = parse_front_matter(nf.read_text())
            title = nmeta.get("title", nf.stem)
            date = nmeta.get("date", "")
            summary = nmeta.get("summary", "")
            # Output path for article
            article_url = rel_link("news/index.html", f"news/{nf.stem}.html")
            # If the article is an _index.md, skip (shouldn't happen)
            if nf.name == "_index.md":
                continue
            # Preview card HTML
            previews.append(f'''
              <article class="news-preview">
                <h2><a href="{article_url}">{title}</a></h2>
                <div class="news-meta">{date}</div>
                <p class="news-summary">{summary}</p>
                <a class="news-readmore" href="{article_url}">Read more &rarr;</a>
              </article>
            ''')
        # Insert previews after the intro content
        content_html += '\n<div class="news-previews-list">' + '\n'.join(previews) + '</div>'
    rel_path = md_path.relative_to(CONTENT_DIR)
    # Home page: content/_index.md -> docs/index.html
    if str(rel_path) == '_index.md':
        out_path = DOCS_DIR / 'index.html'
        menu_path = 'index.html'
    # Top-level .md (e.g. about.md) -> docs/about/index.html
    elif len(rel_path.parts) == 1 and rel_path.suffix == '.md':
        name = rel_path.stem
        out_path = DOCS_DIR / name / 'index.html'
        menu_path = f'{name}/index.html'
    # Section index: content/section/_index.md -> docs/section/index.html
    elif rel_path.suffix == '.md' and rel_path.name == '_index.md' and len(rel_path.parts) == 2:
        section = rel_path.parts[0]
        out_path = DOCS_DIR / section / 'index.html'
        menu_path = f'{section}/index.html'
    # Section articles: content/section/article.md -> docs/section/article.html
    elif len(rel_path.parts) == 2 and rel_path.suffix == '.md':
        section = rel_path.parts[0]
        name = rel_path.stem
        if name == '_index':
            # Already handled above
            return
        out_path = DOCS_DIR / section / f'{name}.html'
        menu_path = f'{section}/{name}.html'
    else:
        # fallback: preserve subfolder and filename, just change .md to .html
        out_html = rel_path.with_suffix('.html')
        out_path = DOCS_DIR / out_html
        menu_path = str(out_html)
    menu_html = build_menu(menu, menu_path, debug=debug)
    # Pass output_path to meta for correct CSS rel path
    meta['output_path'] = str(out_path.relative_to(DOCS_DIR))
    html = build_html(meta, content_html, layout_name, site, menu_html, footer_html)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"[OK] Built {out_path}")
    if debug:
        print(f"--- Debug Info ---\nInput file: {md_path}\nOutput file: {out_path}\nLayout: {layout_name}\nMeta: {meta}\nContent length: {len(md_content)} chars\nHTML length: {len(html)} chars\n")

def main():
    parser = argparse.ArgumentParser(description="Build Open Physics Ed static site.")
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--file', help='Build only a single Markdown file')
    args = parser.parse_args()

    site_content = load_content_yml()
    site = site_content.get('site', {})
    menu = site_content.get('menu', [])
    footer_html = site.get('footer', '')
    content = site_content.get('content', [])


    # Ensure modern CSS is copied to docs/css only (not project root)
    import shutil
    css_src = Path('static/css/theme-modern.css')
    css_docs = Path('docs/css/theme-modern.css')
    css_docs.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(css_src, css_docs)

    # Copy static/images to docs/images (for logo and other assets)
    images_src = Path('static/images')
    images_dst = Path('docs/images')
    if images_src.exists():
        if images_dst.exists():
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)

    # Always create .nojekyll in docs root
    nojekyll_path = Path('docs/.nojekyll')
    nojekyll_path.write_text('')

    if args.file:
        build_file(args.file, site, menu, footer_html, debug=args.debug)
    else:
        files = collect_files_from_content(content)
        if not files:
            print("No files found to build.")
            sys.exit(0)
        for f in files:
            build_file(f, site, menu, footer_html, debug=args.debug)

if __name__ == '__main__':
    main()
