# Demo Mode Plan for AI Force Migration Platform

## Purpose
Demo mode allows users to explore the app's features and functionality even if the database is unavailable or the user is not found. This ensures a robust user experience and supports demos, onboarding, and troubleshooting.

---

## 1. Standardize Enum Values
- All enums (roles, statuses, etc.) should be lowercase in models and seed data.
- Alembic migrations should update schema/data accordingly.

---

## 2. Seed Demo Data with Known UUIDs
- Use fixed UUIDs for demo entities:
  - **Demo Client ID:** `11111111-1111-1111-1111-111111111111`
  - **Demo Engagement ID:** `22222222-2222-2222-2222-222222222222`
  - **Demo Session ID:** `33333333-3333-3333-3333-333333333333`
  - **Demo User Email:** `demo@democorp.com`
  - **Demo Client Name:** `Democorp`
  - **Demo Engagement Name:** `Cloud Migration 2024`

---

## 3. Frontend-Only Demo Mode & Error Handling (Revised & Secure Approach)
- The backend preserves 404s for `/api/v1/me` and `/api/v1/clients/default` if user/context is not found or DB is down.
- The frontend always starts at `/login` unless a valid user is present.
- Only authenticated users (with a valid token) trigger requests to `/api/v1/me` and `/api/v1/clients/default`.
- If `/api/v1/me` or `/api/v1/clients/default` returns a 404 or error, the frontend immediately logs out and redirects to `/login` **unless the current user is the demo user**.
- The login page always offers a "Try Demo Mode" button as a fallback.
- **Security:** Only a dedicated `loginWithDemoUser` method is exposed in AuthContext, which sets only the hardcoded demo user, client, engagement, and session context. No arbitrary user injection is possible from the UI.
- The login page uses this method for demo mode. All other authentication must go through the real backend.
- If demo mode is enabled, the frontend sets demo user, client, engagement, and session context directly, and displays a clear demo mode banner.
- When setting demo context, the objects for client, engagement, and session must match the full interface definitions (including all required fields and correct literal types).
- AuthContext propagates these demo objects to ClientContext, EngagementContext, and SessionContext using the exposed setDemoClient, setDemoEngagement, and setDemoSession methods. This ensures all context consumers work seamlessly in demo mode.
- On logout, demo mode is cleared and the user is returned to the login page.

**Frontend Implementation Steps:**
1. **Login Page:**
   - If login fails due to DB error or user not found, show a "Try Demo Mode" button.
   - When clicked, call `loginWithDemoUser()` from AuthContext to set the hardcoded demo user context.
2. **API Calls & AuthContext:**
   - If demo mode is enabled, skip real authentication and use the demo user context.
   - If `/api/v1/me` or `/api/v1/clients/default` returns a 404 or error, call `logout()` and redirect to `/login` **unless the current user is the demo user, in which case the error is ignored and the demo context remains active**.
3. **Routing:**
   - The app always starts at `/login` if there is no authenticated user.
   - Only redirect to `/session/select` if a user is authenticated but has no client context.
4. **UI Banner:**
   - Display a clear banner or badge across the app when in demo mode.
5. **Logout:**
   - Clear the `demoMode` flag and return to the login page.

---

## 4. Frontend: Robust Error Handling
- If `/api/v1/me` or `/api/v1/clients/default` fails due to DB issues, show a friendly error and offer demo mode.
- If the user is in demo mode, use the fixed demo IDs for all context.
- **If the current user is the demo user, never log out or redirect to login due to API errors. The demo context remains active.**

---

## Implementation Notes
- Demo mode should be clearly separated from real user data and actions.
- All demo data should be read-only and resettable.
- Demo mode should be available even if the backend cannot connect to the database.
- **No arbitrary user injection is possible from the UI. Only the hardcoded demo user can be set via a dedicated method.**
- **Error handling in AuthContext must not log out or redirect if the current user is the demo user. This ensures the app always sees a valid user context and does not need to know about demo mode.**

---

## Next Steps
1. Update models and seed scripts for lowercase enums and fixed UUIDs.
2. Update frontend login page to handle DB errors and offer demo mode using `loginWithDemoUser`.
3. Add clear UI indicators for demo mode.
4. Ensure all context fetch errors result in logout and redirect to login, **except for the demo user, who remains active even on error**. 