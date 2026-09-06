# BioSense-GovAI 고도화 실행 문서 (Cursor + Claude Code 부착용)

> 이 문서는 실제 저장소(`BioSense-GovAI MVP`)를 스캔한 결과를 근거로 작성되었습니다.
> **기존 구현을 다시 만들지 않도록**, 항목마다 `[이미 구현]` / `[부분 구현]` / `[신규]` 를 표시했습니다.
> Cursor에서는 `.cursor/rules/biosense.mdc` 규칙이 자동 적용되므로, 아래 프롬프트는 그 규칙을 전제로 작성했습니다.

---

## 0. 현재 구현 현황 요약 (스캔 근거)

데모 설명(하이브리드 추천 엔진 / 공공데이터 / 문헌 RAG / 성능 예측 / 신뢰도 스코어링 / 리포트 생성)은 **이미 상당 부분 코드로 존재**합니다. 새로 설계할 필요가 없고, 확장·보강만 하면 됩니다.

| 영역 | 상태 | 근거 파일 |
|---|---|---|
| Clean Architecture (api/application/domain/infrastructure) | 이미 구현 | `apps/api/src/biosense/*` |
| 관계형 그래프 스키마 (Cancer→Biomarker→Recognition→Sensor) | 이미 구현 (Postgres, Neo4j 아님) | `infra/db/migrations/postgres/002_domain_entities.sql`, `graph_retrieval_service.py` |
| 하이브리드 랭킹 + 신뢰도 스코어 | 이미 구현 | `domain/services/weighted_ranker.py` (`WeightedRanker`, `ConfidenceScorer`) |
| 추천 엔진 파이프라인 (feature→graph→hybrid→LLM rationale) | 이미 구현 | `application/services/recommendation_engine_service.py` |
| 문헌 RAG (pgvector 임베딩 검색 + 인용 생성) | 이미 구현 | `literature_rag_service.py`, `hybrid_retrieval_service.py` |
| RAG 평가 지표 (precision/recall/MRR/citation coverage) | 이미 구현 | `LiteratureEvaluationService`, 테이블 `rag_evaluations` |
| PDF 파싱 → 청킹 → 임베딩 → 저장 파이프라인 | 이미 구현 | `literature_ingestion_service.py`, `pdf_parser.py`, `chunking_service.py` |
| 문헌 수집 방식 | **관리자 수동 업로드만 가능** (PDF/텍스트) | `api/v1/literature.py` (`/papers/upload`, `/papers/ingest-text`) |
| PubMed/Europe PMC 자동 수집기 | **없음** | 저장소 전체에 관련 클라이언트 없음 |
| 한국 공공데이터 (KOSIS/KDCA) 클라이언트 | 이미 구현 (실 API + 시드 폴백) | `infrastructure/external/korean_health_clients.py` |
| 공공데이터 스케줄러 | 이미 구현 (매일 cron) | `jobs/scheduler.py` — **문헌 수집은 스케줄 대상 아님** |
| 성능지표(민감도/특이도/LOD 등) 자동 추출 | **없음** — `sensor_performances` 테이블은 수기 시드 데이터만 존재 | `infra/db/migrations/postgres/003_seed_domain_data.sql`, `extract_service.py`(공공데이터 전용) |
| 실험 프로토콜 | 부분 구현 — 시드 3건만 실제 논문 인용 연결, 나머지는 기본 스텝 fallback | `recommendation_engine_service.py:87-97`, `003_seed_domain_data.sql` |
| PDF 리포트 생성 | 이미 구현 (클라이언트 jsPDF, 추천 결과 요약) | `apps/web/src/lib/pdf-export.ts` |
| Top-K 추천 카드 UI | 이미 구현 | `apps/web/src/app/(saas)/recommendations/page.tsx` |
| 관리자 문헌/모니터링 화면 | 이미 구현 | `apps/web/src/app/(saas)/admin/literature/page.tsx`, `/admin/page.tsx` |
| Neo4j | **인프라만 존재, 실사용 안 함** (`docker-compose.yml`, `infra/db/migrations/neo4j/*`) — 실제 그래프 순회는 SQLAlchemy join | 결정 필요 (섹션 1 참고) |
| 바이오마커 taxonomy | 7종 (KRAS/EGFR/SEPT9/Fragment/TP53/BRCA1/PIK3CA) — **exosome miRNA, CTC, multi-omics 없음** | `003_seed_domain_data.sql` |
| 센서 taxonomy | 6종 (electrochemical/optical(SPR)/FET/lateral_flow/microfluidic/piezoelectric) — **SERS, AI-NGS, CRISPR 전용 센서 없음** | 동일 |
| 지역별 공공데이터 커버리지 | 4개 지역 × 일부 암종만 시드 존재 (서울/부산/경기) | 동일 |

