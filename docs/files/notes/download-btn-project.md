# Dynamic Download Button Integration Plan for OERForge

## Backend Data Flow

1. **Conversion Tracking**
   - All conversion outputs (e.g., `.md`, `.docx`, `.pdf`, etc.) are tracked in the `conversion_results` table.
   - Each record links a `content_id` (from the `content` table) to a `source_format`, `target_format`, `output_path`, and `status`.

2. **Content and Conversion Query Helpers**
   - Use `get_records('conversion_results', where_clause="content_id=?", params=(content_id,))` from `db_utils.py` to fetch all available conversions for a given content item.
   - Use `get_records('content', ...)` to fetch metadata (title, slug, output_path, etc.) for each page.

3. **Output Path Consistency**
   - Output paths for all formats are generated using TOC slugs and helpers in `path_utils.py` and are stored in the database.

## Template Integration

1. **Template Data Export**
   - When rendering a page (e.g., in a Hugo-like template), query the database for all available conversions for the current page.
   - For each conversion, get the `target_format` and `output_path`.

2. **Dynamic Download Button Rendering**
   - In the template, iterate over the conversion results for the current page.
   - For each available format, render a download button or link:
     ```html
     {% for conversion in conversions %}
       <a href="{{ conversion.output_path }}" class="download-btn">{{ conversion.target_format|upper }}</a>
     {% endfor %}
     ```
   - The button text can be customized (e.g., "Download DOCX", "Download PDF").

3. **Frontend Logic**
   - Optionally, use JavaScript to enhance the buttons (e.g., show/hide based on availability, add icons).

## Implementation Steps

1. **Add a helper function in `db_utils.py`**
   - Example: `get_available_conversions_for_page(page_output_path)` that returns all conversion results for a given page.

2. **Update the build/export logic**
   - Ensure all conversions write their output paths to the database and to the build/docs folder.

3. **Template/Frontend**
   - Update Hugo-like templates to query and render download buttons dynamically using the conversion results.

## Summary

- All conversion outputs are tracked in the database.
- Query conversion results for each page to determine available download formats.
- Render dynamic download buttons in templates using this data.
- The system is extensible for new formats and conversion types.
