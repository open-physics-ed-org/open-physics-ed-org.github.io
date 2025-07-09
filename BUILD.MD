
# BUILD.MD: How to Tame and Build This Site 🛠️

Welcome, curious builder! This is your all-in-one guide to getting Open Physics Ed up and running. No arcane tools, no YAML sacrifices—just Python, Markdown, and a dash of fun.

## 🐍 Prerequisites
- Python 3.8 or newer
- (Strongly recommended) A Python virtual environment (`.venv`)

## 🚀 Quickstart
1. **Clone the repo and jump in:**
   ```sh
   git clone https://github.com/open-physics-ed/open-physics-ed-org.github.io.git
   cd open-physics-ed-org.github.io
   ```
2. **Set up your virtual environment:**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install the essentials:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Build the site!**
   - With VS Code: Hit `Cmd+Shift+B` (or `Ctrl+Shift+B` on Windows/Linux) to run the build task.
   - Or, run it yourself:
     ```sh
     .venv/bin/python3 build.py
     ```
   - Your shiny new site appears in the `docs/` folder. Open `docs/index.html` in your browser and enjoy!

## 🗂️ What’s in This Directory?

Here’s a whirlwind tour of the project:

```
.github/              # GitHub Actions and CI stuff
.vscode/              # VS Code build tasks and settings
.venv/                # Your Python virtual environment (keep it secret, keep it safe)
_build/               # (Optional) Build logs and artifacts
__pycache__/          # Python cache files (ignore these)
_content.yml          # The heart of the site: structure, menu, logo, meta
build.py              # The main build script (where the magic happens)
content/              # All your Markdown content (pages, news, about, etc.)
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

## 🧙‍♂️ How Does the Build Work?
- `build.py` reads `_content.yml` for site structure, menu, and logo info.
- It grabs Markdown from `content/`, injects it into HTML templates from `layouts/`, and writes the result to `docs/`.
- Static assets (CSS, images) are copied from `static/` to `docs/`.
- Menu, logo, and footer are all generated for you—no manual HTML editing needed!

## 💡 Tips & Notes
- **Not a Hugo site!** This is a custom Python static site generator. No Go, no config hell.
- **Menu, logo, and footer**: All injected from `_content.yml`.
- **Logo**: Accessible, WCAG-compliant, and on every page.
- **Color scheme**: Designed for accessibility and clarity.
- **No server required**: Just open `docs/index.html` in your browser.
- **Want to contribute?** See the [README.md](README.md) for more info and a friendly welcome!

---

Happy building! If you break something, you get to keep both pieces. 😄

---

For more details, see `README.md`.