**결론:** 사용자가 요청한 Epic A~E는 "0에서 구축"이 아니라 **"수동 → 자동", "시드 → 실데이터", "정적 → 추출형"으로의 업그레이드**입니다. 아래 우선순위와 TODO는 이 전제로 재구성했습니다.

---

## 1. 고도화 우선순위 (재정렬)

### 우선순위 1 — 문헌 자동 수집 파이프라인 신설 (가장 시급, 가장 임팩트 큼)
현재 문헌은 관리자가 PDF/텍스트를 손으로 올려야만 RAG에 들어갑니다. `papers.source = 'PubMed'`, `external_id = 'pmid:xxxx'` 컨벤션은 이미 시드 데이터에 존재하므로, PubMed E-utilities 수집기만 붙이면 기존 파이프라인(`LiteratureIngestionPipeline`)을 그대로 재사용할 수 있습니다.

### 우선순위 2 — 성능지표 자동 추출기 (RAG를 "검색"에서 "근거 추출"로)
`sensor_performances`(민감도/특이도/LOD)가 전부 수기 값입니다. 논문 청크에서 정량 지표를 뽑아 `sensor_performances`에 `source_paper_id`, `confidence`와 함께 적재하는 추출기가 필요합니다. 이게 되면 `RecommendationEngineService`의 fallback 상수(`sensitivity=0.85` 등, `recommendation_engine_service.py:80-84`)를 실데이터로 대체할 수 있습니다.

### 우선순위 3 — 바이오마커/센서 taxonomy 확장 (Top-K 전략 카드 실현)
exosomal miRNA, SERS, multi-omics panel, CTC, AI-NGS를 추가해야 사용자가 원하는 5대 전략 카드(ctDNA+AI NGS / 엑소좀 miRNA / SERS / 다중오믹스 / 원발부위 예측)가 실제로 매칭 가능해집니다. 지금은 taxonomy에 없어서 나올 수 없습니다.

### 우선순위 4 — 공공데이터 → 정책 우선순위 "문장" 생성
`public_health_score`는 숫자로만 존재합니다("부산 고령층 남성 폐암 부담이 높아…" 같은 서술은 없음). `evidence.public_health` 딕셔너리에 narrative 필드를 추가하고, 지역 커버리지도 4개 지역에서 17개 시도로 확장.

### 우선순위 5 — 인용 근거 UI (citation drawer) + 신뢰도 breakdown 노출
`ConfidenceScorer`는 이미 evidence breadth 기반으로 점수를 계산하지만(`weighted_ranker.py`), 프런트에서 "왜 이 점수인지"를 컴포넌트별로 보여주는 화면이 없습니다.

### (결정 필요) Neo4j를 유지할지 제거할지
`.cursor/rules/biosense.mdc`는 "MVP에 별도 벡터DB/불필요 인프라 금지"를 명시하는데, Neo4j는 이미 실제 추천 로직에서 쓰이지 않습니다(Postgres join으로 대체됨). 그래프 시각화 UI(Epic C 확장)를 정말 만들 계획이면 유지, 아니면 `docker-compose.yml`에서 제거해 인프라 비용을 줄이는 게 규칙에 부합합니다.

