# Phase 2 Multi-Omics Data Feasibility Audit — Methylation (GDC) + CRISPR-Cas Evidence (PubMed/Europe PMC)

Researched 2026-09-07. This is a gating audit, not an implementation. Every claim below
traces to either (a) a live call against the real API, or (b) an official docs page
actually fetched. Anything not directly verified is marked **unable to verify**. No
code was written or modified as part of this task; this file is the only change.

This audit builds on the existing verified findings in `docs/data-access.md` (GDC,
PubMed, Europe PMC base API status) — it does not repeat that verification, only the
methylation- and CRISPR-Cas-specific gaps not yet covered there.

## Research process / sources consulted

- `docs.gdc.cancer.gov/API/Users_Guide/Search_and_Retrieval/` (GDC REST API docs)
- Live calls against `api.gdc.cancer.gov`:
  - `GET /files` filtered on `cases.project.project_id=TCGA-LUAD` and
    `data_type=Methylation Beta Value`, fields `file_id,file_name,data_type,data_format,access,platform`
  - `GET /projects` filtered on `TCGA-LUAD,TCGA-LUSC,TCGA-COAD,TCGA-READ,TCGA-BRCA`,
    fields `summary.data_categories.data_category,summary.data_categories.case_count`
  - `GET /files/_mapping` (full field inventory for the `/files` endpoint)
- WebSearch on IDAT/legacy-archive availability and community tooling (TCGAbiolinks,
  GDC Data Transfer Tool) for cross-checking the harmonized-vs-legacy archive split
- Existing repo code: `apps/api/src/biosense/infrastructure/external/gdc_client.py`,
  `europe_pmc_client.py`, `pubmed_client.py`, `source_registry.py`, and
  `apps/api/src/biosense/domain/entities/biomarker_dimension.py` for current schema
  conventions

One doc fetch failed (`gdc.cancer.gov/.../gdc-dna-methylation-pipeline` returned 404 —
noted as unable to verify via that specific URL; the live API calls above are used as
the primary evidence instead).

## Summary table

| Dataset | Provider | Data type | API | Download | Access | Relevant fields | Suitable for MVP |
|---|---|---|---|---|---|---|---|
| GDC harmonized methylation beta values (Illumina HM450, `sesame.level3betas.txt`) | NCI GDC | Processed per-CpG beta values, one row per probe per sample, TXT | `GET /files` (metadata/discovery only — **VERIFIED live**: `access:"open"`, `data_format:"TXT"`, `platform:"Illumina Human Methylation 450"`, 710 files for TCGA-LUAD alone) | File-level bulk download only (`/data/{file_id}` or Data Transfer Tool); no REST field returns actual beta values | Open-access (no dbGaP needed) | file_id, file_name, data_type, data_format, platform, chip_id, chip_position, access, cases.project.project_id — **no** CpG-site or beta-value fields exist on `/files` (**VERIFIED** via `/files/_mapping`) | **Partially** — project/file discovery is REST-queryable now; actual beta values require downloading and parsing TXT files, which is out of scope for a REST-only MVP feature |
| GDC harmonized methylation, EPIC array | NCI GDC | Same as above, newer array platform | Same as above | Same as above | Open-access | Same as above | Same caveat as above |
| GDC legacy-archive IDAT (raw array intensities) | NCI GDC | Raw scanner intensity files, 2 per sample | Discoverable via legacy `/files`-equivalent endpoints (**not independently re-verified this session**; per community sources, IDAT is in the legacy archive, not the current harmonized archive) | Bulk file download, large binary files, needs a bioinformatics pipeline (e.g. minfi/sesame) to even produce beta values | Open-access historically, but legacy archive access patterns differ from current GDC API — **unable to verify current exact status without a dedicated legacy-archive API call** | N/A (binary format, no queryable fields) | **No** — raw array processing is well outside REST-API/MVP scope regardless of access tier |
| TCGA-LUAD / LUSC / COAD / READ / BRCA methylation case coverage | NCI GDC (TCGA) | Project-level summary counts | `GET /projects` with `summary.data_categories` (**VERIFIED live**: LUAD 579, LUSC 503, COAD 457, READ 165, BRCA 1097 cases carrying a "DNA Methylation" data category) | N/A (summary counts only) | Open-access | project_id, summary.data_categories.data_category, summary.data_categories.case_count | **Yes** — this level (project has methylation data, case counts) is genuinely REST-queryable today and fits the existing `GdcClient.search_projects` pattern |
| PubMed abstracts (E-utilities) | NCBI/NLM | Title, abstract, authors, journal, DOI, MeSH | `esearch`/`efetch` — already implemented (`PubmedClient`), **VERIFIED** in `docs/data-access.md` | N/A | Public domain | Structured bibliographic metadata + free-text abstract; **no structured target/CRISPR-system/assay/sensor relationship fields exist** | **Yes, for literature retrieval** — **No, for pre-extracted structured relationships** (API returns text, not facts) |
| Europe PMC full text/abstracts | EMBL-EBI | Abstract + open-access full text flag | `/search` REST API — already implemented (`EuropePmcClient`), **VERIFIED** | N/A for closed-access full text; open-access full text fetchable per article | Source-dependent; EBI Privacy Notice | Same structured-metadata-only limitation as PubMed | Same as above |

