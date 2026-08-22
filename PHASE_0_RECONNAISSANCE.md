# THE TESSERACTIS — PHASE 0: RECONNAISSANCE & ARCHITECTURE REPORT

**Status:** No existing repository, codebase, or website was supplied. **This is a from-scratch implementation.** No original hackathon PDF ("Code-For-communities-PS") was attached to this conversation — flagged below rather than fabricated.

---

## SOURCE-PROVENANCE NOTICE (read this before anything else)

Two distinct source materials were referenced in this conversation, and they are **not the same thing**:

| Referenced source | Actually provided? | How I'm treating it |
|---|---|---|
| "Code-For-communities-PS" hackathon PDF | **No.** Never attached. | Marked `[SOURCE PDF UNAVAILABLE]` everywhere it would apply. I have not read it and will not invent its contents. |
| The Vineeth / Warangal / Nivaha Business App description | Yes — typed directly into chat by you | Treated as **user-provided problem narrative**, marked `[USER-PROVIDED]`. This is secondhand paraphrase of a source I haven't seen, not a verified PDF extract. |
| An existing Tesseractis codebase/website | **No.** | Confirmed from-scratch. Nothing was inspected because nothing exists to inspect. |

If the actual PDF exists and gets uploaded later, Section 2 below should be re-verified against it and corrected if anything conflicts.

---

## SECTION 1 — Understanding of The Tesseractis

The Tesseractis is a computer-vision-assisted decision-support tool: a user photographs mixed plastic waste, the system attempts to identify visible plastic/material categories, expresses calibrated confidence (including explicit "I don't know"), and gives responsible, non-authoritative recycling guidance. It is explicitly *not* a generic waste-management platform — depth on one workflow, not breadth of features.

## SECTION 2 — Source-derived requirements `[USER-PROVIDED, unverified against PDF]`

From your message: Vineeth runs a general store near Warangal; mixed plastic waste accumulates without an easy way to tell what's recyclable; the hackathon team's smallest useful slice is Vineeth photographing his shop's waste via the **Nivaha Business App**; track = Sustainable Cities & Climate Action.

**Explicitly stated (per your description):**
- Persona: shopkeeper in a village/semi-urban area near Warangal
- Pain point: daily mixed plastic waste, no easy way to sort recyclable vs. not
- Entry point: photo taken *within* the Nivaha Business App (i.e., Tesseractis may be a feature/flow inside a larger existing app, not necessarily its own branded consumer app)
- Track: Sustainable Cities & Climate Action

**Not stated (and I will not assume):** exact taxonomy of materials, target accuracy, whether Nivaha is a real app I can integrate with, dataset availability, whether authentication already exists in Nivaha, language/locale requirements, whether this must be a standalone web app or a module embedded in Nivaha.

**Open question requiring your confirmation:** Should THE TESSERACTIS be built as a **standalone web app** (as all prior prompts specify) or as a flow designed to be *embeddable inside* Nivaha? I'm proceeding with **standalone web app** since that's what every technical spec you've given explicitly describes, and treating "Nivaha" as backstory/context rather than an integration target — but this should be validated once/if the real PDF surfaces.

## SECTION 3 — Enhancements (mine, not source-claimed)

Everything else in your master specs — auth, RBAC, audit logging, admin console, model versioning, feedback loop, history, security hardening, CI/CD, structured AI response contracts — is an **engineering enhancement**, not a stated hackathon requirement. These are good decisions for a "production-style" demo but are explicitly mine/yours-by-instruction, not Vineeth's or the PDF's.

## SECTION 4 — What must NOT be added
Robotics/physical sorting, chemical composition certification, industrial automation, guaranteed municipal recycling instructions, social networking, marketplace, waste-pickup logistics, crypto/reward systems, blockchain, Kubernetes/Kafka/microservices, custom foundation-model training, vector databases (no need for this workflow).

## SECTION 5 — User personas
- **Primary:** Citizen/shopkeeper (Vineeth-like) — low technical sophistication, mobile-first, wants a fast yes/no/uncertain answer.
- **Secondary — Reviewer/Analyst:** reviews uncertain/flagged predictions and feedback.
- **Secondary — Admin:** manages categories/rules, users, audit/security events, model versions.
- **Secondary — ML Operator:** manages model versions/evaluation metadata (can be same role as Admin for MVP; separated in schema for future).

