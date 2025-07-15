# Dynamic Download Button Implementation Plan

This document outlines a step-by-step, verbose plan for implementing dynamic download buttons for all pages in the OERForge static site generator. The goal is to display download buttons for each available conversion format (PDF, DOCX, TEX, etc.) only when the conversion is complete and verified, using the database as the source of truth. The plan leverages existing CSS for both light and dark themes.

## Step 1: Template Review and Button Placement
- **Locate HTML Templates:**
  - Find the main page templates in the `layouts/` directory (e.g., `layouts/_default/base.html`, `layouts/_default/single.html`, etc.).
- **Identify Placement:**
  - Determine where download buttons should appear on each page (typically near the top, bottom, or sidebar).
  - Ensure the placement is consistent across all page types.

## Step 2: Database Query for Verified Conversions
- **Conversion Results Table:**
  - After running all conversions, the database (usually `db/sqlite.db`) contains a `conversion_results` table (or similar) that tracks which formats are available for each page.
- **Query Logic:**
  - For each page, query the database for its available conversions:
    - Example SQL: `SELECT format, output_path FROM conversion_results WHERE source_path=? AND verified=1`
  - Only show buttons for formats where `verified=1` (conversion succeeded and file exists).

## Step 3: Dynamic Button Rendering in Templates
- **Button Generation:**
  - For each verified format, generate a download button in the template.
  - Use the output path from the database to link the button to the correct file.
- **Styling:**
  - Apply the existing CSS classes for light and dark themes to each button (e.g., `class="download-btn theme-light"` and `class="download-btn theme-dark"`).
  - Ensure buttons are visually consistent and accessible.
- **Example Button HTML:**
  ```html
  <a href="{{ output_path }}" class="download-btn theme-light">Download PDF</a>
  <a href="{{ output_path }}" class="download-btn theme-dark">Download DOCX</a>
  ```

## Step 4: Integration and Testing
- **Template Integration:**
  - Update all relevant templates to include the dynamic button logic.
  - Use Jinja2, Mako, or your templating engine to loop over available formats and render buttons.
- **Testing:**
  - Build the site and verify that buttons appear only for pages and formats with verified conversions.
  - Check both light and dark themes for correct styling.
  - Confirm that download links work and files are accessible.

## Step 5: Edge Cases and Accessibility
- **Missing Conversions:**
  - If no conversions are available for a page, do not render any buttons.
- **Accessibility:**
  - Ensure buttons have descriptive text and are keyboard accessible.
  - Use ARIA labels if needed for screen readers.

## Step 6: Maintenance and Future Enhancements
- **Automated Checks:**
  - Consider adding automated tests to verify button rendering and file availability.
- **Additional Formats:**
  - Easily extend logic to support new formats by updating the database and template loop.
- **User Feedback:**
  - Optionally, display tooltips or status messages for unavailable formats.

---

This plan ensures that download buttons are only shown for verified conversions, are styled for both light and dark themes, and are integrated across all pages. Each step can be checked and tested independently for robust implementation.
