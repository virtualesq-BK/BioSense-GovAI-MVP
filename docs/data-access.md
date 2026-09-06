# Official Data Access Policies

Researched 2026-09-07. Each source was verified against its own official documentation
and, where feasible, tested directly against the live endpoint. Only findings that
were confirmed this way are marked **VERIFIED**; everything else is marked
**PER DOCS (untested)**.

---

## 1. CDC — United States Cancer Statistics (USCS)

**Verdict: No automatable API. Two official, human-operated access channels only.
BioSense-GovAI links to the free channel as an external reference; no connector is built.**

### Why no live API

- CDC WONDER (`wonder.cdc.gov`) exposes a genuine XML/POST API for many of its databases
  (mortality, natality, etc.) — **VERIFIED**: no API key required, just a POST of an XML
  request document with `accept_datause_restrictions=true`. But this API access was
  extended only to **vital statistics** databases (mortality/natality) as of a Feb 2015
  policy change — **VERIFIED**: the WONDER homepage's "Cancer Statistics" entry carries no
  API designation, unlike vital-statistics entries, and CDC's own API docs give examples
  only for the mortality database (D76), consistent with cancer registry data being
  excluded due to additional confidentiality/suppression rules.
- **VERIFIED by direct request**: even the public, no-login interactive query tool at
  `wonder.cdc.gov` returns **HTTP 403 (Access Denied, Akamai edge block)** to a
  non-browser client — confirming it is designed for human/browser use only, not
  programmatic automation. Its `robots.txt` additionally declares `Content-Usage: ai=n`
  (content must not be used for AI training/automation), reinforcing that scripting this
  tool would run against the site's stated intent, not just its technical design.
- Per project rule §29.7 ("API가 있는 경우 crawling하지 마라") and §18 (crawling is a last
  resort, bot-blocks are never bypassed), **BioSense-GovAI does not attempt to automate
  either CDC channel.**

### Channel A — WONDER interactive aggregate query tool (free, human use only)

- URL: **https://wonder.cdc.gov/cancer-v2022.html**
- No login or registration. Anyone can select filters (state/region, cancer site, year
  1999–2022, age group, sex, race/ethnicity) and export results as CSV, TSV, or XLS.
- Data granularity: **aggregate** counts/rates only (not individual case records).
- **This is the only channel BioSense-GovAI references.** It is surfaced in the product
  as an external link/citation for users who want official U.S. aggregate cancer
  statistics — the platform does not fetch, cache, or re-host its data automatically.

### Channel B — USCS Public Use Database (case-level, gated, not integrated)

- Requires (1) a separate **SEER Research Plus** account approval, then (2) emailing a
  signed **Database Request Form** to `uscsdata@imsweb.com` — **VERIFIED**: CDC states a
  ~2-business-day turnaround after that. Delivered as a **SEER*Stat-format** file (a
  proprietary desktop analysis tool), not a REST-consumable format.
- Out of scope for this MVP: gated behind manual, per-person approval that a backend
  service cannot obtain on its own, and not in a directly machine-ingestible format.
  If a future user obtains approved access themselves, the resulting export could be
  dropped into `infra/seed/public_health/` and normalized via the existing
  `seed_loader.py` pattern — but that remains a manual, human-initiated step.

**Implication for BioSense-GovAI:** No `CdcUscsConnector` exists in code. The UI/report
layer should present `https://wonder.cdc.gov/cancer-v2022.html` as a labeled external
reference link for U.S. aggregate cancer statistics, distinct from and clearly marked
apart from the platform's own live-queried sources (GDC, PubMed, Europe PMC, KOSIS/KDCA).