## SECTION 6 — Core user journey
Upload/capture photo → client pre-check → secure server-side validation → (optional) image-quality gate → AI analysis via provider abstraction → structured, schema-validated response → confidence/uncertainty decision → recommendation engine (separate from raw AI output) → result shown → user feedback captured → saved to history.

## SECTION 7 — Functional requirements (MVP)
Register/login/logout · upload or capture image · server-side validation · AI classification with confidence · explicit uncertainty path · recycling guidance (rule-engine, not model-invented) · save/view/delete history · feedback per scan · admin: view users, review feedback/uncertain scans, manage categories & rules, view audit log.

## SECTION 8 — Non-functional requirements
Security (OWASP-aligned) · privacy-by-default · accessibility (WCAG AA target) · mobile-first responsiveness · observability (structured logs, request IDs) · maintainability (modular monolith, typed code) · testability (mock AI provider so tests don't need a paid API) · runnable at every milestone.

## SECTION 9 — System architecture (logical)

```
Browser (Next.js/React/TS)
   ↓ HTTPS
Reverse proxy (dev: none/Caddy; prod: nginx/Traefik + TLS)
   ↓
FastAPI backend (Python)
   ├── Auth & session middleware
   ├── Authorization (RBAC) dependency layer
   ├── Rate limiter (Redis-backed)
   ├── Scan Service
   │     ├── Upload validator (magic bytes, decode check, size/dims)
   │     ├── Object storage (S3-compatible / MinIO dev)
   │     ├── AI Provider abstraction → Mock or Real vision provider
   │     ├── Response schema validator (Pydantic, strict)
   │     └── Recommendation/rules engine (independent of AI)
   ├── PostgreSQL (SQLAlchemy + Alembic)
   ├── Audit/security event logger
   └── Admin service
```

**Boundaries (hard rules):** frontend never touches Postgres directly; AI provider credentials exist only server-side; recommendation logic is a separate module the AI cannot directly author; audit logs are append-only and distinct from user-facing scan records.

## SECTION 10 — Frontend architecture
Next.js (App Router) + TypeScript + Tailwind. Structure: `app/` (routes), `components/` (dumb UI), `features/` (scan, auth, history, admin — feature-sliced), `lib/` (API client, fetch wrappers), `hooks/`, `types/` (mirrors backend Pydantic schemas). Auth state via httpOnly cookie session, never localStorage for tokens. Protected routes enforced client-side for UX only — real enforcement is server-side.

## SECTION 11 — Backend architecture
FastAPI, layered: `api/` (routers, thin) → `services/` (business logic) → `repositories/` (DB access) → `models/` (SQLAlchemy ORM) → `schemas/` (Pydantic request/response) → `security/` (hashing, session, RBAC deps) → `ai/` (provider interface + Mock/Real implementations) → `storage/` (object-storage abstraction) → `audit/`.

## SECTION 12 — Database ERD (description)
`users(id, email, password_hash, role, status, created_at, updated_at)` → `sessions(id, user_id, token_hash, expires_at, created_at)` → `scans(id, user_id, image_object_key, image_hash, status, model_version_id, created_at, completed_at, deleted_at)` → `scan_objects(id, scan_id, object_index, predicted_category_id, confidence, confidence_band, uncertainty_reason)` → `material_categories(id, code, label, description, active)` → `recycling_rules(id, category_id, locale, guidance_text, version, active)` → `feedback(id, scan_id, user_id, verdict, comment, created_at)` → `model_versions(id, provider, name, version, is_active, created_at)` → `audit_events(id, actor_user_id, action, target_type, target_id, metadata_json, created_at)` — append-only, no update/delete path exposed via API. All FKs indexed; soft-delete (`deleted_at`) on scans/users; UUID primary keys.

## SECTION 13 — API architecture
Versioned REST under `/api/v1/`. Consistent error envelope (`{error:{code,message,request_id}}`), never raw stack traces/DB errors. Every mutating/privileged route: auth dependency → RBAC dependency → Pydantic input validation → rate limit → service call → structured log. OpenAPI auto-generated via FastAPI.

## SECTION 14 — AI architecture
`VisionProvider` abstract interface: `analyze_image()`, `validate_response()`, `health_check()`. Two implementations: `MockVisionProvider` (deterministic, clearly labeled DEVELOPMENT MODE, used in dev/tests/demo-fallback) and `RealVisionProvider` (adapter to an actual vision-capable model API — provider swappable, e.g., could target Gemini/OpenAI-vision-class APIs; **no specific provider commitment made yet — needs your decision, see Assumptions**). Backend enforces a strict Pydantic schema on every AI response; failures are logged safely and surfaced to the user as a generic "could not analyze" state, never as raw provider output.

## SECTION 15 — Secure image-processing architecture
Client: basic type/size pre-check for UX only. Server (authoritative): max size + dimension caps, magic-byte/file-signature check (not just extension/MIME header), actual image decode via a safe library (e.g., Pillow with decompression-bomb guard), EXIF stripped by default, random UUID object key (never original filename), private bucket, signed short-lived URLs for any client-side display, rate limit per user/IP.

## SECTION 16 — Authentication architecture
Argon2id password hashing, server-side sessions (opaque token in httpOnly+Secure+SameSite cookie, hashed token stored server-side so DB leak ≠ session leak), configurable expiry, logout = server-side revocation. Email verification & password reset flows scaffolded structurally in MVP; can be stubbed (no real email sending) but the data model and endpoints exist so it's not fake — it's "not yet wired to an SMTP provider," clearly documented as such.

## SECTION 17 — Authorization / RBAC
Roles: `user`, `admin` at MVP (schema allows `reviewer`, `ml_operator` later without migration rewrite). Every privileged endpoint has a server-side dependency check — role is never trusted from a client-supplied field. Ownership check (scan.user_id == current_user.id) enforced on every scan read/delete.

## SECTION 18 — Threat model (summary — full detail in `THREAT-MODEL.md` at implementation time)

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Malicious/oversized upload | Medium | Medium | magic-byte + decode validation, size/dim caps, decompression-bomb guard |
| IDOR on scan/history endpoints | Medium | High | ownership check server-side on every read/delete |
| Prompt/image-text injection into AI | Medium | Medium | fixed system instruction, output schema validation, never treat in-image text as instructions |
| Auth/session attacks | Low-Med | High | Argon2id, httpOnly cookies, rate-limited login, session revocation |
| AI-provider outage | Medium | Low | provider abstraction + fallback to controlled "unavailable" state, never fake a result |
| Credential/secret leakage | Low | Critical | server-only env vars, `.env.example` never real secrets, no `NEXT_PUBLIC_` for keys |
| Privilege escalation via role tampering | Low | High | server-side RBAC dependency on every route, ignore client role claims |

## SECTION 19 — Security controls (implementation checklist)
Input validation (Pydantic strict), parameterized queries via SQLAlchemy ORM, RBAC dependencies, Argon2id hashing, httpOnly/Secure/SameSite cookies, CSRF token for cookie-auth mutations, restrictive CORS (explicit allow-list, no `*` with credentials), security headers (CSP, X-Content-Type-Options, Referrer-Policy, HSTS in prod, frame-ancestors none), rate limiting (Redis token bucket) on auth/upload/AI endpoints, audit logging of security-relevant events, safe generic error responses.

## SECTION 20 — Privacy architecture
EXIF stripped on ingest by default; images stored in private bucket, never public URLs; no image bytes in logs or audit records; retention configurable via `IMAGE_RETENTION_DAYS`/`ANALYSIS_RETENTION_DAYS`; account deletion removes scans/images/feedback/sessions, retains only audit records legally/operationally required (documented, not silently kept).

## SECTION 21 — Testing strategy
Unit: validators, confidence/uncertainty logic, auth, RBAC deps, upload validator. Integration: auth flow, upload→analyze→save, feedback, history, cross-user access denial (User A cannot read/delete User B's scan — explicit test). E2E: register→login→upload→analyze→result→feedback→history→logout. Security tests: IDOR, oversized/fake-MIME/malformed uploads, SQLi/XSS payloads, rate-limit enforcement, privilege escalation attempt. AI tests run entirely against `MockVisionProvider` so CI never requires a paid API key.

## SECTION 22 — DevSecOps strategy
Docker Compose for local dev (frontend, backend, postgres, redis, minio). `.env.example` with placeholder values only. Alembic migrations versioned in repo. Lint/format (ruff/black, eslint/prettier) + type checks (mypy, tsc) in CI, then unit → integration tests, then dependency audit (`pip-audit`/`npm audit`), then builds.

## SECTION 23 — Deployment architecture
Containerized modular monolith (not microservices). Reverse proxy terminates TLS in prod. Postgres and object storage never publicly exposed. Health/readiness endpoints (`/health`, `/ready`) return minimal non-sensitive status.

## SECTION 24 — Folder structure
```
tesseractis/
  frontend/  (app/, components/, features/, lib/, hooks/, types/, styles/)
  backend/app/  (api/, core/, models/, schemas/, services/, repositories/, security/, ai/, storage/, audit/, tests/)
  infrastructure/  (docker-compose.yml, nginx/, etc.)
  docs/  (ARCHITECTURE.md, SECURITY.md, API.md, DATABASE.md, AI.md, DEPLOYMENT.md, TESTING.md, THREAT-MODEL.md, PRIVACY.md, DEMO.md)
  .env.example
```

## SECTION 25 — Development phases (adopting your Phase 1–15 sequence)
1 Repo/dev-env scaffold → 2 DB + migrations → 3 Auth + RBAC → 4 Secure upload → 5 AI abstraction + mock provider → 6 Real provider integration → 7 Confidence/uncertainty logic → 8 Recommendation engine → 9 Frontend core UI → 10 History + feedback → 11 Admin console → 12 Security hardening → 13 Automated testing → 14 Observability/DevSecOps/CI → 15 Demo polish + docs.

## SECTION 26 — Acceptance criteria
A new user can register → log in → analyze a photo → see classification+confidence, or explicit uncertainty → get recycling guidance → save/view/delete history → submit feedback. An admin can log in → view flagged/uncertain scans → review feedback → view audit log → manage categories/rules. Every check runs against real DB state, not hard-coded JSON.

## SECTION 27 — Hackathon demo strategy
Skip login-first framing. Open straight to scan flow → upload a real mixed-waste photo → show classification + confidence + guidance → deliberately upload a blurry/ambiguous photo → show the system say "I don't know" instead of guessing → show it saved to history → briefly show admin view of the uncertain case. The "confident wrong answer avoided" moment is the strongest beat — plan the script around it.

## SECTION 28 — Known limitations (to state honestly, not hide)
No trained/fine-tuned plastic-classification model currently exists — `RealVisionProvider` will call a general vision-capable API, not a purpose-built resin classifier, unless/until a real dataset + evaluation is done. No accuracy numbers exist yet and none will be claimed until measured. No confirmed dataset. No confirmed real recycling-rule source (rules will start as clearly-labeled placeholder/configurable data, not authoritative municipal rules).

## SECTION 29 — Assumptions requiring your validation
1. **AI provider**: which vision-capable API should `RealVisionProvider` target (e.g., an OpenAI- or Gemini-class multimodal endpoint)? None chosen yet — I will not silently pick one and call it decided.
2. Standalone web app (not embedded in "Nivaha") — confirm this reading is correct.
3. No dataset currently available — confirmed, or do you have one?
4. Backend language/framework: proceeding with **Python/FastAPI** per your repeated stack preference (noted your second doc mentioned Node/NestJS as an alternative — defaulting to FastAPI since it appeared in both earlier specs and pairs naturally with a Python-based AI layer, unless you say otherwise).
5. Email sending (verification/reset) — stub only for MVP unless you have an SMTP/provider to wire up.

## SECTION 30 — FINAL IMPLEMENTATION ROADMAP
Proceed exactly per Section 25's 15 phases. Each phase, on your "START PHASE N" command, will: state what's changing → list affected files → implement in the actual filesystem here (not theoretical snippets) → run relevant tests/linting → report results → wait for the next command.

---

**PHASE 0 COMPLETE — READY TO BEGIN PHASE 1.**

Waiting on: (a) your answer to the 5 assumptions above (or "proceed with your defaults"), and (b) `START PHASE 1`.
