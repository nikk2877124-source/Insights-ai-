# TODO - Streamlit Navigation Fix

- [ ] Understand current navigation wiring (custom sidebar + selected_page usage)
- [ ] Implement single navigation system: selected_page from `render_sidebar()` determines which page module renders.
- [ ] Remove default Streamlit multipage navigation sidebar (keep only custom sidebar).
- [ ] Implement logout redirect to Login using session state + selected page.
- [ ] Gate protected pages with `require_auth()`.
- [ ] Ensure no placeholder routing text is shown.
- [ ] Remove duplicate/unused navigation logic.
- [ ] Run Streamlit to verify: only one sidebar visible; clicking buttons navigates; protected pages work.

