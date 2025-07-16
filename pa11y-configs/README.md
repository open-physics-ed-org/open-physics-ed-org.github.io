# Pa11y Configurations

This folder contains example Pa11y configuration files for different accessibility compliance needs. Use these with the `--config` or `-c` flag in your verification scripts.

## Config Files

### basic.json
- **standard**: `WCAG2AA` — Checks for WCAG 2.0 AA compliance (common baseline).
- **ignore**: `["notice"]` — Only errors and warnings are reported; notices are ignored.
- **timeout**: `30000` — Each test has a 30-second timeout.

### eu.json
- **standard**: `WCAG2AA` — Meets EU accessibility requirements.
- **ignore**: `[]` — Reports all issues (errors, warnings, and notices).
- **timeout**: `30000` — 30-second timeout.
- **viewport**: `{width: 1280, height: 800}` — Simulates a desktop browser size common in the EU.
- **screenCapture**: `false` — No screenshots taken.

### strict.json
- **standard**: `WCAG2AAA` — The strictest level of WCAG 2.0 compliance.
- **ignore**: `[]` — Reports all issues.
- **timeout**: `60000` — 60-second timeout for complex pages.
- **viewport**: `{width: 1280, height: 800}` — Desktop browser size.
- **screenCapture**: `true` — Takes screenshots of each page.
- **wait**: `2000` — Waits 2 seconds before running checks (for dynamic content).

## Usage

To use a config, run:

```
python oerforge/verify.py --config pa11y-configs/basic.json
```

Or substitute `basic.json` with `eu.json` or `strict.json` as needed.

## Customization
- You can copy and modify these files to suit your project's needs.
- See the [Pa11y documentation](https://github.com/pa11y/pa11y) for all available options.
