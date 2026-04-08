---
title: Align Zeabur checklist with repo and harden API base URL
type: refactor
status: completed
date: 2026-04-08
---

# Align Zeabur checklist with repo and harden API base URL

## Overview

Update the Zeabur deployment checklist so it matches the current repository (dependencies file and frontend API base behavior already present). Harden `VITE_API_BASE_URL` handling in the frontend API client so common copy-paste mistakes (whitespace, multiple trailing slashes) still produce a valid request URL. **Do not** change `backend/requirements.txt` or dependency versions (explicit product decision).

## Problem Frame

Readers following `docs/plans/2026-04-08-zeabur-deploy-checklist.md` may believe `backend/requirements.txt` is still missing and that `frontend/src/services/api.js` still needs a Vite env implementation—both are already in the repo. Separately, the API URL helper only strips a single trailing slash, which is slightly brittle for hand-entered Zeabur variables.

## Requirements Trace

- R1. Checklist prose must state that `backend/requirements.txt` exists in-repo and that Zeabur Python build steps refer to that file (no “可能尚無此檔” or “先建立檔案” framing unless clearly marked historical).
- R2. Section 0.2 must describe **current** behavior: `VITE_API_BASE_URL` is already read in `frontend/src/services/api.js`; steps should focus on Zeabur variables and rebuild, not “請在 api.js 實作”.
- R3. “Next Steps” must not imply a future PR is required solely to add requirements or wire the env var when those are already landed.
- R4. `removeBackgroundApiUrl()` (or equivalent) must trim surrounding whitespace on `VITE_API_BASE_URL`, then remove **all** trailing slashes before concatenating `/api/remove-background`.
- R5. When the env var is empty or whitespace-only after trim, behavior must remain: use relative `/api/remove-background` for local Vite proxy (unchanged invariant).

## Scope Boundaries

- **In scope:** `docs/plans/2026-04-08-zeabur-deploy-checklist.md`, `frontend/src/services/api.js`.
- **Out of scope:** Pinning or changing Python package versions in `backend/requirements.txt`; README edits unless discovered as strictly necessary for consistency (defer unless checklist duplicates README—prefer minimal checklist edits only).

## Context & Research

### Relevant Code and Patterns

- `frontend/src/services/api.js` — `removeBackgroundApiUrl()` uses `(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')` today; only one trailing slash removed, no trim.
- `docs/plans/2026-04-08-zeabur-deploy-checklist.md` — §0.1 lines 15–17 still say the requirements file may be missing; §0.2 step 1 reads like an unimplemented change; §Next Steps still references opening a PR to land requirements and env wiring.

### Institutional Learnings

- No matching entry found under `docs/solutions/` for this topic (none required for this scope).

### External References

- None required; Vite env semantics are established project context.

## Key Technical Decisions

- **Documentation vs code drift:** Fix the checklist to reflect repo truth instead of adding redundant README duplication in this pass.
- **URL normalization:** Apply `trim` then strip one-or-more trailing slashes via a single regex on the suffix (e.g. `/+$/`), avoiding manual loops; preserve empty → relative URL behavior.
- **No version pins:** Per stakeholder request, requirements file content stays unpinned in this work.

## Open Questions

### Resolved During Planning

- **Pin dependencies?** No — explicitly excluded.

### Deferred to Implementation

- None expected; if checklist cross-links to README, verify one sentence still matches `README.md` Zeabur section after edits (quick read during implementation).

## Implementation Units

- [x] **Unit 1: Refresh Zeabur deployment checklist copy**

**Goal:** Remove misleading “file missing” and “future PR” language; align §0.1–0.2 and Next Steps with the current repo.

**Requirements:** R1, R2, R3

**Dependencies:** None

**Files:**

- Modify: `docs/plans/2026-04-08-zeabur-deploy-checklist.md`

**Approach:**

- §0.1: State that `backend/requirements.txt` is **already** in the repository and lists runtime dependencies for Zeabur `pip install -r requirements.txt`; keep the example block as reference of **contents shape**, not as “create this file from scratch” (adjust intro sentences accordingly).
- §0.2: Reframe step 1 as **verification** that `frontend/src/services/api.js` uses `VITE_API_BASE_URL`, or fold into a short “已實作” note plus Zeabur variable + rebuild steps (items 2–3).
- Next Steps: Replace “若要把…寫進 repo…開 PR” with directions appropriate for **follow-on work** (e.g. optional CI, operational hardening) or a simple pointer to `/ce:work` / Zeabur console steps—without claiming requirements or env wiring are still absent.

**Patterns to follow:**

- Existing checklist structure and repo-relative paths only.

**Test scenarios:**

- Test expectation: none — documentation-only; manually re-read the edited sections for internal consistency (no contradictory “尚未加入” phrasing).

**Verification:**

- A new reader can follow the doc without believing `requirements.txt` or `VITE_API_BASE_URL` support is still TODO in the repo.

---

- [x] **Unit 2: Normalize production API base URL in `api.js`**

**Goal:** Make `VITE_API_BASE_URL` tolerant of whitespace and multiple trailing slashes.

**Requirements:** R4, R5

**Dependencies:** Unit 1 may land in parallel; no code dependency between units.

**Files:**

- Modify: `frontend/src/services/api.js`
- Test: none in repo today

**Approach:**

- Derive a string from `import.meta.env.VITE_API_BASE_URL` (treat missing as empty).
- `.trim()`; if result is empty, use relative `/api/remove-background`.
- Otherwise strip trailing slashes with a regex matching one-or-more `/` at end; concatenate `${base}/api/remove-background`.

**Patterns to follow:**

- Keep the small helper style already used in the file; no new dependencies.

**Test scenarios:**

- Happy path — `VITE_API_BASE_URL` unset: request URL is `/api/remove-background` (local dev proxy unchanged).
- Edge case — value `  https://api.example.com  `: effective base `https://api.example.com`, final URL `https://api.example.com/api/remove-background`.
- Edge case — value `https://api.example.com///`: final URL `https://api.example.com/api/remove-background` (no duplicated slashes before `api`).
- Edge case — value whitespace-only: falls back to relative `/api/remove-background`.

**Verification:**

- Manual: `npm run dev` with unset env; `npm run build` / `preview` with sample env values above and confirm Network tab target URL (or console log during dev if needed).

## System-Wide Impact

- **Interaction graph:** Only the remove-background fetch URL construction is affected; `postForBlob` unchanged.
- **Error propagation:** Unchanged; malformed **scheme** or host is still user/config error—out of scope for this micro-hardening.
- **State lifecycle risks:** None.
- **API surface parity:** N/A.
- **Integration coverage:** Browser fetch to backend; manual verification sufficient given no test harness.
- **Unchanged invariants:** Relative `/api/...` when env empty; request body and error parsing unchanged.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Over-aggressive trimming breaks intentional rare formats | Only trim ASCII whitespace as per `String.prototype.trim`; document Zeabur values as normal HTTPS URLs. |

## Documentation / Operational Notes

- After Unit 1, optional one-line sync with `README.md` Zeabur section if any duplicated claims remain (only if implementer notices direct contradiction).

## Sources & References

- Related doc: [docs/plans/2026-04-08-zeabur-deploy-checklist.md](2026-04-08-zeabur-deploy-checklist.md)
- Related code: `frontend/src/services/api.js`
