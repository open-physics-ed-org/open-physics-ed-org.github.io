# Release v1.0: "Hank's Sturdy Build" 🏗️

## 🚀 Open Physics Education Network v1.0 — The Sturdy Foundation Release

We are proud to announce **v1.0** of the Open Physics Education Network site generator! This release, named **"Hank's Sturdy Build"** (in honor of Hank Hill and the Texas spirit of reliability), marks the first stable version of our custom Python static site builder.

---

## 🎯 What's New in v1.0?

### 🐍 `build.py`: The Heart of the Site
- **Custom Static Site Generator**: No Hugo, no Jekyll—just a handcrafted Python script that turns Markdown and YAML into a modern, accessible website.
- **YAML-Driven Structure**: Reads `_content.yml` to define the site menu, structure, logo, and meta info.
- **Markdown to HTML**: Converts all Markdown in `content/` into simple and accessible HTML using templates in `layouts/`.
- **WCAG-Compliant & Accessible**: Injects a modern, accessible theme, navigation, and logo into every page. Includes a dark/light mode toggle and keyboard navigation.
- **Smart Menu & Links**: Dynamically generates the menu for every page, with correct relative links and ARIA roles for accessibility.
- **Asset Management**: Copies CSS and images from `static/` to `docs/` automatically—no manual copying needed.
- **News & Previews**: Special handling for news articles and index, with preview cards and summaries.
- **.nojekyll Support**: Ensures GitHub Pages compatibility out of the box.
- **Debug Mode**: Run with `--debug` for detailed output and troubleshooting.

### 📁 Output Structure
- All output is in `docs/`, ready for GitHub Pages or any static host.
- Homepage: `docs/index.html`
- About: `docs/about/index.html`
- News: `docs/news/`
- CSS: `docs/css/theme-modern.css`
- Images: `docs/images/`

### 📝 Documentation
- See [`README.md`](README.md) for a friendly overview and quickstart.
- See [`BUILD.md`](BUILD.md) for a deep dive into the build process, file structure, and how to extend or debug the site.

---

## 💡 Why This Matters
- **Accessible by Design**: Every page is built with accessibility and clarity in mind.
- **Open & Extensible**: Anyone can add content, improve the build, or adapt the process for new courses.
- **Simple, Reliable, and Texas-Tough**: Like Hank Hill, this build system is sturdy, dependable, and ready for the long haul.

---

This is just the beginning—let's build a more open, accessible future for physics education!