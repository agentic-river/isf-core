# 📘 Official API Convention Rules

This document outlines the architectural choices, design patterns, and tooling required for all APIs developed in this project. Our goal is **Developer Experience (DX), Type Safety, Performance, and Predictability.**

## 1. Paradigm & Versioning
*   **Architecture:** We use **RESTful APIs** backed by automatically generated OpenAPI (Swagger) specifications.
*   **Versioning:** All APIs must be versioned from day one via the URL path.
    *   🟢 **Good:** `/api/v1/users`
    *   🔴 **Bad:** `/api/users`

## 2. URL & Routing Conventions
URLs must represent **resources (nouns)**, not actions (verbs).

*   **Use Plurals:** Always use plural nouns for resources.
    *   🟢 **Good:** `GET /v1/users`, `GET /v1/invoices/{id}`
    *   🔴 **Bad:** `GET /v1/user`, `GET /v1/get_invoices`
*   **Custom Actions:** If a business action doesn't fit standard CRUD, append a verb to the specific resource.
    *   🟢 **Good:** `POST /v1/invoices/{id}/pay`
    *   🔴 **Bad:** `POST /v1/pay_invoice/{id}`
*   **Sensible Nesting:** Maximum of 2 levels deep. Use query parameters or direct ID lookups for deeper relationships.
    *   🟢 **Good:** `GET /v1/users/123/posts`
    *   🟢 **Good:** `GET /v1/comments/789` (Comment ID is already unique)
    *   🔴 **Bad:** `GET /v1/users/123/posts/456/comments/789`

## 3. HTTP Methods & Status Codes
Be strictly semantically correct with HTTP methods and status codes.

| Method | Purpose | Status Code (Success) | Status Code (Error) |
| :--- | :--- | :--- | :--- |
| **GET** | Read data (No state mutation) | `200 OK` | `404 Not Found` |
| **POST** | Create a new resource | `201 Created` | `400 Bad Request` |
| **PUT** | Completely replace a resource | `200 OK` | `400 / 404` |
| **PATCH** | Partially update a resource | `200 OK` | `400 / 404` |
| **DELETE** | Remove a resource | `204 No Content` | `404 Not Found` |

## 4. Data Formatting & Payloads
Always use `application/json`. 

*   **The Case Convention Bridge:** Python uses `snake_case`, but JavaScript/TypeScript frontends expect `camelCase`. 
    *   **Rule:** Pydantic models must be configured to consume and output **camelCase** automatically (`alias_generator = to_camel`), so the frontend never has to map properties manually.
    *   🟢 **Output:** `{ "firstName": "John", "createdAt": "2024-01-01T12:00:00Z" }`

*   **List Enveloping:** Arrays/Lists must never be returned raw. They must be enveloped in a standard pagination response.
    ```json
    {
      "data": [
        { "id": "123", "name": "Alice" }
      ],
      "meta": {
        "totalCount": 100,
        "page": 1,
        "limit": 20,
        "hasNextPage": true
      }
    }
    ```

## 5. Standardized Error Handling
Never expose raw backend exceptions (e.g., SQLAlchemy crashes) or HTML error pages to the frontend. All errors must be intercepted and formatted.

*   **Rule:** The API must return a predictable JSON error object.
    ```json
    {
      "error": {
        "code": "VALIDATION_FAILED",
        "message": "The provided data is invalid.",
        "details": [
          { "field": "email", "issue": "Must be a valid email address" }
        ]
      }
    }
    ```
*   **Common Error Codes:**
    *   `400`: Client validation failed.
    *   `401`: Missing or invalid authentication token.
    *   `403`: Authenticated, but lacks role/permissions.
    *   `404`: Resource does not exist.
    *   `500`: Unhandled backend exception (hide internal details).

## 6. Filtering, Sorting, and Pagination
All list (`GET`) endpoints must support pagination to ensure performance at scale. To prevent database overload, a single API request MUST NOT return more than 1000 records.

*   **Filtering:** Use exact query parameters (`GET /v1/users?role=admin&status=active`)
*   **Sorting:** Use `sortBy` and `order` (`GET /v1/users?sortBy=createdAt&order=desc`)
*   **Pagination:**
    *   *Standard:* Use `page` and `limit` for dashboards. (Limit must be $\le$ 1000)
    *   *Infinite Scroll:* Use `cursor` for heavy mobile/feed views.

## 7. Security & Authentication
*   **Stateless JWT:** Use JSON Web Tokens for authentication.
*   **Storage:** Tokens MUST be delivered via **HttpOnly, Secure cookies**. The frontend should never store tokens in `localStorage` to prevent XSS attacks.
*   **CORS:** Explicitly whitelist the frontend domains (e.g., `https://app.yourdomain.com`). Never use `*` in production.
*   **Rate Limiting:** Protect public endpoints (like `/login`, `/signup`, `/forgot-password`) with strict IP-based rate limiting.

## 8. Developer Experience (DX) & Type Safety
The boundary between the frontend and backend must be completely type-safe.

*   **Single Source of Truth:** FastAPI and Pydantic define the truth. FastAPI will automatically generate an `openapi.json` file.
*   **Frontend Generation:** The frontend team must NEVER write manual TypeScript interfaces for API responses. Instead, use tools like **Orval**, **openapi-ts**, or **openapi-fetch** to generate fully typed React Query/SWR hooks directly from the backend's OpenAPI schema.
*   **Validation:** Pydantic is our definitive validation engine. If it fails, a `400 Bad Request` standard error is automatically generated.

---

### ✅ Deployment Checklist
Before merging a new API route, ensure:
1. [x] It uses JSON with `camelCase` keys.
2. [x] The URL path is a plural noun (`/users` not `/user`).
3. [x] It returns the appropriate HTTP status code (e.g., `201` for creations).
4. [x] Lists are enveloped in `{"data": [...], "meta": {...}}`.
5. [x] Any known exceptions use the standardized `{"error": {...}}` format.
6. [x] Pydantic models are fully typed to ensure proper OpenAPI schema generation for the frontend team.



## 9. Python Type Hinting & Code Quality Guidelines

To ensure maximum compatibility with VS Code/Pylance (e.g., "Find All References", "Call Hierarchy", and Autocomplete), all Python code must adhere to strict type hinting rules.

**The Golden Rules for Parameters & Variables:**
1. **Mandatory Type Hints:** Every function/method parameter MUST have a type hint. Never leave bare parameters like `param=None`.
2. **Explicit Optionals:** Any parameter that defaults to `None` MUST be paired with `Optional[T]` (or `T | None` in Python 3.10+). 
   * 🟢 **Good:** `def execute(persistence_service: Optional[PersistenceService] = None)`
   * 🔴 **Bad:** `def execute(persistence_service=None)`
3. **Avoid `Any`:** Never use `Any` as a cop-out when a concrete type exists. Only use `Any` if the data is truly heterogeneous and cannot be typed.
4. **Import for Context:** When adding a type hint for a class from another module, you MUST add the import at the top of the file. This is the mechanism that allows IDEs to trace references across the codebase.
5. **Circular Dependencies:** If adding the import causes a circular dependency, use `from typing import TYPE_CHECKING` with a forward reference as a string:
   ```python
   from typing import TYPE_CHECKING, Optional
   
   if TYPE_CHECKING:
       from backend.services.persistence_service import PersistenceService
       
   def execute(persistence_service: Optional["PersistenceService"] = None):
       pass
   ```
