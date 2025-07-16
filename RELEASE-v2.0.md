# Pocket Sand Edition (v2.0) 🚨🦸‍♂️🛠️

A robust rebuild of OERForge, inspired by Dale Gribble’s legendary “Pocket Sand” move—quick, clever, and ready for anything. This release brings a modular design, helper libraries, and a fully documented, extensible codebase for open education.

## 🏗️ Highlights

- **Modular architecture:** Each major function (build, convert, scan, export, verify, copy) is now a dedicated module with clear APIs.
- **Helper libraries:** Streamlined content conversion, asset management, accessibility checking, and export workflows.
- **Robust error handling:** Consistent logging and error management across all modules.
- **Accessibility:** Integrated WCAG/Pa11y workflows for automated compliance checking and reporting.
- **Documentation:** Every module is documented in Markdown for new users and contributors.
- **Extensibility:** Easy to add new formats, workflows, and integrations.

## 🧩 Major Modules

- `build.py` — Orchestrates the entire build workflow.
- `oerforge.convert` — Converts Markdown, Jupyter, and DOCX to multiple formats.
- `oerforge.copyfile` — Handles file and asset copying for deployment.
- `oerforge.db_utils` — Manages the SQLite database for content and assets.
- `oerforge.export_all` — Exports all site content and assets for backup or external use.
- `oerforge.make` — Static site generator with Jinja2 templates and navigation.
- `oerforge.scan` — Scans content and assets, populates the database.
- `oerforge.verify` — Automated accessibility checking and badge/report generation.
- `pa11y.py` — Batch runner for accessibility checks.

## 🚀 How to Use

- See the documentation in `content/documentation/` for API references and usage examples.
- Run `build.py` to orchestrate the full site build.
- Use `pa11y.py` for batch accessibility validation.

## 📄 License

See LICENSE in the project root.