---

## 2. Cursor용 TODO 리스트 (실제 경로 기준, 이미 구현된 것 제외)

### Epic A. 문헌 수집 파이프라인
- [ ] **A-1** `apps/api/src/biosense/infrastructure/external/pubmed_client.py` 신설 — PubMed E-utilities(`esearch`+`efetch`) 클라이언트. `KosisClient`와 동일한 패턴(`with_retry`, 실패 시 로그, 결과 없으면 빈 리스트)으로 작성
  - 기본 검색식: `ctDNA AND biosensor AND cancer`, `exosome miRNA cancer diagnosis`, `SERS cancer biomarker liquid biopsy`, `liquid biopsy early cancer detection AI`
  - PMID/제목/초록/저널/발행일/DOI 반환 → `LiteratureIngestionPipeline.ingest_text()`로 그대로 연결 가능 (신규 파이프라인 아님, 기존 메서드 재사용)
- [ ] **A-2** `europe_pmc_client.py` 신설 — Open Access full-text 확보용. 확보 후 기존 `PdfParser`/`ChunkingService` 재사용
- [ ] **A-3 (재확인만)** `korean_health_clients.py`는 이미 KOSIS/KDCA 구현됨 — 지역 커버리지 확장은 003 시드 확장 작업(Epic C)으로 처리
- [ ] **A-4** 유전자 심볼/동의어 정규화 — `domain/entities/literature.py`에 `BiomarkerSynonym` 개념 추가 또는 신규 테이블 `biomarker_synonyms` (마이그레이션 `007_biomarker_synonyms.sql`)
- [ ] **A-5** `jobs/scheduler.py`에 `scheduled_literature_harvest()` 잡 추가 (현재는 `scheduled_full_sync`만 존재, 공공데이터 전용)

### Epic B. 문헌 RAG 고도화
- [ ] **B-1 (신규)** `application/services/metric_extraction_service.py` — 논문 청크에서 sensitivity/specificity/AUC/LOD/assay time/cost 후보 문장을 정규식+LLM structured output으로 추출. 결과를 `sensor_performances`에 `source_paper_id` FK와 함께 upsert (마이그레이션으로 FK 컬럼 추가 필요, `005_literature_rag.sql` 이후 `007_performance_provenance.sql`)
- [ ] **B-2 (검증)** `hybrid_retrieval_service.py`의 reranking 로직 확인 — 필요시 cross-encoder 재랭킹 단계 추가
- [ ] **B-3 (이미 구현, 확장만)** `LiteratureRagQueryService._generate_recommendations`는 이미 citation-grounded — 인용 최소 2개 강제 로직만 추가 (`literature_rag_service.py:126` 부근)

### Epic C. 바이오마커-센서 taxonomy 확장 (신규 시드)
- [ ] **C-1** `infra/db/migrations/postgres/007_taxonomy_expansion.sql` 작성
  - `ctdna` 테이블에 `exosomal_mirna`, `ctc`(circulating tumor cell), `multi_omics` 코드 추가
  - `sensors.sensor_type`에 `SERS`, `AI_NGS`, `CRISPR` 값 추가 (현재 6종 → 확장)
  - `biomarkers`에 exosomal miRNA 후보(예: miR-21, miR-141), multi-omics panel 예시 추가
- [ ] **C-2 (이미 구현)** rule-based baseline은 `GraphRetrievalService`가 이미 수행 — 신규 taxonomy 추가 시 `biomarker_recognition_matches`, `recognition_sensor_uses` 관계 데이터만 채우면 자동으로 추천에 반영됨 (엔진 코드 수정 불필요)
- [ ] **C-3 (이미 구현)** evidence-weighted ranking — `WeightedRanker` 완료. 가중치 튜닝만 필요시 `RankingWeights` 클래스 수정
- [ ] **C-4 (이미 구현)** confidence score — `ConfidenceScorer` 완료. 상충 논문 감점 로직만 신규 추가 검토 (현재는 미반영)

