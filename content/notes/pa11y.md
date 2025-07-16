# Pa11y Accessibility Integration

This project supports optional accessibility compliance checking using [Pa11y](https://github.com/pa11y/pa11y).

## How it works
- If you want to check accessibility, install Pa11y locally (requires Node.js):
  ```sh
  npm install -g pa11y
  ```
- The `verify.py` script will detect if Pa11y is installed and, if so, run accessibility checks on built HTML files.
- If Pa11y is not installed, accessibility checks are skipped and a message is shown.

## Next steps
- This document will be updated as the integration is developed.
- Planned: CLI options, reporting, and integration with CI.

# Pa11y Integration and WCAG Conformance Logos

## WCAG Conformance Logos Reference

Official WCAG conformance logos and their usage recommendations are not hard-coded in the codebase. Instead, they are stored in a shared JSON config file:

- Location: `pa11y-configs/wcag_logos.json`
- Source: [W3C WCAG Conformance Logos](https://www.w3.org/WAI/standards-guidelines/wcag/conformance-logos/#logos)

Example structure:
```json
{
  "A": {
    "url": "https://www.w3.org/WAI/wcag2A",
    "img": "https://www.w3.org/WAI/wcag2A-blue-v.svg",
    "alt": "WCAG 2.0 Level A Conformance Logo",
    "usage": "See https://www.w3.org/WAI/standards-guidelines/wcag/conformance-logos/#logos"
  },
  ...
}
```

## How to Use
- Load this config in your badge/report generation code to reference the correct logo and usage info for each WCAG level.
- If the W3C updates their logos or recommendations, update this file (not your code).
- Both the Pa11y integration and the site generator should use this config for consistency.

## Why?
- Ensures compliance with official recommendations.
- Makes updates easy and avoids hard-coding URLs or HTML.
- Centralizes logo and usage info for all scripts and reports.
