# Auth and RBAC Workflow Analysis Report

## User Flow: Homepage to Dashboard and CMDB Import

### Frontend Touchpoints
1. **Homepage**: `src/pages/Home.tsx`
2. **Login Page**: `src/pages/Login.tsx`
   - Uses `AuthContext` from `src/contexts/AuthContext.tsx`
   - Calls `authApi.login` from `src/lib/api/auth.ts`
3. **Dashboard**: `src/pages/Dashboard.tsx`
4. **CMDB Import**: `src/components/cmdb/CMDBImporter.tsx`

### Backend Touchpoints
1. **Authentication Handler**: `app/api/v1/auth/handlers/authentication_handlers.py`
   - `login_user` function
2. **Authentication Service**: `app/services/auth_services/authentication_service.py`
   - `authenticate_user` method
3. **User Model**: `app/models/client_account.py`
   - `User` class

### Database Touchpoints
1. `users` table

### Data Flow
1. Frontend sends email and password to `/api/v1/auth/login`.
2. Backend queries the `users` table by email.
3. Backend verifies password (if hash exists).
4. Backend updates `last_login` and `login_count`.
5. Backend returns a token and user data.
6. Frontend stores token and user data in `localStorage` and context.
7. Frontend navigates to dashboard.

### Detailed Parameter Flow

### 1. Frontend Login (Login.tsx)
- **Input Parameters**: 
  - `email: string` 
  - `password: string`
- **Output**: Calls `AuthContext.login(email, password)`

### 2. AuthContext Handling (AuthContext.tsx)
- **Parameters Received**: `email`, `password`
- **API Call**: `authApi.login({ email, password })`
- **Expected Response Shape**:
  ```ts
  {
    user: {
      id: string,
      name: string,
      email: string,
      // ... other fields
    },
    token: string,
    client: { /* client data */ },
    engagement: { /* engagement data */ },
    session: { /* session data */ }
  }
  ```

### 3. API Client (auth.ts)
- **Request**:
  ```ts
  POST /api/v1/auth/login
  {
    "email": "user@example.com",
    "password": "secretpassword"
  }
  ```
- **Expected Response**:
  ```ts
  {
    status: "success",
    message: string,
    user: UserData,
    token: string
  }
  ```

### 4. Backend Handler (authentication_handlers.py)
- **Request Model**:
  ```python
  class LoginRequest(BaseModel):
      email: str
      password: str
  ```
- **Calls**: `AuthenticationService.authenticate_user(login_request)`

### 5. Authentication Service (authentication_service.py)
- **Database Query**:
  ```python
  select(User).where(User.email == login_request.email)
  ```
- **Password Verification**:
  ```python
  bcrypt.checkpw(login_request.password.encode(), user.password_hash.encode())
  ```
- **Response Model**:
  ```python
  LoginResponse(
      status="success",
      message="Login successful",
      user=user_data,
      token=token
  )
  ```

### 6. Database Schema (client_account.py)
- **Relevant Columns**:
  - `email: str`
  - `password_hash: str`
  - `last_login: datetime`
  - `login_count: int`
  - `is_active: bool`

### Identified Issues
1. **Token Generation**: The backend returns a placeholder token (`db-token-<id>-<uuid>`). This is not a JWT and will break authenticated requests.
2. **Password Verification**: The code currently does not verify the password against the hash. It only checks if the user exists and is active.

### Parameter Mismatch Issues
1. **Frontend/Backend Token Format**
   - Backend: `db-token-{user.id}-{uuid}`
   - Frontend: Expects JWT with specific claims

2. **Context Data Missing**
   - Backend response missing `client`, `engagement`, `session` data
   - Frontend expects full context initialization

3. **Security Gap**
   - Passwords transmitted in plaintext
   - Recommendation: Implement HTTPS and frontend hashing

### Recommendations
1. Implement JWT token generation using a library like `python-jose`.
2. Add password verification using `bcrypt`.
3. Update the frontend to handle JWT tokens.
4. Implement JWT token generation in backend
5. Add client/engagement context to login response
6. Implement password hashing in frontend before transmission
7. Add HTTPS enforcement

### Verification Checklist
- [ ] Validate password hashing flow
- [ ] Test JWT token decoding in frontend
- [ ] Confirm context data in dashboard
- [ ] Verify HTTPS enforcement in production
