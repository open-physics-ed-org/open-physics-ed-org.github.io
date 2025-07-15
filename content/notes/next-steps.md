# Next Steps: Robust Menu Generation for Static Site

## Database-Driven Solutions for Navigation Menu

1. **Store Relative Links in Database**
   - Add a column to the `content` table for precomputed relative links for each menu item.
   - Compute and store these links during the build process, referencing the output path of each page.
   - Menu generation simply reads the correct relative link from the database.

2. **Store Menu Hierarchy in Database**
   - Add parent/child relationships for menu items in the `content` table.
   - Use SQL queries to build the menu tree and compute links relative to the current page.
   - Enables dynamic menu generation for nested sections and child pages.

3. **Store Output Path and Section Info**
   - Ensure every menu item in the database has its output path and section/folder info.
   - Use this to compute relative links for each page during menu rendering.
   - Allows for accurate link computation regardless of page depth.

4. **Store Menu Context for Each Page**
   - For each page, store its menu context (e.g., current section, parent, siblings) in the database.
   - Use this context to generate correct menu links and highlight the active page.
   - Improves navigation UX and link accuracy.

5. **Store Canonical and Relative Links**
   - Store both canonical (site-rooted) and relative links for each menu item in the database.
   - Use relative links for local file browsing, canonical links for deployment.
   - Menu generation logic chooses the appropriate link type based on build mode.

---

These approaches leverage the database to ensure robust, context-aware menu link generation for all pages, including auto-generated section indexes and child pages. Choose and implement one or more to fix broken navigation menus across the site.
