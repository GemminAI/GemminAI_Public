# Release Notes — GemminAI

---

## v1.2.1 — 2026-04-11

**Codename: "First Light"**  
*gemminai.com goes live on Cloud Run.*

### Infrastructure
- Migrated frontend from Vercel to **Google Cloud Run** (`asia-northeast1`)
- Established `api.gemminai.com` as dedicated Laravel upstream endpoint
- Resolved BFF self-reference loop (`laravelUpstream.ts` — `LARAVEL_ALLOW_SELF_HOST` guard)
- SSL certificate provisioned via Cloud Run domain mapping
- Restored `narrative-generator` Cloud Function (gen2) — `google-genai` dependency fix

### Pipeline
- Confirmed end-to-end narrative generation: RSS → Gemini 2.0 Flash → Laravel → Cloud Run
- `success=6/6` (6-country narrative generation per event) verified in production
- T25 `state_hash` invariance confirmed across JP/EN language switch (§8.1 of NQ 2.0.1)

### Research
- Added `benchmark_v2.py` — evidence generation script for NQ 2.0.1 empirical claims
- Added `measurement_plan.md` — computational specification for V1/V2/V3 verifications

---

## v1.2.0 — 2026-04-08

**Codename: "Design Migration + EventID Intelligence + JP/EN Switch"**

### Frontend
- Full design migration from Vite to Next.js 15 App Router
- Noto Serif JP typography, CSS variable theming
- JP/EN language switch with T25 hash invariance display
- `LangSwitch.tsx` Server Component

### Backend
- `resolveEventId()` — cosine similarity-based event deduplication (Laravel)
- `event_intelligence_logs` table — embedding judgment tracking
- `embed_text()` integrated into Cloud Functions narrative pipeline

---

## v1.1.0 — 2026-04-06

**Codename: "Next.js Migration"**

### Infrastructure
- Next.js 15 App Router migration initiated (`gemminai-next`)
- BFF (Backend for Frontend) layer implemented
- Vercel deployment confirmed
- DUNS number acquired (698915261)
- Google for Startups Cloud Program application submitted

### Protocol
- Acta AIIE Protocol v1.0.0 ratified
- RFC-0001 ~ RFC-0004 committed to Vault

---

## v1.0.7 — 2026-04-03

**Codename: "Language Lock"**

- Narrative generation language enforcement (JP/EN/CN per country)
- DB direct connection disabled — Laravel API pipeline unified
- `backbone_history`: Japanese only, 1000+ characters enforced

---

## v1.0.0 — 2026-03-01

**Codename: "Genesis"**

- Initial production deployment
- GemminAI pipeline: RSS → Gem0 → Gem1 → T35 → Gem2 → Laravel → Frontend
- 35TAG schema v6.0 finalized
- 3DLUT color rendering system operational

---

*Gemmina Intelligence LLC. — Pure Information Laboratory*