## GDC methylation — detailed findings

1. **REST API is real and live** (confirms/extends `docs/data-access.md` §2): a filtered
   `GET /files` call against `api.gdc.cancer.gov` for `TCGA-LUAD` +
   `data_type=Methylation Beta Value` returned 710 matching files, all
   `"access": "open"`, `"platform": "Illumina Human Methylation 450"`,
   `"data_format": "TXT"`.
2. **What the API actually returns for methylation is file *metadata*, not
   measurement data.** `GET /files/_mapping` was fetched and inspected: the queryable
   field set for `/files` includes `data_type`, `platform`, `chip_id`, `chip_position`,
   `data_format`, `access`, and case/project linkage fields — **there is no field that
   returns a CpG site id, a beta value, or any per-probe methylation number.** To get
   an actual methylation value you must download the named TXT file (via
   `/data/{file_id}` or the GDC Data Transfer Tool) and parse it yourself — that file
   is a plain-text table of probe-id → beta-value pairs per sample, not something the
   REST API surfaces as structured JSON fields.
3. **Access tier**: the harmonized beta-value files for TCGA-LUAD are open-access
   (no dbGaP authorization required) — this was directly observed in the live
   response (`"access": "open"`). This does **not** generalize automatically to every
   project/file — GDC's access control is per-file, and controlled-access clinical or
   germline files do exist elsewhere in GDC — but beta-value-level methylation output
   specifically is the open-access processed product, consistent with GDC's general
   open/controlled split described in `docs/data-access.md` §2.
4. **Raw IDAT array files** (the actual scanner output, needed if you wanted to
   reprocess methylation from scratch rather than use TCGA's own beta values) sit in
   GDC's **legacy archive**, not the current harmonized archive that `/files` primarily
   serves today — per community documentation (TCGAbiolinks, GDC download tooling).
   This session did not independently re-verify current legacy-archive API behavior
   against a live legacy endpoint, so **the exact current access path/status for legacy
   IDAT is unable to verify** beyond what third-party tooling docs describe. This does
   not change the MVP recommendation either way, since IDAT processing is out of scope
   regardless.
5. **All five target TCGA cohorts (LUAD, LUSC, COAD, READ, BRCA) do carry a "DNA
   Methylation" data category with real case counts** (579 / 503 / 457 / 165 / 1097
   respectively), verified live via `/projects`. So project-level "does this cancer
   type have methylation data" is a genuinely answerable, real REST query today.

### What this means for Phase 2 MVP feasibility (methylation)

- **Feasible as REST-only, MVP-appropriate today**: extending `GdcClient` with a
  `search_methylation_files(project_id, platform=...)` -style method that returns
  file-level metadata (file count, platform, access, chip info) — the same shape as
  the existing `search_projects`/`search_genes`/`search_mutations` methods. This is a
  legitimate, live-queryable, no-auth extension consistent with the current client
  design.