### Epic D. 성능 예측 / 리포트
- [ ] **D-1** = Epic B-1과 동일 작업 (중복 방지, 하나로 통합해서 진행)
- [ ] **D-2 (신규)** 검출 방식별 prior 테이블 — `sensor_performances`에 `is_estimated: bool`, `prior_source: str` 컬럼 추가해 "문헌 실측값" vs "방식별 기본 prior" 구분
- [ ] **D-3 (부분 구현, 확장)** 프로토콜 자동 생성 — 현재 `recommendation_engine_service.py:87-97`의 fallback 스텝은 인용 없음. `Protocol` 테이블(`protocols`)에 있는 실제 프로토콜을 우선 조회하고, 없을 때만 LLM 초안 생성 + citation 필드 채우기
- [ ] **D-4 (이미 구현, 확장)** PDF 리포트 — `pdf-export.ts`는 이미 요약 카드/입력조건/추천결과를 렌더링. 참고문헌 섹션과 공유 링크 생성만 추가

### Epic E. 프론트엔드/UX
- [ ] **E-1 (이미 구현)** 케이스 입력 폼 — 확인 필요, `우선순위 선택(민감도/비용/POC/탐색)` 필드 존재 여부만 체크 후 없으면 추가
- [ ] **E-2 (이미 구현)** Top-K 카드 UI — `recommendations/page.tsx` 존재. "왜 추천했는가" rationale은 이미 표시 중(`rationale` 필드), confidence breakdown 시각화만 보강
- [ ] **E-3 (신규)** citation drawer 컴포넌트 — `apps/web/src/components/features/literature/citation-drawer.tsx` 신설 (`.cursor/rules` 컨벤션에 따라 `components/features/<feature>/` 경로 사용)
- [ ] **E-4 (부분 구현)** 모니터링 대시보드 — `/admin/page.tsx`, `MonitoringService`는 공공데이터 잡만 커버. 문헌 수집(`/literature/ingestion/status`)까지 한 화면에 통합

---

## 3. Claude Code / Cursor에 바로 붙일 프롬프트 세트

> 아래 프롬프트는 그대로 복사해서 Cursor 채팅(Agent 모드) 또는 Claude Code에 붙여 넣으면 됩니다. 저장소 루트에서 실행한다고 가정합니다. `.cursor/rules/biosense.mdc`가 자동 로드되므로 별도 스택 설명은 생략했습니다.

### 프롬프트 세트 1 — PubMed 자동 수집기 (Epic A-1)
```
apps/api/src/biosense/infrastructure/external/pubmed_client.py 를 신규 생성해줘.
korean_health_clients.py의 KosisClient 패턴(with_retry 사용, httpx.AsyncClient, 실패시 로그 후 빈 리스트 반환)을 그대로 따라줘.

요구사항:
1. NCBI E-utilities esearch + efetch 사용 (API 키는 settings.pubmed_api_key, 없으면 무료 rate limit로 동작)
2. 기본 검색식 4개를 상수로 정의: 
   "ctDNA AND biosensor AND cancer", "exosome miRNA cancer diagnosis",
   "SERS cancer biomarker liquid biopsy", "liquid biopsy early cancer detection AI"
3. 반환 타입은 새 dataclass RawPaperRecord(external_id: "pmid:{id}", title, abstract, journal, published_at, doi, authors)
4. config.py의 Settings에 pubmed_api_key, pubmed_base_url 추가하고 .env.example에도 추가
5. apps/api/src/biosense/application/services/literature_ingestion_service.py 의 
   LiteratureIngestionPipeline.ingest_text()를 재사용하는 새 유스케이스
   application/services/pubmed_harvest_service.py 를 만들어서 검색→ingest_text 루프를 수행하게 해줘
6. api/v1/ingestion.py 에 POST /v1/ingestion/literature/harvest 엔드포인트 추가 (기존 
   /ingestion/jobs/trigger 패턴을 참고)
7. tests/unit/test_pubmed_client.py, tests/integration/test_pubmed_harvest.py 작성 (httpx mock 사용)

작업 전 infra/db/migrations/postgres/ 에 스키마 변경이 필요한지 먼저 확인하고, 필요하면 
007_pubmed_harvest.sql 마이그레이션을 추가해줘. packages/openapi/openapi.yaml도 새 엔드포인트로 갱신해줘 (.cursor/rules 규칙: API 변경은 openapi.yaml 먼저).
```

