# BuildCost AI — Authentication Architecture & Security Tradeoffs

This document details the design choices, security tradeoffs, and architectural simplifications implemented in BuildCost AI's JWT-based authentication system.

---

## 1. Token Storage Strategy: `localStorage` vs `httpOnly` Cookies

### Implementation Choice
BuildCost AI stores the signed JWT access token in React state and persists it across page reloads using browser `localStorage` (`buildcost_jwt_token`).

### Security Tradeoff Analysis

| Metric | `localStorage` (Implemented) | `httpOnly` Cookies (Alternative) |
| :--- | :--- | :--- |
| **XSS Vulnerability** | **Vulnerable**: Any JavaScript running on the origin (e.g. via malicious package or injected script) can read `localStorage` and steal the token. | **Protected**: JavaScript cannot access `httpOnly` cookies under any circumstances. |
| **CSRF Vulnerability** | **Protected**: Browser does not automatically send `localStorage` tokens with cross-site HTTP requests. | **Vulnerable**: Browser automatically attaches cookies to cross-site requests unless protected by `SameSite` flags and CSRF tokens. |
| **Architecture Overhead** | **Low**: Fits decoupled frontend/backend SPA architectures (e.g. Vite dev server on `:5173`, FastAPI backend on `:8000`) without complex cookie domain configuration. | **High**: Requires same-origin reverse proxy or explicit CORS credentials configuration (`Access-Control-Allow-Credentials: true`). |

### Architectural Rationale
For the scope of this engineering project, `localStorage` provides a clean, decoupled authentication workflow. The security vulnerability to XSS is explicitly acknowledged as a known tradeoff. In a production deployment serving sensitive enterprise financial data, the app would transition to `httpOnly`, `SameSite=Strict` cookies with CSRF token validation.

---

## 2. Token Expiration: 24-Hour Access Tokens vs. Refresh Tokens

### Implementation Choice
Access tokens are signed using HMAC-SHA256 (`HS256`) with a 24-hour expiration window (`exp = now + 24 hours`).

### Simplification Disclosure
- **Production Standard**: Production authentication systems utilize short-lived access tokens (e.g., 15 minutes) paired with long-lived refresh tokens stored securely in `httpOnly` cookies. Refresh token rotation allows immediate revocation of compromised sessions.
- **Project Simplification**: Implementing refresh token rotation adds stateful token tracking and database overhead without altering the core per-engineer project scoping concepts. A 24-hour access token is a deliberate simplification for developer experience and interview discussion.

---

## 3. Legacy Unowned Projects (`user_id IS NULL`)

### Implementation Choice
The `migrate_add_auth.py` script adds a nullable `user_id` column to the `projects` table. Projects created prior to the auth feature rollout have `user_id IS NULL`.

Going forward:
- `GET /projects` filters explicitly by `WHERE user_id = current_user.id`.
- Single-project routes (`GET /projects/{id}`, `PATCH`, `DELETE`, `/forecast`, `/phases/*`) enforce ownership check `project.user_id == current_user.id`.
- Consequently, legacy unowned projects (`user_id IS NULL`) are isolated and inaccessible through normal authenticated user routes.

### Production Comparison
In an enterprise production migration:
1. An admin migration script would reassign legacy projects to designated organizational owners or system admin accounts.
2. Unclaimed projects would be assigned to a default workspace or prompted for claim via email verification.
For this project, isolating legacy unowned projects is an intentional choice.

---

## 4. Key Security Practices Implemented

### Password Hashing (`passlib` + `bcrypt`)
- Passwords are never stored in plaintext or hashed using fast general-purpose algorithms (MD5/SHA256).
- We use `passlib` with `bcrypt`, an adaptively slow algorithm incorporating cryptographic salts to resist dictionary and brute-force GPU attacks.
- Passwords are validated before storage (min 6 characters) and `hashed_password` is excluded from all API response models.

### User Enumeration Protection
- When authenticating via `POST /auth/login`, invalid credentials return a generic `401 Unauthorized` response with detail `"Invalid email or password"`.
- Distinguishing between "User not found" and "Incorrect password" would allow malicious actors to harvest valid registered email addresses.

### Project Ownership Checks & Information Leakage Prevention
- Authentication check (`get_current_user`) verifies identity.
- Ownership check (`project.user_id == current_user.id`) verifies authorization.
- Accessing a project owned by another user yields **`403 Forbidden`** (not `404 Not Found`), distinguishing authorization failure while protecting project privacy.

### Stateless Calculation Preservation
- One-off procurement forecasts (`POST /predict-optimal-build-window`) and standalone vendor quote checks (`POST /check-fair-price` without `project_id`) remain publicly accessible without authentication.
- This preserves the "casual exploratory tool" UX while securing persistent project management features behind authentication.