Sources:
- [CDC WONDER API for Data Query Web Service](https://wonder.cdc.gov/wonder/help/wonder-api.html)
- [CDC WONDER data use restrictions](https://wonder.cdc.gov/datause.html)
- [United States and Puerto Rico Cancer Statistics, 1999-2022 Incidence Request](https://wonder.cdc.gov/cancer-v2022.html)
- [U.S. Cancer Statistics Public Use Database](https://www.cdc.gov/united-states-cancer-statistics/public-use/index.html)
- [U.S. Cancer Statistics Public Use Databases](https://www.cdc.gov/cancer/uscs/public-use/)
- [United States Cancer Statistics Restricted Access (RDC)](https://cdc.gov/rdc/other-restricted-data/cancer-statistics.html)
- Direct verification: `curl` to `wonder.cdc.gov` returned HTTP 403 (Akamai block); its
  `robots.txt` declares `Content-Usage: ai=n` (checked 2026-09-07)

---

## 2. NCI Genomic Data Commons (GDC)

**Verdict: Real, public REST API. No authentication needed for open-access metadata. VERIFIED live.**

- Base URL: `https://api.gdc.cancer.gov`
- **VERIFIED by direct call** (no API key, no auth header):
  - `GET /projects` → returns TCGA/other project metadata (93 total projects)
  - `GET /genes` → gene-level annotations (22,824 genes)
  - `GET /ssms` → simple somatic mutations (3.6M+ records, e.g. `chr12:g.109768424G>A`)
- Also documented: `/cases`, `/files`, `/annotations`, `/history`, `/status`,
  `/{endpoint}/_mapping` (introspection) — all open-access, no auth.
- **Controlled-access** data (raw sequencing files, germline variants, some clinical
  fields) requires dbGaP authorization via an NIH Data Access Committee, plus an
  `X-Auth-Token` header on the `/data` download endpoint. This must **never** be
  auto-fetched — per the project's own rule, controlled access requires an explicit
  manual user-authorization workflow.
- Citation requirement: cite the GDC paper (Heath et al., Nat Genet 2021) and each
  project's own attribution policy (e.g., TCGA publication guidelines) — no formal
  data license, but citation is a condition of use.

**Implication:** `GdcConnector` can be built as a genuine live `PublicDataConnector`
(open-access tier only) — `search()`/`fetch()`/`health_check()` all map directly onto
real endpoints. This is the strongest, most "real API" data source of the five.

**Status: implemented.** `apps/api/src/biosense/infrastructure/external/gdc_client.py`
(`GdcClient`) — `search_projects(primary_site=...)`, `search_genes(symbol)`,
`search_mutations(gene_symbol=...)`, `health_check()`. All three query shapes were
live-tested against `api.gdc.cancer.gov` before implementation (see filter examples
below). Unit tests: `apps/api/tests/unit/test_gdc_client.py` (9 tests, mocked HTTP).

Sources:
- [GDC API](https://gdc.cancer.gov/content/gdc-api)
- [GDC Data Access Processes and Tools](https://gdc.cancer.gov/access-data/data-access-processes-and-tools)
- [GDC API Users Guide — Getting Started](https://docs.gdc.cancer.gov/API/Users_Guide/Getting_Started/)
- [GDC API Users Guide — Search and Retrieval](https://docs.gdc.cancer.gov/API/Users_Guide/Search_and_Retrieval/)
- Live endpoint tests: `api.gdc.cancer.gov/genes`, `/ssms`, `/projects` (run 2026-09-07)

---

## 3. TCGA

**Verdict: Not a separate API — accessed entirely through the GDC API/portal above.**

- TCGA has no standalone REST API; all TCGA project data (`TCGA-LUAD`, `TCGA-BRCA`,
  `TCGA-COAD`, `TCGA-LIHC`, `TCGA-STAD`, etc.) is served through GDC's `/projects`,
  `/cases`, `/files`, `/ssms` endpoints, filtered by `project_id`.
- No formal data license, but TCGA publication guidelines require citation/acknowledgment
  when TCGA-derived data is used in any output (including AI-generated R&D reports).

**Implication:** Do not build a separate `TcgaConnector`. Treat TCGA cancer types as a
`project_id` filter parameter on the `GdcConnector`.

Sources:
- [GDC — General Questions FAQ](https://gdc.cancer.gov/faq-tags/general-questions-0)
- TCGA publication guidelines (linked from GDC citation policy)

---

## 4. PubMed (NCBI E-utilities)

**Verdict: Real official API, already implemented in this repo. VERIFIED policy.**

- Base: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils` (already in `.env` as
  `PUBMED_BASE_URL`, used by `PubmedClient`).
- Rate limit: **3 requests/sec without a key, 10/sec with a free NCBI API key**
  (`api_key=` param). No key is currently configured (`PUBMED_API_KEY` empty in `.env`)
  — recommend obtaining one from an NCBI account to raise the ceiling before scaling
  ingestion volume.
- No cost, no data license restriction beyond normal citation norms (PubMed is an index,
  not a full-text repository — abstracts and metadata only via E-utilities).

**Implication:** Existing `PubmedClient` is policy-compliant. Only action needed:
add a real `PUBMED_API_KEY` when ingestion volume increases.

Sources:
- [NCBI E-utilities API keys](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/)
- [Release Plan for E-utility API Keys](https://ncbiinsights.ncbi.nlm.nih.gov/2018/08/14/release-plan-for-e-utility-api-keys/)

---

## 5. Europe PMC

**Verdict: Real official REST API, no auth required.**

- Base: `https://www.ebi.ac.uk/europepmc/webservices/rest/`
- Key endpoints: `/search` (full-text + metadata search over 33M+ publications, 6.5M+
  open-access full text), `/fields` (queryable field list).
- No API key / authentication required.
- Rate limit reported at ~10 req/sec per IP (unofficial community reports; no documented
  hard cap found in official docs — implement conservative throttling + `with_retry`,
  consistent with the existing `PubmedClient` pattern).
- Output formats: JSON, XML, Dublin Core RDF/XML. Users must accept EBI's Privacy Notice
  (no account needed, it's a usage-terms acknowledgment, not a login).

**Implication:** Safe to build following the same shape as `PubmedClient` — real API,
no auth, straightforward JSON responses. Useful complement to PubMed for open-access
full-text metadata (PubMed/E-utilities gives abstracts only).

**Status: implemented.** `apps/api/src/biosense/infrastructure/external/europe_pmc_client.py`
(`EuropePmcClient`) — `search_and_fetch(query, max_results)` normalizes results into the
same `RawPaperRecord` shape as `PubmedClient`, using `firstPublicationDate` for exact
publication dates. Live-tested against the real API before implementation. Unit tests:
`apps/api/tests/unit/test_europe_pmc_client.py` (7 tests, mocked HTTP).

Sources:
- [Europe PMC RESTful Web Service](https://europmc.org/RestfulWebService)
- [Europe PMC API usage discussion (rate limits)](https://groups.google.com/a/ebi.ac.uk/g/epmc-webservices/c/58IylGvdeY8)

---

## Summary Table

| Source | Live API? | Auth | Verified | Status |
|---|---|---|---|---|
| CDC USCS | ❌ No automatable API (403-blocked, `ai=n` robots policy) | N/A | ✅ (confirmed absence + block) | **Not integrated.** Referenced as an external link (`wonder.cdc.gov/cancer-v2022.html`) only — no connector, no automated fetch |
| NCI GDC | ✅ Real REST API | None (open-access) | ✅ Live-tested | **Implemented** — `GdcClient` (`infrastructure/external/gdc_client.py`) |
| TCGA | (via GDC) | via GDC | ✅ | Covered by `GdcClient.search_projects(primary_site=...)` — no separate client |
| PubMed | ✅ Real API | Optional key (raises rate limit) | ✅ (already in repo) | Already implemented — add API key when scaling |
| Europe PMC | ✅ Real API | None | ✅ Live-tested | **Implemented** — `EuropePmcClient` (`infrastructure/external/europe_pmc_client.py`) |

All four implemented clients (`KosisClient`, `KdcaClient`, `PubmedClient`, `GdcClient`,
`EuropePmcClient`) implement the common `PublicDataConnector` interface
(`infrastructure/external/base.py`: `search()`, `fetch()`, `health_check()`) alongside
their existing domain-specific methods — see `apps/api/tests/unit/test_public_data_connector_interface.py`.

## Key Constraint This Sets on the Roadmap

CDC USCS cannot be a `search()`/`fetch()`-style live connector like the others —
building one that pretends to call a live API, or scripting a bot-blocked interactive
tool, would violate rules §29.2 and §29.7. It is intentionally **excluded from the
connector layer** and surfaced only as a labeled external reference link in the UI/reports.
