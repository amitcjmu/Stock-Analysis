
# Complete Auth and RBAC Workflow Guide

This document provides a detailed, step-by-step guide to the authentication (AuthN) and Role-Based Access Control (RBAC) mechanisms within the AI Modernize Migration Platform. It is intended to help developers and other coding agents understand and troubleshoot the system.

The analysis follows a user performing a standard workflow: logging in and uploading a CMDB file.

**Last Updated:** July 4, 2025

---

## 1. High-Level Overview

The platform's security model can be broken down into two main concepts:

1.  **Authentication (AuthN):** Verifying a user's identity. This is achieved through a classic email/password login that results in a JSON Web Token (JWT).
2.  **Authorization (AuthZ) / RBAC:** Determining what an authenticated user is allowed to do. This is primarily enforced through a combination of a user's role (e.g., `admin`, `user`) and, more importantly, a **request context** system that ensures users can only access data associated with their specific client and engagement.

All API access is multi-tenant aware, and data is strictly scoped. This is not just a feature but a core security principle of the backend architecture.

---

## 2. The User Login Flow (Authentication)

This section details the end-to-end process of a user logging in.

### Step 2.1: Frontend - Submitting Credentials

- **Initiation:** The user enters their email and password into a login form, likely rendered by a React component.
- **Service Hook:** The `useAuthService` hook (from `src/contexts/AuthContext/services/authService.ts`) orchestrates the login process via its `login` function.
- **API Call:** The `login` function calls `authApi.login` (from `src/lib/api/auth.ts`), which makes a `POST` request to the backend endpoint: `/api/v1/auth/login`.

### Step 2.2: Backend - Verifying Credentials & Issuing Token

- **Endpoint:** The request is handled by the `login_user` function in `backend/app/api/v1/auth/handlers/authentication_handlers.py`.
- **Core Logic:** This handler delegates the main work to `AuthenticationService.authenticate_user` (from `backend/app/services/auth_services/authentication_service.py`).
- **Verification Steps:**
    1.  The service queries the `users` table for the provided email.
    2.  It verifies that the user account is active and approved.
    3.  It securely compares the provided password against the stored hash using `bcrypt.checkpw`.
    4.  It fetches the user's roles from the `user_roles` table to determine if they have admin privileges.
- **Token Generation:**
    - Upon successful verification, the `JWTService` (from `backend/app/services/auth_services/jwt_service.py`) is called.
    - It creates a JWT containing a payload with the `sub` (subject, which is the `user.id`), `email`, and `role`.
    - This token is signed using the `SECRET_KEY` from the application's configuration and set to expire after a configured duration.
- **Response:** The backend returns a JSON object containing the user's details and the `access_token`.

### Step 2.3: Frontend - Storing the Token & Initializing Context

- **Token Storage:** Back in the `useAuthService.login` function, the received JWT is stored in the browser's `localStorage` under the key `auth_token`. The user's information is also stored under `auth_user`. This is handled by the `tokenStorage` utility.
- **Context Establishment:** This is a critical step. Immediately after storing the token, the frontend makes a `GET` request to `/context/me`. This endpoint validates the new token and returns a complete `UserContext` object, which includes the user's definitive role, their associated clients, engagements, and active flows.
- **State Update:** The `AuthContext` (`src/contexts/AuthContext/index.tsx`) is populated with the user object and the detailed context information. This makes the user's identity and permissions available to the entire React application.

---

## 3. The CMDB Upload Flow (Authorization & RBAC)

This section details how authorization is enforced when an authenticated user uploads a CMDB file.

### Step 3.1: Frontend - Pre-Upload Checks & API Call

- **Component:** The file upload is handled by the UI in `src/pages/discovery/CMDBImport/`. The logic is primarily within the `useFileUpload` hook (`src/pages/discovery/CMDBImport/hooks/useFileUpload.ts`).
- **Client-Side RBAC:** Before the upload is even attempted, the `handleFileUpload` function performs these checks:
    1.  `if (!user)`: It ensures the user is authenticated.
    2.  `if (!hasContext && !isAdmin)`: It checks that a non-admin user has selected a Client and an Engagement. Admin users are exempt from this check and can proceed with a "demo" context.
- **API Call Preparation:**
    - The `useAuthHeaders` hook (`src/contexts/AuthContext/hooks/useAuthHeaders.ts`) is used to construct a set of HTTP headers for the API call.
    - These headers include:
        - `Authorization: Bearer <jwt_from_localStorage>`
        - `X-User-ID`: The user's ID.
        - `X-Client-Account-ID`: The ID of the currently selected client.
        - `X-Engagement-ID`: The ID of the currently selected engagement.
- **Sending the Request:** The file data is sent in a `POST` request to the `/data-import/store-import` backend endpoint with the prepared headers.

### Step 3.2: Backend - Context-Based Authorization

- **Endpoint:** The request is handled by `store_import_data` in `backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`.
- **Context Extraction:**
    - The endpoint uses the `Depends(get_current_context)` dependency.
    - The `get_current_context` function (from `backend/app/core/context.py`) is responsible for reading the `X-` headers from the request and populating a `RequestContext` object.
    - **Crucially, the backend does not have a "demo" fallback.** It relies entirely on the headers sent by the frontend. If they are missing, the context will be incomplete.
- **Server-Side Authorization Check:** The endpoint performs explicit validation on the extracted context:
    ```python
    if not client_account_id or not engagement_id:
        raise AppValidationError("Client account and engagement context required")
    if not user_id:
        raise AppValidationError("User ID is required for data import authentication")
    ```
    This is the core of the RBAC enforcement. It verifies not just that the user is logged in (`user_id` exists), but that they are operating within a valid client/engagement context. An attempt to upload data without selecting a context will be rejected at this stage.
- **Data Scoping:** All subsequent database operations are scoped using the IDs from the `RequestContext`. When a new `DataImport` record is created, it is stamped with the `client_account_id` and `engagement_id`, ensuring the uploaded data is tied to the correct tenant and cannot be accessed by other tenants.

---

## 4. Summary of RBAC Implementation

- **Authentication** is handled by a standard JWT-based login flow.
- **Authorization** is primarily achieved through **Context-Based Access Control**, which is a form of RBAC.
- A user's role (`admin` or `user`) provides broad permissions, mainly on the frontend (e.g., UI visibility, bypassing certain checks).
- The fine-grained, critical access control happens on the **backend** and is enforced by requiring `X-User-ID`, `X-Client-Account-ID`, and `X-Engagement-ID` headers for any API call that accesses or manipulates tenant-specific data.
- This ensures strict multi-tenancy and prevents data leakage, as all data is associated with and filtered by the context provided in the request. 