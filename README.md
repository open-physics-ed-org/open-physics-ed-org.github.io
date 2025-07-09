# Welcome to Open Physics Ed dot Org! 🚀

*Open Physics Ed* is a fun, friendly, and community-powered static site for sharing open physics education resources, news, and more. No Hugo, no Jekyll, no magic SSGs—just pure Python and a sprinkle of creativity!

## What Makes This Site Special?

- **Handcrafted Python Build**: Forget the static site generator hype. This project uses a custom Python script (`build.py`) to turn Markdown and YAML into a beautiful, accessible website.
- **Markdown Content**: All your pages and news live in `content/` and are organized by `_content.yml`.
- **Accessible by Design**: Color schemes, navigation, and our stylish logo are all WCAG-compliant.
- **Easy to Hack**: Want to add a page? Just drop a Markdown file in `content/` and update `_content.yml`.
- **No Server Needed**: Open `docs/index.html` in your browser and enjoy!
- **VS Code Friendly**: Comes with a build task that uses your Python virtual environment for smooth, reproducible builds.

## Project Map (a.k.a. "What's in this repo?")

```
.github/              # GitHub workflows (CI, etc.)
.vscode/              # VS Code settings and build tasks
.venv/                # Python virtual environment (recommended!)
_build/               # (Optional) Build logs and artifacts
__pycache__/          # Python cache files
_content.yml          # Site structure, menu, meta, logo, etc.
build.py              # The main build script (the magic happens here)
content/              # Markdown content (pages, news, about, etc.)
css/                  # (Legacy) CSS, not used in build
docs/                 # Output static site (HTML, CSS, images)
generate_menu.py      # (Optional) Menu generation helper
layouts/              # HTML templates (not Hugo, just HTML!)
requirements.txt      # Python dependencies
scripts/              # (Optional) Extra build scripts
static/               # Static assets (css, images)

# Inside static/:
static/css/           # CSS themes (modern, dark, light, tailwind)
static/images/        # Logo and other images

# Inside docs/ (after build):
docs/index.html       # Home page (open this in your browser!)
docs/news/            # News articles
docs/about/           # About page
docs/css/             # CSS for the site
docs/images/          # Logo, etc.

# VS Code build task:
.vscode/tasks.json    # Runs `.venv/bin/python3 build.py` for you
```

## How Do I Build This Thing?

To set up your environment automatically, run:

```sh
python3 setup.py
```

This will:
- Create a Python virtual environment in `.venv` if it doesn't exist
- Install all dependencies from `requirements.txt`

After setup, activate the environment:

```sh
source .venv/bin/activate
```

Then build the site:

```sh
python build.py
```

Your site will be ready in `docs/index.html`.

Check out [`BUILD.MD`](BUILD.MD) for a fun, step-by-step guide to setting up your environment and building the site. Spoiler: it's just a couple of commands!

---

**Questions? Ideas? PRs?**

We love contributions and feedback. If you spot a typo, want to add a feature, or just want to say hi, open an issue or pull request!

---

*P.S. This README is best enjoyed with a cup of coffee and a sense of curiosity.*
