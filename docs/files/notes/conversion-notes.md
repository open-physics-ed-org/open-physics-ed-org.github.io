# Conversion Logic Modernization: Project Notes

## Big Picture
- Modernize the static site generator for open physics education.
- Make content conversion logic robust, extensible, and database-driven.
- Store conversion capabilities in the SQLite database (`conversion_capabilities` table).
- Support Markdown, Jupyter Notebooks, DOCX, and more.
- Maintain hierarchical relationships from the Table of Contents (TOC) YAML.

## Key Steps Completed
1. **Database Schema Update**
   - Added `conversion_capabilities` table to SQLite.
2. **Helper Function**
   - Implemented `get_enabled_conversions` in `db_utils.py`.
3. **Refactored Conversion Logic**
   - Updated `scan.py` to use DB-driven conversion flags via `get_conversion_flags`.
4. **Testing and Debugging**
   - Fixed import/circular import issues and environment setup.
   - Moved import for `get_enabled_conversions` inside the function.
5. **Scan Workflow**
   - Successfully ran scan workflow to populate the database.

## Current Status
- Scan workflow populates the database with content records and conversion flags.
- Conversion logic is now robust and extensible.
- Next step: Inspect database and test build/conversion workflow.

## Next Steps
- Inspect the `content` table for correct conversion flags.
- Test build/conversion logic to ensure only enabled conversions are performed.
- Extend or refine conversion logic as needed.

---
*These notes summarize the conversion logic modernization and current project status.*
