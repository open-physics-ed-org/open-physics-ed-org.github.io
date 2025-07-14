import os
import re
import markdown
import shutil

# Paths configuration
README_PATH = "README.md"
OUTPUT_PATH = "docs/index.html"
TEMPLATE_PATH = "static/templates/readme_index.html"
CSS_SRC_DIR = "static/css"
CSS_DEST_DIR = "docs/css"
JS_SRC_DIR = "static/js"
JS_DEST_DIR = "docs/js"

def copy_assets(src_dir, dest_dir):
    """
    Copy all files from src_dir to dest_dir. Creates dest_dir if it doesn't exist.
    """
    if not os.path.exists(src_dir):
        return
    os.makedirs(dest_dir, exist_ok=True)
    for fname in os.listdir(src_dir):
        src_file = os.path.join(src_dir, fname)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, os.path.join(dest_dir, fname))

def build_index_from_readme(readme_path, output_path, template_path):
    """
    Generate an HTML index page from a Markdown README file using a template.

    Args:
        readme_path (str): Path to the README.md file.
        output_path (str): Path to write the generated HTML file.
        template_path (str): Path to the HTML template file.
    """
    if not os.path.isfile(readme_path):
        raise FileNotFoundError(f"README not found: {readme_path}")
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    if not output_path.endswith(".html"):
        raise ValueError("Output file must be .html")

    with open(readme_path, "r", encoding="utf-8") as f:
        md_content = f.read()


    def copy_image_assets(md_content, docs_dir):
        # Find all <img src="..."> and ![alt](url) patterns
        img_srcs = re.findall(r'<img[^>]+src="([^"]+)"', md_content)
        img_md_srcs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', md_content)
        all_imgs = set(img_srcs + img_md_srcs)
        for img_path in all_imgs:
            src_path = img_path
            dest_path = os.path.join(docs_dir, img_path)
            dest_dir = os.path.dirname(dest_path)
            if os.path.exists(src_path):
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(src_path, dest_path)
            else:
                print(f"[WARN] Image not found: {src_path}")

    # Copy image assets referenced in README
    copy_image_assets(md_content, "docs")

    # Use markdown package for full markdown support
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'codehilite'])

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    html_page = template.replace("{{ content }}", html_content)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_page)
    print(f"[INFO] Wrote {output_path}")

    # Copy CSS/JS assets
    copy_assets(CSS_SRC_DIR, CSS_DEST_DIR)
    copy_assets(JS_SRC_DIR, JS_DEST_DIR)

    # Create empty .nojekyll file in docs/
    nojekyll_path = os.path.join(os.path.dirname(output_path), '.nojekyll')
    with open(nojekyll_path, 'w', encoding='utf-8') as f:
        pass
    print(f"[INFO] Wrote {nojekyll_path}")

if __name__ == "__main__":
    build_index_from_readme(
        README_PATH,
        OUTPUT_PATH,
        TEMPLATE_PATH
    )