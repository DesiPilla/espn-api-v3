# Doritostats Main Site — Redesign Master Plan

**Status:** Planning  
**Branch:** `huge-redesign`  
**Scope:** Main site only (fantasy_stats app). The `playoff_pool/` feature is explicitly excluded.

---

## Overview

Three-phase redesign of the main fantasy football stats site:

1. **Phase 1 — Authentication:** Users log in to see and manage their own leagues
2. **Phase 2 — UI Overhaul:** Modern, professional-grade visual design
3. **Phase 3 — New Features:** Stats, graphs, and additional functionality (scoped later)

---

## Current Stack (Baseline)

| Layer | Technology |
|---|---|
| Frontend | React 19, React Router v6, Axios |
| Styling | Plain CSS + CSS Modules (no framework) |
| Backend | Django 5.1.2, Django REST Framework |
| Auth (main site) | **None** — no login required |
| Auth (playoff pool) | DRF Token Auth (reference implementation) |
| Database | PostgreSQL via Railway |
| Deployment | Railway (Gunicorn) |

---

## Phase 1 — Authentication System

**Goal:** Users create accounts, log in, and see only their own leagues.

### 1.1 Backend

**Decision:** Use Django's built-in `User` model + DRF Token Auth (consistent with what playoff_pool already does).

#### Tasks

- [x] **1.1.1** Add auth endpoints to `fantasy_stats` app (or a shared `accounts` app)
  - `POST /api/auth/register/` — email + password
  - `POST /api/auth/login/` — returns token
  - `POST /api/auth/logout/` — invalidates token
  - `GET  /api/auth/me/` — returns current user info
- [x] **1.1.2** Associate `LeagueInfo` with a `User`
  - Add `user = ForeignKey(User, on_delete=CASCADE)` to `LeagueInfo`
  - Write migration (`0007_add_user_to_leagueinfo`)
  - Existing rows: `user` is nullable — orphaned rows can be claimed later
- [x] **1.1.3** Update `fantasy_stats` views to filter leagues by `request.user`
  - All league endpoints return only leagues owned by the authenticated user
  - Added `@token_auth_required` decorator (in `backend/accounts/decorators.py`) to plain Django views
- [x] **1.1.4** Implement password reset flow
  - `POST /api/auth/password-reset/` — sends email with reset link
  - `POST /api/auth/password-reset/confirm/` — validates token and sets new password
  - Uses Django's `default_token_generator`; link points to `FRONTEND_URL` env var
- [x] **1.1.5** Decide on account model scope
  - Email + password; `username = email` internally; custom `EmailBackend` auth backend
  - Google login deferred to Phase 3

### 1.2 Frontend

#### Tasks

- [x] **1.2.1** Create `AuthContext` for the main site
  - `frontend/src/components/AuthContext.js` — `AuthProvider` + `useAuth` hook
  - Token stored in `localStorage` under `doritostatsToken`
  - On init: validates stored token with `GET /api/auth/me/`
  - Provides: `user`, `token`, `isAuthenticated`, `loading`, `login()`, `logout()`, `register()`
- [x] **1.2.2** Build Login page (`/login`)
  - `frontend/src/pages/LoginPage.js`
  - Email + password form; on success redirects back to `location.state.from`
  - "Forgot password?" link; link to Register
- [x] **1.2.3** Build Register page (`/register`)
  - `frontend/src/pages/RegisterPage.js`
  - Email + password + confirm password; link to Login
- [x] **1.2.4** Build Password Reset pages
  - `frontend/src/pages/PasswordResetPage.js` — request form at `/password-reset`
  - `frontend/src/pages/PasswordResetConfirmPage.js` — new password form at `/password-reset/confirm?uid=…&token=…`
- [x] **1.2.5** Implement protected routes
  - `frontend/src/components/ProtectedRoute.js` — redirects to `/login` with `state.from`
  - All fantasy_stats routes wrapped in `<ProtectedRoute>`
- [x] **1.2.6** Update `api.js` to attach Bearer token to all requests
  - `getAuthHeaders()` helper reads `doritostatsToken` from localStorage
  - Both `safeFetch` and `fetchWithRetry` merge auth headers automatically
  - 401 response in `safeFetch` clears token and redirects to `/login`