### 프롬프트 세트 2 — 성능지표 자동 추출기 (Epic B-1 / D-1, 최우선 권장)
```
apps/api/src/biosense/application/services/metric_extraction_service.py 를 신규 생성해줘.

목적: paper_chunks 테이블(이미 존재, chunking_service.py로 생성됨)에서 sensitivity, specificity, 
AUC, LOD(값+단위), assay_time, sample_volume, cost 관련 정량 지표를 추출해서 
sensor_performances 테이블에 저장한다. 현재 sensor_performances는 003_seed_domain_data.sql의 
수기 값만 존재하므로, 이 서비스가 실 논문 기반 값으로 채워야 한다.

구현 방식:
1. 1차: 정규식/규칙 기반 후보 문장 탐지 (예: "sensitivity of 9X%", "LOD of X ng/mL", "AUC = 0.9X")
2. 2차: openai_client.py의 create_openai_client()로 후보 문장을 structured JSON 출력으로 정제
   (response_format={"type":"json_object"}, literature_rag_service.py의 패턴 참고)
3. 추출 결과는 sensor_performances에 upsert하되, source_paper_id, extraction_confidence, 
   is_estimated=false 컬럼 필요 (신규 마이그레이션 작성)
4. 값이 여러 논문에서 상충되면 저장은 하되 domain/services/weighted_ranker.py의 
   ConfidenceScorer가 감점할 수 있도록 conflicting_sources 플래그를 추가

domain 레이어는 SQLAlchemy를 몰라야 하므로(.cursor/rules 규칙), 추출 로직은 
application/services에, 저장은 infrastructure/persistence/postgres/literature_repository.py에 
메서드를 추가하는 방식으로 계층을 지켜줘.

literature_ingestion_service.py의 ingest_pdf_bytes / ingest_text 완료 후 자동으로 
metric_extraction_service를 호출하도록 연결해줘 (파이프라인 마지막 단계로 추가).

테스트: tests/unit/test_metric_extraction_service.py — 문장에서 값 추출 정확도 케이스 5개 이상
```

### 프롬프트 세트 3 — 바이오마커/센서 taxonomy 확장 (Epic C-1)
```
infra/db/migrations/postgres/007_taxonomy_expansion.sql 을 신규 작성해줘.
003_seed_domain_data.sql의 INSERT 패턴(ON CONFLICT DO NOTHING, JOIN으로 FK 연결)을 그대로 따라줘.

추가할 내용:
1. ctdna 테이블에 코드 추가: exosomal_mirna(엑소좀 miRNA), ctc(circulating tumor cell), 
   multi_omics(다중오믹스 패널)
2. biomarkers에 추가: miR-21, miR-141, miR-1246 (exosomal_mirna 연결), 
   multi-omics panel 예시 2-3개
3. sensors.sensor_type에 추가: SERS(광학 SERS), AI_NGS(AI 기반 NGS 분석), 
   CRISPR_dedicated(CRISPR 전용 센서 — 기존 recognition_strategies.crispr_based와는 별개로 
   센서 자체가 CRISPR 통합형인 경우)
4. biomarker_recognition_matches, recognition_sensor_uses, sensor_performances에 
   위 신규 항목들 간 관계와 초기 성능값(문헌 기반 추정치로, is_estimated=true 표기) 추가
5. 사용자가 원하는 5대 전략 카드가 실제로 조회 가능한지 확인:
   - ctDNA + AI NGS
   - 엑소좀 miRNA + AI 분류
   - 광학/SERS 기반 센싱
   - 다중오믹스 통합 패널
   - 원발부위 예측 멀티모달 리포트 (이건 단일 센서가 아니라 추천 결과 조합 로직이 필요 — 
     RecommendationEngineService에 별도 output mode로 추가할지 별도 이슈로 분리해줘)

마이그레이션 적용 후 apps/api/tests/unit/test_weighted_ranker.py, 
tests/benchmark/test_recommendation_benchmark.py가 여전히 통과하는지 확인해줘 
(신규 taxonomy가 기존 추천 결과 순위를 깨뜨리지 않는지 회귀 테스트).
```

