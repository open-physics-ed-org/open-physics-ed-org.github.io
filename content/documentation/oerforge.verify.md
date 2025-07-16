# oerforge.verify

Comprehensive accessibility verification and reporting for static HTML sites using Pa11y and WCAG standards.

---

## Overview

`oerforge.verify` provides tools to automate accessibility checks, badge generation, and reporting for HTML files. It integrates with Pa11y, stores results in a SQLite database, and injects badges and links to accessibility reports directly into your site. This module is designed for static site generators and educational content platforms.

---

## Functions

### load_pa11y_config

```python
def load_pa11y_config(yml_path: str = "_content.yml") -> dict
```

Load Pa11y configuration and logo info from a YAML file. Returns a dictionary of configuration values.

**Parameters**
- `yml_path` (str): Path to the YAML config file. Defaults to `_content.yml`.

**Returns**
- `dict`: Parsed configuration data.

---

### run_pa11y_on_file

```python
def run_pa11y_on_file(html_path: str, config_path: Optional[str] = None, wcag_level: str = "AA") -> Optional[List[Dict[str, Any]]]
```

Run Pa11y accessibility checks on a single HTML file. Returns parsed JSON results or `None` on error.

**Parameters**
- `html_path` (str): Path to the HTML file.
- `config_path` (Optional[str]): Optional path to Pa11y config.
- `wcag_level` (str): WCAG level to check ("AA" or "AAA").

**Returns**
- `Optional[List[Dict[str, Any]]]`: List of issue dictionaries, or `None` if Pa11y fails.

---

### get_content_id_for_file

```python
def get_content_id_for_file(html_path: str, conn) -> Optional[int]
```

Get the database content ID for a given HTML file.

**Parameters**
- `html_path` (str): Path to the HTML file.
- `conn`: SQLite connection object.

**Returns**
- `Optional[int]`: Content ID, or `None` if not found.

---

### store_accessibility_result

```python
def store_accessibility_result(content_id: int, pa11y_json: List[Dict[str, Any]], badge_html: str, wcag_level: str, error_count: int, warning_count: int, notice_count: int, conn=None)
```

Store the latest accessibility result for a page in the database.

**Parameters**
- `content_id` (int): Content ID from the database.
- `pa11y_json` (List[Dict[str, Any]]): Pa11y result data.
- `badge_html` (str): HTML for the accessibility badge.
- `wcag_level` (str): WCAG level checked.
- `error_count` (int): Number of errors.
- `warning_count` (int): Number of warnings.
- `notice_count` (int): Number of notices.
- `conn`: SQLite connection object.

---

### generate_badge_html

```python
def generate_badge_html(wcag_level: str, error_count: int, logo_info: dict, report_link: str) -> str
```

Generate HTML for a WCAG badge, linking to the accessibility report.

**Parameters**
- `wcag_level` (str): WCAG level ("AA", "AAA", etc.).
- `error_count` (int): Number of errors.
- `logo_info` (dict): Mapping of WCAG levels to badge/logo URLs.
- `report_link` (str): Link to the accessibility report.

**Returns**
- `str`: HTML for the badge.

---

### inject_badge_into_html

```python
def inject_badge_into_html(html_path: str, badge_html: str, report_link: str, logo_info: dict)
```

Inject the accessibility badge/button into the HTML file after the `<main>` tag.

**Parameters**
- `html_path` (str): Path to the HTML file.
- `badge_html` (str): Badge HTML to inject.
- `report_link` (str): Link to the accessibility report.
- `logo_info` (dict): Badge/logo info.

---

### generate_nav_menu

```python
def generate_nav_menu(context: dict) -> list
```

Generate the navigation menu for the site, based on database content and current page context.

**Parameters**
- `context` (dict): Context dictionary, typically with `rel_path`.

**Returns**
- `list`: List of menu item dictionaries.

---

### generate_wcag_report

```python
def generate_wcag_report(html_path: str, issues: List[Dict[str, Any]], badge_html: str, config: dict)
```

Generate a detailed HTML accessibility report for a file using Jinja2 templates.

**Parameters**
- `html_path` (str): Path to the HTML file.
- `issues` (List[Dict[str, Any]]): List of Pa11y issues.
- `badge_html` (str): Badge HTML.
- `config` (dict): Page and WCAG config.

**Returns**
- `str`: Path to the generated report.

---

### process_all_html_files

```python
def process_all_html_files(build_dir="build", config_file=None, db_path="db/sqlite.db")
```

Process all HTML files in the build directory: run accessibility checks, store results, generate badges and reports, and copy changed files to the docs directory.

**Parameters**
- `build_dir` (str): Directory containing HTML files.
- `config_file` (Optional[str]): Optional Pa11y config file.
- `db_path` (str): Path to the SQLite database.

---

### copy_to_docs

```python
def copy_to_docs()
```

Copy all changed files from the build directory to the docs directory.

---

### main

```python
def main()
```

CLI entry point. Parses arguments, runs checks, stores results, and generates reports as needed.

---

## Usage Example

```python
from oerforge import verify
verify.process_all_html_files()
```

---

## Requirements
- Python 3.7+
- Pa11y (Node.js CLI tool)
- SQLite3
- Jinja2
- PyYAML
- BeautifulSoup4

---

## See Also
- [Pa11y Documentation](https://pa11y.org/)
- [WCAG Standards](https://www.w3.org/WAI/standards-guidelines/wcag/)

---

## License
See `LICENSE` in the project root.