- [x] **1.2.7** Update `Header.js` to show login/logout and user info
  - Shows `user.email` + "Sign out" button when authenticated
  - Shows "Sign in" + "Register" links when not
- [x] **1.2.8** Replace `LeagueSelector.js` / `NewLeagueForm.js` with a proper "My Leagues" dashboard
  - `frontend/src/pages/DashboardPage.js` — replaces `HomePage` at `/`
  - Leagues grouped by year; each has a "Remove" (soft-delete) button
  - Collapsible "Add League" form with ESPN credentials
  - Includes `ReturningLeagueSelector` for season-over-season copy
  - Backend: `leagues_data` now includes `id` field; `DELETE /api/league/<pk>/delete/` endpoint added

### 1.3 Infrastructure / Security

- [x] **1.3.1** Audit CSRF settings for token auth coexistence
  - Plain Django views with `@token_auth_required` were subject to `CsrfViewMiddleware` and returned 403 on POSTs
  - Fixed by setting `wrapper.csrf_exempt = True` inside the decorator (token auth is header-based, not cookie-based, so CSRF is not needed)
- [x] **1.3.2** Ensure `SECURE_SSL_REDIRECT` and `SESSION_COOKIE_SECURE` are on in production
  - Added `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` gated on `not DEBUG` in `settings.py`
- [x] **1.3.3** Add `DEFAULT_AUTHENTICATION_CLASSES` for main site to Railway env
  - Already set in `settings.py` (TokenAuthentication + SessionAuthentication); no Railway override needed
- [x] **1.3.4** Confirm Railway environment variables include email credentials for password reset
  - Railway already had `RESEND_API_KEY` + `SENDER_EMAIL`; updated `settings.py` to use Resend SMTP relay (`smtp.resend.com:587`)
  - Fixed `accounts/views.py` to send from `DEFAULT_FROM_EMAIL` instead of `EMAIL_HOST_USER`
  - Added `FRONTEND_URL=https://doritostats.up.railway.app` to Railway (was missing; password-reset links pointed to localhost)

### 1.4 Testing

- [x] **1.4.1** Flesh out and implement a working test suite for all Phase 1 backend auth endpoints and views
  - 84 tests, all passing — run with: `python manage.py test backend.tests.test_auth --settings=backend.doritostats.test_settings`
  - Covers: register, login, logout, `/me`, password reset request, password reset confirm
  - Covers: `@token_auth_required` decorator behavior (valid token, missing token, invalid token)
  - Covers: league filtering by user (authenticated user only sees their own leagues)
  - Uses Django's `TestCase` + DRF's `APIClient`; email sending is mocked
- [ ] **1.4.2** Add frontend integration tests (Playwright) for auth flows
  - Register → login → dashboard → logout
  - ProtectedRoute redirect when unauthenticated
  - Password reset request form

---

## Phase 2 — UI Overhaul

**Goal:** Replace the plain HTML/CSS interface with a sleek, modern, professional design.

### 2.1 Design System Decisions

These need to be decided before coding begins:

- [ ] **2.1.1** **CSS Framework:** Tailwind CSS (utility-first, great DX with React, no style conflicts)
- [ ] **2.1.2** **Component Library:** shadcn/ui (built on Tailwind + Radix, fully customizable, copy-paste model)
- [ ] **2.1.3** **Color Palette & Theme:** Define primary, secondary, accent, background, surface, and text colors
  - Consider dark mode from the start (shadcn/ui supports it natively)
- [ ] **2.1.4** **Typography:** Choose a font pairing (e.g., Inter for UI, a display font for headings)
- [ ] **2.1.5** **Icon Library:** Lucide (ships with shadcn/ui) or Heroicons

### 2.2 Infrastructure for Styling

- [ ] **2.2.1** Install Tailwind CSS into the React project
- [ ] **2.2.2** Install and initialize shadcn/ui
- [ ] **2.2.3** Migrate or delete existing CSS files (keep module files alive until their components are migrated)
- [ ] **2.2.4** Set up a design token file (colors, spacing, border radii) in Tailwind config

