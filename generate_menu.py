#!/usr/bin/env python3
"""
Generate a site menu HTML from _content.yml menu section, rewriting links to output structure.
- about.html -> about/index.html
- news/_index.html -> news/index.html
- index.html stays index.html

Usage: python3 generate_menu.py
"""
import yaml
from pathlib import Path

def rewrite_menu_url(url):
    if url.endswith('/_index.html') or url.endswith('/_index.htm'):
        return url.rsplit('/', 1)[0] + '/index.html'
    elif url.endswith('.html') and '/' not in url:
        return url.replace('.html', '/index.html')
    elif url.endswith('.htm') and '/' not in url:
        return url.replace('.htm', '/index.html')
    if url == 'index/index.html':
        return 'index.html'
    return url


def generate_menu_html(menu):
    # Tailwind CSS classes for horizontal nav, dark mode, and spacing
    ul_class = (
        "flex gap-8 list-none m-0 p-0 justify-center "
        "bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 py-4"
    )
    a_class = (
        "text-gray-800 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 "
        "transition-colors duration-200 font-medium px-2 py-1 rounded"
    )
    items = []
    for item in sorted(menu, key=lambda x: x.get('weight', 0)):
        url_out = rewrite_menu_url(item['url'])
        link = f'<a href="{url_out}" class="{a_class}">{item["name"]}</a>'
        items.append(f'<li>{link}</li>')
    return f'<ul class="{ul_class}">' + ''.join(items) + '</ul>'

def main():
    with open('_content.yml') as f:
        data = yaml.safe_load(f)
    menu = data.get('menu', [])
    html = generate_menu_html(menu)
    print(html)

if __name__ == '__main__':
    main()
