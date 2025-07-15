"""
path_utils.py

Utility functions for building output paths for all formats (html, docx, pdf, tex, md, ipynb, etc.)
using TOC slugs from _content.yml. Ensures consistent folder structure for all outputs.
"""
import os

def get_output_path_for_format(toc, file_path, ext, build_root):
    """
    Given a TOC, a source file path (e.g. 'sample/welcome.md'), an extension (e.g. 'docx'),
    and the build root, return the correct output path respecting parent slugs.
    """
    def find_path(items, target, parent_slugs=None):
        if parent_slugs is None:
            parent_slugs = []
        for item in items:
            slug = item.get('slug')
            children = item.get('children', [])
            if item.get('file') == target:
                return parent_slugs, item
            if children:
                result = find_path(children, target, parent_slugs + [slug] if slug else parent_slugs)
                if result:
                    return result
        return None
    result = find_path(toc, file_path)
    if not result:
        # Fallback: no slug, just use build_root
        out_dir = build_root
    else:
        parent_slugs, item = result
        out_dir = os.path.join(build_root, *parent_slugs) if parent_slugs else build_root
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(out_dir, f"{base_name}.{ext}")
    return out_path