### 2.3 New Page Architecture

The current page structure will be reorganized around authentication:

| Route | Page | Description |
|---|---|---|
| `/` | **Landing Page** | Public marketing/intro page for logged-out users |
| `/login` | **Login Page** | Phase 1 deliverable |
| `/register` | **Register Page** | Phase 1 deliverable |
| `/dashboard` | **My Leagues Dashboard** | Logged-in home; shows all user's leagues |
| `/league/:year/:id` | **League Hub** | Stats dashboard for one league (redesigned LeaguePage) |
| `/league/:year/:id/records` | **Season Records** | Redesigned LeagueRecordsPage |
| `/league/:year/:id/simulation` | **Playoff Simulation** | Redesigned LeagueSimulationPage |
| `/awards` | **Awards** | Redesigned AwardsPage |

### 2.4 Component Rebuild List

#### Layout / Shell
- [ ] **2.4.1** `Header` — Top nav bar with logo, nav links, user avatar/login button
- [ ] **2.4.2** `Sidebar` (optional) — Collapsible sidebar for league navigation
- [ ] **2.4.3** `Footer` — Minimalist footer
- [ ] **2.4.4** `Layout` — Page wrapper with consistent padding/max-width

#### Core UI Components (shadcn/ui)
- [ ] **2.4.5** `Button` — Replace all ad-hoc buttons
- [ ] **2.4.6** `Card` — Container for stats widgets
- [ ] **2.4.7** `Table` — Replace all tables (standings, rankings, records, etc.)
- [ ] **2.4.8** `Tabs` — League page section navigation
- [ ] **2.4.9** `Select` / `Dropdown` — Week/season selector
- [ ] **2.4.10** `Modal` / `Dialog` — Replace custom modal
- [ ] **2.4.11** `Badge` — For tags, statuses, awards
- [ ] **2.4.12** `Spinner / Skeleton` — Loading states
- [ ] **2.4.13** `Toast` — Notifications (errors, success messages)

#### Pages (full rewrites)
- [ ] **2.4.14** Landing Page — Hero section, feature highlights, call to action
- [ ] **2.4.15** My Leagues Dashboard — Card grid of user's leagues with quick stats
- [ ] **2.4.16** League Hub Page — Tabbed interface: Standings | Power Rankings | Luck Index | Playoff Odds | Box Scores
- [ ] **2.4.17** League Records Page — Season records with modern table/card layout
- [ ] **2.4.18** Simulation Page — Playoff odds visualization
- [ ] **2.4.19** Awards Page — Weekly and season awards display

### 2.5 Mobile / Responsive

- [ ] **2.5.1** Ensure all pages are responsive on mobile (Tailwind responsive utilities)
- [ ] **2.5.2** Collapsible nav on mobile
- [ ] **2.5.3** Horizontal-scroll or card-based tables on mobile

---

## Phase 3 — New Features

**Status:** Not yet scoped. Will be tackled in a dedicated planning session.

**Planned work for that session:**
1. Audit all backend utility functions (`backend/src/doritostats/`) to inventory what data is computable but not yet surfaced in the UI
2. Deep dive of the current frontend to identify gaps
3. Competitor analysis: Sleeper, ESPN Fantasy, Yahoo Fantasy, Underdog — what do they show that we don't?
4. Brainstorm roadmap: charts, graphs, head-to-head history, power rankings history, season projections, etc.

---

## Decisions Log

| # | Decision | Rationale |
|---|---|---|
| D1 | Token auth (DRF) for main site | Consistent with playoff_pool pattern; simpler than JWT for this use case |
| D2 | Tailwind CSS | No style conflicts, great DX, well-supported with React |
| D3 | shadcn/ui | Copy-paste model means no version lock-in; built on Radix for accessibility |
| D4 | Keep playoff_pool untouched | Out of scope for this redesign |
| D5 | Public landing page at `/`, dashboard behind auth at `/dashboard` | Better UX for new visitors; clean separation of concerns |
| D6 | New `accounts` app for auth | Keeps auth separate from stats; clean home for shared auth if playoff_pool is ever unified |
| D7 | `username = email` internally on Django User | No custom User model; email-based login via `EmailBackend`; Google login via django-allauth later |
| D8 | Nullable `user` on `LeagueInfo` for existing rows | Orphaned rows can be "claimed" later; no fake system user needed |
| D9 | `@token_auth_required` decorator for plain Django views | Avoids converting existing views to DRF; reads `Authorization: Token` header and sets `request.user` |