### 프롬프트 세트 4 — citation drawer UI (Epic E-3)
```
apps/web/src/components/features/literature/citation-drawer.tsx 를 신규 생성해줘.
.cursor/rules/biosense.mdc 컨벤션: Server Component 기본, apps/web은 apps/api를 직접 import하지 
않고 lib/api-client.ts를 통해서만 통신.

요구사항:
1. recommendations/page.tsx의 각 추천 카드에서 "근거 문헌 보기" 클릭 시 열리는 슬라이드 drawer
2. evidence.literature_ids (recommendation_engine_service.py의 evidence 딕셔너리, 
   SensorRecommendation.evidence 필드)를 받아서 
   GET /v1/literature/papers/{paper_id} 로 상세 조회
3. 원문 발췌(excerpt), relevance_score, 원문 링크(DOI 있으면 링크, 없으면 papers.metadata의 
   journal명만 표시) 노출
4. 기존 apps/web/src/components/ui/* (shadcn 스타일)을 재사용, 새 UI 프리미티브 만들지 말 것
5. 로딩/빈 상태는 components/common/loading.tsx 패턴 재사용

api-client.ts에 필요한 함수가 없으면 추가해줘 (기존 함수 네이밍 컨벤션을 따를 것).
```

### 프롬프트 세트 5 — 공공데이터 우선순위 문장 생성 (Epic 우선순위 4)
```
apps/api/src/biosense/application/services/feature_extraction_service.py 와 
recommendation_engine_service.py를 확장해줘.

목적: evidence.public_health 딕셔너리(현재 incidence_rate, mortality_rate, region_code 숫자만 
포함, recommendation_engine_service.py:104-108)에 narrative 필드를 추가해서 
"부산광역시 고령층 위암 부담이 전국 평균 대비 높아 혈액 기반 조기진단 전략이 우선 검토됨" 같은 
한국어 문장을 생성한다.

구현:
1. 규칙 기반 템플릿(전국 평균 대비 X% 높음/낮음 계산) + 값이 없을 때 문장 생략
2. domain/entities/recommendation.py의 ExtractedFeatures 또는 새 dataclass에 
   public_health_narrative: str 필드 추가
3. LLM 호출 없이 순수 계산으로 구현 (비용 절감, .cursor/rules 규칙과 일치)
4. 전국 평균값은 public_health_features 테이블에서 region_code 상관없이 
   cancer_id+feature_type으로 집계해서 계산

지역 커버리지가 현재 4개 지역뿐이라(003_seed_domain_data.sql) 나머지 13개 시도 데이터는 
KOSIS 실 API 연동(korean_health_clients.py는 이미 구현됨, .env에 KOSIS_API_KEY만 설정하면 
seed 대신 실데이터 사용됨) 필요 여부를 먼저 확인하고, 없으면 seed_loader.py에 나머지 지역 
샘플 데이터를 보강해줘.
```

