# Release Notes — GemminAI

## v1.3.1 — 2026-04-25

**Codename: "Research Portal"**  
*6-country narrative pipeline established. Empirical Kill Shot confirmed. Research Portal fully operational.*

### 6-Country Narrative Pipeline

* Added `/multi` endpoint to `narrative-generator` — generates JP/US/GB/CN/EU/QA narratives in a single request
* Refactored `/multi` to 2-phase architecture: Gemini generation (all countries first) then bulk DB save (single connection)
* Fixed MySQL connection timeout during long Gemini retry waits
* `orchestrator.py` updated to dispatch via `/multi` — 6 countries per article
* Phase 2 `max_output_tokens` increased 2048 to 4096 — `backbone_history` and `deep_dive` now fully generated
* Added `isinstance(dict)` guard for Phase 1/2 JSON parsing — eliminates `list.get()` AttributeError

### Research Portal (`gemminai.com/research`)

* **Figure 7 tab added** — live empirical testbed wired to real DB metrics
* `GET /api/v1/research/metrics` endpoint added (Laravel + Next.js BFF)
* `EmpiricalTestbed.tsx` component connected to live API — real SIV, state_hash, today event count
* `stats/route.ts` rewritten to fetch all-country narratives; `points3d` computed per country with real SIV
* `sovereign/events/[id]/route.ts` — `normalize()` added to flatten nested narrative structure for SovereignPanel
* `EventController@latest` rewritten — `narrative_articles` replaced by `v31_states_core` JOIN (eliminated 500 error)
* All 5 tabs operational: Narrative Spectrometer, 3D Viewpoint Gap, Raw Data, Sovereign v3.1, Figure 7

### Figure 7: Failure of the Independence Assumption (Kill Shot)

* Empirical validation on GemminAI production dataset — 786 real SIV pairs + 5,000 IID simulations
* Two-sided permutation test, n_perm=10,000
* Variance reduction (Structured vs IID): **84.2%** — p < 0.0001 (variance and entropy both)
* Published: `scripts/classical_baseline.py`, `data/results_classical.csv`, `figure7_classical_baseline.png`
* Paper: *NQM 3.1 — Quantum-Formalism Narrative State Observation* (PDF, April 2026)

### Infrastructure

* `orchestrator.service` confirmed enabled (systemd) — survives VM reboot
* Cloud Scheduler `reporter-brain-daily` confirmed firing at JST 23:00
* `narrative-generator` revision 00015 deployed with 2-phase `/multi` architecture

### Data Quality

* Batch-corrected 2 records with `{'english': '...'}` key pattern in `title_ja`
* Remaining 3 quota-exhausted records corrected after Gemini API daily reset

---

## v1.3.0 — 2026-04-24

**Codename: "Epistemic Engine"**  
*SIV-driven reporter routing replaces string matching. Sovereign inference layer established.*

### Epistemic Engine v6.0

* Implemented `assign_reporter_by_siv()` — `argmax(|SIV|)` maps 6-dimensional Strategic Interest Vector to reporter deterministically
* Replaced `CATEGORY_REPORTER` string-matching with SIV-based dynamic routing in `reporter_brain_fn`
* `chief_editor` integrated into `reporter_brain_fn` — synthesizes top-10 articles across all categories
* Model updated: `gemini-2.0-flash` (v1beta API compatible) confirmed as production model

### Infrastructure

* `narrative-generator` migrated from Cloud Functions (gen1) to pure Cloud Run (gunicorn)
* Eliminated `functions_framework` annotation conflict — `run.googleapis.com/build-function-target` cleared via service recreation
* OIDC authentication unified: `orchestrator.py` now injects `Authorization: Bearer` token via `gem0_auth_provider`
* `narrative-generator` secured with `--no-allow-unauthenticated` + Cloud Run Invoker IAM
* All secrets migrated to **Secret Manager** (`GEMINI_API_KEY`, `DB_PASSWORD`) — plaintext env vars eliminated
* Cloud Scheduler registered: `reporter-brain-daily` fires daily at JST 23:00 (`asia-northeast1`)
* `orchestrator.service` registered as systemd enabled — survives VM reboot

### Pipeline

* `gateway.py` rewritten: `narrative_articles` table replaced by `events` + `v31_states_core` JOIN
* SIV reconstructed from `t09_siv_*` columns (6-column → dict) for downstream compatibility
* `narrative-generator` URL updated to `narrative-generator-962210526512.asia-northeast1.run.app`
* `orchestrator.py` dispatched 2 articles successfully post-fix (NIKKEI, TECHCRUNCH)

### Data Quality

* Batch-corrected 65 records with dict-string `title_ja` corruption (4/19–4/23 legacy bug)
* Root cause: Python `str(dict)` serialization instead of value extraction — fixed in `generate_title_ja()`

### Research

* T35 Phase E branching confirmed live: `dv=0.568, coh=0.901, ent=0.699` observed in production logs
* These values constitute real observational data for **Figure 7 (Kill Shot)** in the forthcoming paper


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