*Add decisions here as they are made during implementation.*

---

## Session Notes

*Append notes here at the end of each Claude session to preserve context.*

### Session 1 — 2026-04-09
- Kicked off redesign planning
- Explored full codebase; confirmed no auth exists on main site
- Created this document as the master tracking plan
- Phases 1 and 2 fully scoped; Phase 3 deferred
- No code written yet — pure planning session

### Session 3 — 2026-04-09

- Completed all of Phase 1.2 (Frontend)
- Created `frontend/src/components/AuthContext.js` (AuthProvider + useAuth), `ProtectedRoute.js`
- Created `LoginPage`, `RegisterPage`, `PasswordResetPage`, `PasswordResetConfirmPage` in `frontend/src/pages/`
- Created `DashboardPage.js` — replaces `HomePage` at `/`; shows leagues grouped by year with remove buttons and collapsible add-league form
- Updated `api.js`: `getAuthHeaders()` helper; auth headers merged in `safeFetch` and `fetchWithRetry`; 401 → clears token + redirects to `/login`
- Updated `Header.js`: shows logged-in user email + Sign out button
- Updated `App.js`: wrapped in `AuthProvider`; added auth routes; all fantasy_stats routes wrapped in `ProtectedRoute`
- Backend additions: `leagues_data` now includes `id` field; `delete_league` view + `POST /api/league/<pk>/delete/` URL added
- Phase 1.3 (Infrastructure/Security) still pending

### Session 4 — 2026-04-10

- Ran Playwright verification of all Phase 1.1 + 1.2 changes (after rebuilding static assets)
- All auth flows confirmed working: register, login, logout, error handling, ProtectedRoute redirect, dashboard, Add League form
- Completed Phase 1.3 (Infrastructure/Security):
  - **1.3.1**: Discovered `@token_auth_required` POST views returned 403 (CSRF). Fixed by setting `wrapper.csrf_exempt = True` in the decorator — token auth is header-based so CSRF is redundant
  - **1.3.2**: Added `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` to `settings.py` gated on `not DEBUG`
  - **1.3.3**: `DEFAULT_AUTHENTICATION_CLASSES` was already in `settings.py`; nothing to do
  - **1.3.4**: Railway had `RESEND_API_KEY` + `SENDER_EMAIL` but no `FRONTEND_URL`. Updated `settings.py` email config to use Resend SMTP relay. Fixed `accounts/views.py` to use `DEFAULT_FROM_EMAIL` instead of `EMAIL_HOST_USER`. Added `FRONTEND_URL=https://doritostats.up.railway.app` to Railway

### Session 5 — 2026-04-09

- Added Phase 1.4 (Testing) to the plan
- An initial test suite was written but is very long and all tests fail — needs to be diagnosed and rewritten from scratch
- Testing work deferred; Phase 1 is otherwise complete

### Session 2 — 2026-04-09
- Completed all of Phase 1.1 (Backend)
- Created `backend/accounts/` app: `EmailBackend`, `token_auth_required` decorator, register/login/logout/me/password-reset endpoints
- Added nullable `user` FK to `LeagueInfo`; migration `0007_add_user_to_leagueinfo` applied
- Updated `leagues_data`, `league_input`, `copy_old_league`, `get_league_details`, `get_distinct_leagues_previous_year` to require auth and filter by user
- Fixed `get_cached_league` to use `.filter().first()` (handles multiple `LeagueInfo` rows per league once multiple users exist)
- All 5 auth endpoints smoke-tested and working
- `FRONTEND_URL` env var required in Railway for password-reset emails (defaults to `http://localhost:3000`)