---

## 4. 추천 결과 JSON 스키마 (기존 dataclass 확장안)

현재 `domain/entities/recommendation.py`의 `SensorRecommendation`이 이미 아래 구조를 대부분 갖추고 있습니다. 확장이 필요한 필드만 `+`로 표시했습니다.

```json
{
  "rank": 1,
  "sensor_type": "electrochemical",
  "sensor_name": "Gold electrode EC sensor",
  "recognition_strategy": "aptamer_based",
  "recognition_name": "Aptamer-based recognition",
  "biomarker_name": "KRAS G12D mutation",
  "expected_metrics": {
    "sensitivity": 0.92,
    "specificity": 0.94,
    "lod_value": 0.10,
    "lod_unit": "ng/mL",
    "estimated_cost_usd": 35.0,
    "_+is_estimated": false,
    "_+extraction_confidence": 0.88,
    "_+source_paper_ids": ["pmid:34567890"]
  },
  "experimental_protocol": {
    "steps": ["Pretreat gold electrode with plasma", "..."],
    "reagents": ["Thiolated KRAS aptamer", "PBS buffer"],
    "duration_hours": 6.0,
    "_+step_citations": [
      {"step_index": 0, "paper_external_id": "pmid:34567890", "excerpt": "..."}
    ]
  },
  "confidence_score": 0.87,
  "_+confidence_breakdown": {
    "graph_match": 0.30,
    "literature_evidence": 0.25,
    "public_health_context": 0.10,
    "performance_data": 0.15,
    "sensor_efficiency": 0.20,
    "_+conflicting_sources_penalty": 0.0
  },
  "composite_score": 0.89,
  "rationale": "Graph path ... supports Aptamer-based recognition on Gold electrode EC sensor for KRAS G12D mutation detection.",
  "evidence": {
    "literature_ids": ["pmid:34567890", "pmid:35678901"],
    "graph_paths": ["Cancer:colorectal->Biomarker:KRAS G12D->Recognition:aptamer_based->Sensor:gold_ec"],
    "public_health": {
      "incidence_rate": 38.2,
      "mortality_rate": 12.1,
      "region_code": "KR-11",
      "_+narrative": "서울특별시 대장암 발생률이 전국 평균 대비 X% 높아..."
    },
    "_+citations": [
      {
        "paper_external_id": "pmid:34567890",
        "paper_title": "Electrochemical detection of KRAS mutations in circulating tumor DNA",
        "chunk_id": "...",
        "excerpt": "...",
        "relevance_score": 0.91
      }
    ]
  }
}
```

`+` 표시 필드는 섹션 2의 Epic B-1(성능지표 추출), D-3(프로토콜 인용), 우선순위4(narrative)가 완료되면 자연스럽게 채워집니다. 기존 `evidence.literature_ids`는 문자열 배열이라 UI에서 근거 문헌 상세(제목/발췌)를 보여주려면 추가 API 호출이 필요한데, `_+citations`처럼 확장하면 citation drawer(프롬프트 세트 4)가 한 번의 응답으로 렌더링 가능해집니다.

---

## 5. 빠른 MVP 고도화 순서 (2주 스프린트 제안)

이미 구현된 부분이 많으므로, ROADMAP.md의 Phase 5(AI Recommendation Engine)를 처음부터 다시 하지 말고 아래 순서로 진행하는 것을 권장합니다.

