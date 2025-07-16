# WCAG Compliance Summary System: Engineering Notes

## Overview
- The compliance summary is generated using a Jinja2 template (`layouts/_default/compliance-summary.html`).
- All ARIA roles and CSS for accessibility are handled in the template, not in Python.
- Python code only queries the database, builds a context dictionary, and calls the template renderer.

## Key Implementation Points
- The summary table columns (configs) are discovered from unique `wcag_level` values in the database.
- Each cell in the table shows:
  - ✅ for zero errors
  - ❌N for N errors
  - N/A if no result
- Page titles in the summary link to their respective reports.
- The template uses proper ARIA roles and `.visually-hidden` CSS for accessibility.

## Python Code Structure
- `generate_compliance_table_page` builds the context and calls `render_page(context, 'compliance-summary.html')`.
- The context passed to the template includes:
  - `configs`: list of config names (columns)
  - `rows`: list of page dicts, each with `title`, `output_path`, `configs` (per config), and `last_checked`
- No HTML is built in Python; all rendering is done by the template.

## Future Improvements
- A stub function `read_config_order_from_yaml` is present for future YAML-driven config order (not yet implemented).
- The system is ready for further customization of config order, appearance, or accessibility features via the template.

## Static Assets
- CSS, JS, and images are loaded via the template and are present in the `static/` directory.
- The template references these assets for consistent styling and accessibility.

## Example Context Structure
```python
context = {
    'configs': configs,
    'rows': table_rows,
    'title': 'Accessibility Compliance Summary',
    'site': {
        'favicon': 'static/images/favicon.ico',
        'title': 'Open Physics Ed',
        'subtitle': 'Accessible OER for Physics',
    },
    'css_path': 'css/theme-light.css',
    'js_path': 'js/main.js',
    'logo_path': 'images/logo.png',
    'top_menu': [],
}
```

## Summary
- The workflow is now robust, maintainable, and accessible.
- All presentation and accessibility logic is centralized in the template.
- Python code is responsible only for data preparation and template invocation.