- **Not feasible as a REST-only MVP feature**: anything that claims to return an
  actual gene-level or CpG-site-level methylation value, methylation status
  (hyper/hypomethylated), or normalized beta value through the API. That data exists
  only inside downloadable TXT files that require a separate download-and-parse step
  (and, for true per-sample statistical use, arguably a small ETL/caching layer —
  GDC's own docs do not offer a "give me beta value for gene X, project Y" endpoint).
- **This is a scope decision, not an implementation detail**: Phase 2 methylation
  can ship as "file/dataset discovery + citation" (analogous to how mutation counts are
  surfaced today) without implying resolved beta-value data is available. Presenting
  gene-level or CpG-level methylation *values* would require either (a) a bulk-download
  + offline processing pipeline (out of scope for a backend REST service per current
  architecture), or (b) sourcing a pre-computed third-party summary (not verified to
  exist as an open API in this audit — would need its own separate feasibility check,
  e.g. UCSC Xena, cBioPortal, ICGC).

## PubMed / Europe PMC — CRISPR-Cas structured evidence extraction

- Both `PubmedClient` and `EuropePmcClient` are already real, working, no-auth (or
  optional-key) API clients per `docs/data-access.md` §4–5, and both were re-confirmed
  in this session by reading their source directly — they parse title/abstract/
  authors/journal/DOI/publication date into `RawPaperRecord`. Neither API, nor any
  documented endpoint of either, returns pre-extracted structured facts such as
  "target gene X was edited with CRISPR system Y and detected via assay Z with
  reported sensitivity N."
- **This is a hard, structural limitation, not a configuration gap**: PubMed
  E-utilities and Europe PMC's REST API are literature *search and retrieval* systems.
  Their output unit is a paper (title/abstract/optionally full text) and associated
  bibliographic metadata (MeSH terms, journal, authors). Turning that into a
  target→CRISPR-system→assay→sensor→performance relationship graph requires either:
  1. **Manual curation** (a human reads matched papers and records structured facts),
     or
  2. **NLP/LLM-based relation extraction** run separately over the fetched abstracts/
     full text — itself a nontrivial task requiring its own accuracy validation
     (false positives/negatives in extracted "facts" are a known failure mode for
     biomedical relation extraction and would need explicit confidence/evidence-review
     UI, consistent with how this repo already treats `EvidenceRef`/
     `BiomarkerEvidenceStatus` as explicit "how sure are we" fields rather than
     silently authoritative data).
- **No violation of API terms is implied by either path** — search/fetch of
  abstracts and open-access full text via the official APIs is exactly what both
  services are for; the gap is purely that "structured relationship" is not a shape
  either API emits, so building it means adding a distinct
  extraction/curation stage downstream of the existing clients, not extending the
  clients themselves.

### What this means for Phase 2 MVP feasibility (CRISPR-Cas evidence)

- **Feasible now**: literature retrieval/citation for CRISPR-Cas-related papers,
  using the existing `PubmedClient`/`EuropePmcClient` with CRISPR-specific search
  terms (analogous to `DEFAULT_PUBMED_QUERIES` in `pubmed_client.py`) — this fits the
  existing evidence-layer pattern exactly (`EvidenceRef` citations attached to a
  biomarker/dimension).
- **Not feasible via API alone**: structured target→CRISPR-system→assay→sensor→
  performance extraction. This requires an explicit scope decision:
  either (a) descope to citation-only evidence (papers linked, no extracted
  structured fields) for Phase 2, or (b) commission a separate NLP/curation
  workstream with its own accuracy bar, review UI, and (per existing
  `BiomarkerEvidenceStatus`) an explicit way to mark extracted facts as
  lower-confidence than directly-sourced structured data (e.g. GDC mutation records).

## Schema fit — existing `BiomarkerDimension` / `EvidenceRef`

`apps/api/src/biosense/domain/entities/biomarker_dimension.py` already reserves
`BiomarkerDimensionType.METHYLATION` in the enum (currently `is_phase1_supported`
returns `False` for it — i.e. the codebase already flags methylation as
not-yet-implemented, consistent with this audit's finding that it needs a scope
decision before proceeding). Fit assessment against the fields named in the task spec:

- `gene`, `cancer_type`, `sample_type`, `study`/`dataset`, `evidence` — map cleanly
  onto existing fields (`genomic_context`, and `EvidenceRef.dataset`/`source`/
  `external_id`/`access_level`/`evidence_type`).
- `genomic_region`, `CpG_site` — **no current field**. `molecular_feature`/
  `structural_feature` are free-text and could hold a CpG probe id as a string, but
  there's no dedicated, typed field for probe-level identity the way `RawGdcMutationRecord`
  has `genomic_dna_change`.
- `methylation_value`, `methylation_status` — **no current field anywhere in
  `BiomarkerDimension`.** This is a real gap: the class currently has no numeric/
  quantitative fields at all (everything is `str | None` descriptive text), whereas
  methylation is inherently a per-probe numeric measurement. Adding it would need a
  new typed field (e.g. `methylation_beta: float | None`, `methylation_status: str | None`)
  plus, per the finding above, a data source that can actually populate it — which,
  per this audit, the GDC REST API alone cannot do without a file-download step.
- `assay`/`platform`, `normalization status`, `units` — **no current field.** The
  closest analogue is `EvidenceRef.evidence_type`, but that's evidence-type
  classification, not assay/platform provenance. This would need new fields.
- **Net assessment**: the existing dataclass shape (descriptive-text dimension +
  list of `EvidenceRef` citations) is a good fit for *methylation-as-a-discovered-
  dataset* (file/project-level), matching what's actually REST-queryable. It is
  **not yet a good fit for methylation-as-a-quantitative-measurement** (beta value,
  CpG site, platform, normalization) — those fields don't exist today and, more
  importantly, populating them from GDC would require the file-download pipeline
  this audit flags as out of current REST-only scope. Adding the fields without also
  deciding on a data-population path would create schema for data the platform
  cannot yet honestly fill in.

## Explicit list of what is NOT feasible / needs a scope decision before Phase 2 proceeds

1. **Do not implement** any endpoint or field that implies live per-gene or
   per-CpG-site methylation *values* are retrievable via GDC's REST API — they are
   not; only file-level discovery metadata is.
2. **Scope decision needed**: whether Phase 2 methylation ships as
   discovery-only (file/project/case-count metadata, open-access, REST-queryable
   today — recommended path if a decision is needed quickly) or whether the project
   commits to a bulk-download + offline-processing pipeline (parsing GDC TXT beta-value
   files) to get actual quantitative values — the latter is a materially larger,
   different piece of engineering (batch jobs, storage, a bioinformatics dependency)
   than anything currently in this repo's connector pattern.
3. **Do not implement** any GDC IDAT/raw-array ingestion — this is legacy-archive,
   binary, and requires external bioinformatics processing (minfi/sesame-style
   pipelines) regardless of access tier; this audit did not fully re-verify current
   legacy-archive API access mechanics and flags that as unable-to-verify-further
   rather than assuming it's straightforward.
4. **Do not implement** any feature that claims PubMed/Europe PMC APIs return
   structured CRISPR-Cas target/system/assay/sensor/performance relationships — they
   return text (abstracts/full text) and bibliographic metadata only.
5. **Scope decision needed**: whether CRISPR-Cas evidence in Phase 2 is
   citation-only (recommended path fitting the current `EvidenceRef` pattern with no
   new engineering) or whether the project commissions a separate NLP/manual-curation
   extraction workstream — and if the latter, what confidence/verification UI marks
   extracted-not-directly-sourced facts as such (per the existing
   `BiomarkerEvidenceStatus` philosophy of never presenting an unsupported claim as if
   it were fully verified).
6. **Schema gap flagged, not filled**: `BiomarkerDimension` has no numeric/
   quantitative fields today (methylation beta value, CpG site id, platform,
   normalization status, units) — these should only be added once a decision is made
   on where the actual values will come from (per point 2), so the schema doesn't get
   ahead of what the platform can honestly populate.