| 순서 | 작업 | 이유 |
|---|---|---|
| 1 | **성능지표 자동 추출기** (섹션 3 프롬프트 세트 2) | 지금 추천 결과의 민감도/특이도/LOD가 전부 하드코딩 fallback(`0.85`, `0.90` 등, `recommendation_engine_service.py:80-84`) — 데모 설득력에 가장 직접적 영향 |
| 2 | **PubMed 자동 수집기** (프롬프트 세트 1) | 1번이 돌아가려면 논문이 더 필요. 지금 4편뿐(003 시드) |
| 3 | **taxonomy 확장** (프롬프트 세트 3) | 1,2번으로 파이프라인이 검증되면, 5대 전략 카드를 위한 새 바이오마커/센서 추가 |
| 4 | **citation drawer + confidence breakdown UI** (프롬프트 세트 4) | 백엔드 근거 데이터가 갖춰진 뒤에 노출해야 빈 화면이 안 나옴 |
| 5 | **공공데이터 narrative + 지역 커버리지 확장** (프롬프트 세트 5) | 우선순위는 높지만 다른 항목과 독립적이라 병렬 진행 가능 |
| 6 | Neo4j 유지/제거 결정 + PDF 리포트에 참고문헌 섹션 추가 | 마무리 단계 |

각 단계 종료 시 회귀 테스트: `apps/api/tests/unit/test_weighted_ranker.py`, `tests/benchmark/test_recommendation_benchmark.py`, `tests/unit/test_hybrid_retrieval.py`, `tests/unit/test_literature_evaluation.py` — 이미 존재하므로 새 기능이 기존 스코어링을 깨뜨리지 않는지 매번 확인.

---

## 6. 검색 결과를 반영한 전략 방향 (Top-K 카드 목표 상태)

사용자가 제시한 5대 전략은 현재 taxonomy에 부분적으로만 존재합니다. 섹션 2/3(taxonomy 확장)이 끝나면 아래처럼 매핑됩니다.

| 전략 카드 | 현재 taxonomy 매핑 | 필요 작업 |
|---|---|---|
| ctDNA + AI NGS | `ctdna.mutation`/`methylation` biomarker 존재, `sensor_type=AI_NGS` 없음 | 프롬프트 세트 3에서 추가 |
| 엑소좀 miRNA + AI 분류 | 전혀 없음 (`exosomal_mirna` ctdna 클래스 없음) | 프롬프트 세트 3 필수 |
| 광학/SERS 기반 센싱 | `optical`(SPR)만 존재, SERS 없음 | 프롬프트 세트 3 필수 |
| 다중오믹스 통합 패널 | 없음 | 신규 `multi_omics` ctdna 클래스 + 별도 output 모드 필요 (단일 sensor 매칭이 아니라 여러 biomarker 조합) |
| 원발부위 예측 멀티모달 리포트 | 없음 — 이건 추천 엔진의 새로운 출력 모드 | `RecommendationEngineService`에 `mode="tissue_of_origin"` 같은 별도 유스케이스 분리 검토 (별도 이슈로 스코핑 권장, 이번 스프린트 범위 밖) |

원발부위 예측(multimodal report)은 기존 "biomarker→sensor" 추천과 성격이 달라서(여러 바이오마커 조합 + 확률적 분류 출력) 이번 2주 스프린트에는 포함하지 않는 것을 권장합니다. taxonomy 확장이 끝난 뒤 별도 스코핑 세션에서 다루세요.

---

## 부록 — Cursor/Claude Code에 매 세션 붙일 공통 컨텍스트

```
저장소: BioSense-GovAI (apps/web = Next.js 15, apps/api = FastAPI clean architecture)
규칙: .cursor/rules/biosense.mdc 를 항상 준수
- domain 레이어는 FastAPI/SQLAlchemy/Neo4j import 금지
- API 계약은 packages/openapi/openapi.yaml 먼저 수정
- 스키마 변경은 infra/db/migrations/postgres/ 에 순번 SQL 추가 (Alembic 아님, raw SQL)
- Redis/Kafka/Celery/별도 벡터DB 금지 (pgvector만 사용)
- 새 UI는 apps/web/src/components/features/<feature>/ 에 배치

작업 시작 전: docs/PLATFORM_UPGRADE_PLAYBOOK.md 의 섹션 0(현재 구현 현황)을 참고해서 
이미 구현된 부분을 재구현하지 말 것.
```
