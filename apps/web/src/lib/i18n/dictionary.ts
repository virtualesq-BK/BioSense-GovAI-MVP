export type Locale = 'ko' | 'en';

export const locales: Locale[] = ['ko', 'en'];

export const defaultLocale: Locale = 'ko';

/**
 * Flat key -> { ko, en } translation map.
 * Keys are dot-namespaced by area (nav, common, dashboard, recommendations, reports, admin, auth).
 */
export const dictionary = {
  // Sidebar / nav
  'nav.dashboard': { ko: '대시보드', en: 'Dashboard' },
  'nav.recommendations': { ko: '추천', en: 'Recommendations' },
  'nav.reports': { ko: '리포트', en: 'Reports' },
  'nav.rndDesign': { ko: 'R&D 설계', en: 'R&D Design' },
  'nav.admin': { ko: '관리', en: 'Admin' },
  'nav.closeMenu': { ko: '메뉴 닫기', en: 'Close menu' },
  'nav.footer': { ko: 'ctDNA · 공공데이터 · RAG', en: 'ctDNA · Public Data · RAG' },

  // Topbar / common chrome
  'common.themeToggle': { ko: '테마 전환', en: 'Toggle theme' },
  'common.languageToggle': { ko: '언어 전환', en: 'Toggle language' },
  'common.refresh': { ko: '새로고침', en: 'Refresh' },
  'common.loading': { ko: '불러오는 중...', en: 'Loading...' },
  'common.loadingData': { ko: '데이터를 불러오는 중…', en: 'Loading data…' },
  'common.noData': { ko: '데이터 없음', en: 'No data' },
  'common.connected': { ko: '연결됨', en: 'Connected' },
  'common.offline': { ko: '오프라인', en: 'Offline' },
  'common.adminConsole': { ko: '관리 콘솔', en: 'Admin Console' },
  'common.error.loadFailed': { ko: '데이터 로드 실패', en: 'Failed to load data' },
  'common.error.partial': {
    ko: '일부 데이터를 불러오지 못했습니다. Supabase(Postgres)가 연결되어 있는지 확인하세요.',
    en: 'Some data could not be loaded. Check that Supabase (Postgres) is connected.'
  },
  'common.error.apiDown': {
    ko: 'API 연결 실패',
    en: 'API connection failed'
  },
  'common.error.checkBackend': {
    ko: '백엔드가 실행 중인지 확인하세요.',
    en: 'Check that the backend is running.'
  },

  // Dashboard
  'dashboard.title': { ko: '대시보드', en: 'Dashboard' },
  'dashboard.description': {
    ko: '플랫폼 상태, 데이터 파이프라인, 문헌 인덱스 개요',
    en: 'Overview of platform health, data pipeline, and literature index'
  },
  'dashboard.stat.apiStatus': { ko: 'API 상태', en: 'API Status' },
  'dashboard.stat.ok': { ko: '정상', en: 'Healthy' },
  'dashboard.stat.degraded': { ko: '부분 장애', en: 'Degraded' },
  'dashboard.stat.down': { ko: '오프라인', en: 'Offline' },
  'dashboard.stat.needsAttention': { ko: '점검 필요', en: 'Needs attention' },
  'dashboard.stat.ingestionJobs': { ko: '수집 작업', en: 'Ingestion Jobs' },
  'dashboard.stat.completed': { ko: '완료', en: 'Completed' },
  'dashboard.stat.failed': { ko: '실패', en: 'Failed' },
  'dashboard.stat.indexedPapers': { ko: '인덱싱 논문', en: 'Indexed Papers' },
  'dashboard.stat.totalPapers': { ko: '전체', en: 'Total' },
  'dashboard.stat.papersUnit': { ko: '편', en: '' },
  'dashboard.stat.vectorChunks': { ko: '벡터 청크', en: 'Vector Chunks' },
  'dashboard.stat.ragIndex': { ko: 'RAG 검색 인덱스', en: 'RAG search index' },
  'dashboard.chart.ingestionTrend': { ko: '수집 파이프라인 추이', en: 'Ingestion Pipeline Trend' },
  'dashboard.chart.recentRecords': { ko: '최근 작업별 저장 레코드 수', en: 'Records stored per recent job' },
  'dashboard.chart.literatureStatus': { ko: '문헌 인덱스 현황', en: 'Literature Index Status' },
  'dashboard.chart.statusDistribution': { ko: '논문 처리 상태 분포', en: 'Paper processing status distribution' },
  'dashboard.chart.noLiteratureData': { ko: '문헌 데이터 없음', en: 'No literature data' },
  'dashboard.chart.metrics': { ko: '문헌·데이터 메트릭', en: 'Literature & Data Metrics' },
  'dashboard.metric.papers': { ko: '논문', en: 'Papers' },
  'dashboard.metric.chunks': { ko: '청크', en: 'Chunks' },
  'dashboard.metric.pending': { ko: '대기', en: 'Pending' },
  'dashboard.donut.indexed': { ko: '인덱싱 완료', en: 'Indexed' },
  'dashboard.donut.pending': { ko: '대기', en: 'Pending' },
  'dashboard.donut.failed': { ko: '실패', en: 'Failed' },
  'dashboard.donut.total': { ko: '합계', en: 'Total' },
  'dashboard.recentJobs.title': { ko: '최근 수집 작업', en: 'Recent Ingestion Jobs' },
  'dashboard.recentJobs.description': { ko: '공공 데이터 ETL 작업 이력', en: 'Public data ETL job history' },
  'dashboard.recentJobs.empty': { ko: '수집 작업 이력이 없습니다.', en: 'No ingestion job history yet.' },
  'dashboard.table.source': { ko: '소스', en: 'Source' },
  'dashboard.table.status': { ko: '상태', en: 'Status' },
  'dashboard.table.extracted': { ko: '추출', en: 'Extracted' },
  'dashboard.table.stored': { ko: '저장', en: 'Stored' },
  'dashboard.table.createdAt': { ko: '생성일', en: 'Created' },
  'dashboard.dependency.connected': { ko: '연결됨', en: 'Connected' },
  'dashboard.dependency.offline': { ko: '오프라인', en: 'Offline' },
  'dashboard.dependency.optional': { ko: '선택적 기능 비활성', en: 'Optional feature offline' },
  'dashboard.day.mon': { ko: '월', en: 'Mon' },
  'dashboard.day.tue': { ko: '화', en: 'Tue' },
  'dashboard.day.wed': { ko: '수', en: 'Wed' },
  'dashboard.day.thu': { ko: '목', en: 'Thu' },
  'dashboard.day.fri': { ko: '금', en: 'Fri' },

  // Recommendations
  'recommendations.title': { ko: '센서 추천', en: 'Sensor Recommendations' },
  'recommendations.description': {
    ko: '바이오마커·ctDNA 조건에 맞는 바이오센서 전략 생성',
    en: 'Generate biosensor strategies matched to biomarker/ctDNA conditions'
  },
  'recommendations.pdf': { ko: 'PDF', en: 'PDF' },
  'recommendations.saveReport': { ko: '리포트 저장', en: 'Save Report' },
  'recommendations.caseInput': { ko: '케이스 입력', en: 'Case Input' },
  'recommendations.caseInput.description': {
    ko: '암종, ctDNA 분류, 지역, 바이오마커를 설정하세요.',
    en: 'Set the cancer type, ctDNA class, region, and biomarker.'
  },
  'recommendations.field.cancerType': { ko: '암종', en: 'Cancer Type' },
  'recommendations.field.ctdnaClass': { ko: 'ctDNA 분류', en: 'ctDNA Class' },
  'recommendations.field.region': { ko: '지역', en: 'Region' },
  'recommendations.field.patientAge': { ko: '환자 연령', en: 'Patient Age' },
  'recommendations.field.biomarker': { ko: '바이오마커 (선택)', en: 'Biomarker (optional)' },
  'recommendations.field.topK': { ko: 'Top-K', en: 'Top-K' },
  'recommendations.generate': { ko: '추천 생성', en: 'Generate Recommendations' },
  'recommendations.error.generateFailed': { ko: '추천 생성 실패', en: 'Failed to generate recommendations' },
  'recommendations.loading': { ko: '하이브리드 검색 중…', en: 'Running hybrid search…' },
  'recommendations.empty.title': { ko: '추천 결과가 여기에 표시됩니다', en: 'Recommendations will appear here' },
  'recommendations.empty.description': {
    ko: '케이스를 입력하고 추천 생성을 클릭하세요.',
    en: 'Enter a case and click Generate Recommendations.'
  },
  'recommendations.confidenceComparison': { ko: '신뢰도 비교', en: 'Confidence Comparison' },
  'recommendations.confidence': { ko: '신뢰도', en: 'Confidence' },
  'recommendations.metric.sensitivity': { ko: '민감도', en: 'Sensitivity' },
  'recommendations.metric.specificity': { ko: '특이도', en: 'Specificity' },
  'recommendations.metric.lod': { ko: 'LOD', en: 'LOD' },
  'recommendations.metric.estimatedCost': { ko: '예상 비용', en: 'Est. Cost' },
  'recommendations.viewEvidence': { ko: '근거 문헌 보기', en: 'View Supporting Literature' },
  'recommendations.seoul': { ko: '서울 (11)', en: 'Seoul (11)' },

  // Reports
  'reports.title': { ko: '리포트', en: 'Reports' },
  'reports.description': {
    ko: '저장된 추천 결과 조회 및 PDF보내기',
    en: 'View saved recommendation reports and export to PDF'
  },
  'reports.listPdf': { ko: '목록 PDF', en: 'Export List PDF' },
  'reports.selectedPdf': { ko: '선택 PDF', en: 'Export Selected PDF' },
  'reports.newRecommendation': { ko: '새 추천', en: 'New Recommendation' },
  'reports.empty.title': { ko: '저장된 리포트가 없습니다', en: 'No saved reports yet' },
  'reports.empty.description': {
    ko: '추천 페이지에서 결과를 생성한 뒤 "리포트 저장"을 클릭하세요.',
    en: 'Generate a result on the Recommendations page, then click "Save Report".'
  },
  'reports.generate': { ko: '추천 생성하기', en: 'Generate Recommendation' },
  'reports.savedReports': { ko: '저장된 리포트', en: 'Saved Reports' },
  'reports.count': { ko: '건', en: 'items' },
  'reports.table.date': { ko: '날짜', en: 'Date' },
  'reports.table.cancerType': { ko: '암종', en: 'Cancer Type' },
  'reports.inputConditions': { ko: '입력 조건', en: 'Input Conditions' },
  'reports.field.cancerType': { ko: '암종', en: 'Cancer Type' },
  'reports.field.ctdna': { ko: 'ctDNA', en: 'ctDNA' },
  'reports.field.region': { ko: '지역', en: 'Region' },
  'reports.field.age': { ko: '연령', en: 'Age' },
  'reports.ageUnit': { ko: '세', en: 'yo' },
  'reports.sensitivity': { ko: '민감도', en: 'Sensitivity' },
  'reports.selectPrompt': { ko: '리포트를 선택하세요', en: 'Select a report' },
  'reports.pdfListTitle': { ko: 'BioSense 리포트 목록', en: 'BioSense Report List' },
  'reports.pdfCol.createdAt': { ko: '생성일', en: 'Created' },
  'reports.pdfCol.cancerType': { ko: '암종', en: 'Cancer Type' },
  'reports.pdfCol.region': { ko: '지역', en: 'Region' },
  'reports.pdfCol.count': { ko: '추천 수', en: 'Recs' },
  'reports.pdfCol.topSensor': { ko: 'Top 센서', en: 'Top Sensor' },

  // Admin
  'admin.title': { ko: '과학 문헌 RAG', en: 'Scientific Literature RAG' },
  'admin.description': {
    ko: 'PDF 수집 → 청킹 → pgvector 임베딩 → 바이오마커 추천 + 인용',
    en: 'PDF ingestion → chunking → pgvector embedding → biomarker recommendations + citations'
  },
  'admin.console.title': { ko: '관리 콘솔', en: 'Admin Console' },
  'admin.console.description': {
    ko: '데이터 수집 파이프라인 및 문헌 RAG 관리',
    en: 'Manage the data ingestion pipeline and literature RAG'
  },
  'admin.console.error.loadFailed': { ko: '로드 실패', en: 'Failed to load' },
  'admin.console.error.triggerFailed': { ko: '트리거 실패', en: 'Trigger failed' },
  'admin.console.stat.totalJobs': { ko: '총 수집 작업', en: 'Total Ingestion Jobs' },
  'admin.console.stat.completed': { ko: '완료', en: 'Completed' },
  'admin.console.stat.failed': { ko: '실패', en: 'Failed' },
  'admin.console.stat.indexedPapers': { ko: '인덱싱 논문', en: 'Indexed Papers' },
  'admin.console.stat.chunks': { ko: '청크', en: 'Chunks' },
  'admin.console.publicData.title': { ko: '공공 데이터 수집', en: 'Public Data Ingestion' },
  'admin.console.publicData.description': {
    ko: 'KOSIS / KDCA ETL 파이프라인 수동 실행',
    en: 'Manually run the KOSIS / KDCA ETL pipeline'
  },
  'admin.console.source': { ko: '소스', en: 'Source' },
  'admin.console.source.full': { ko: '전체 동기화', en: 'Full Sync' },
  'admin.console.running': { ko: '실행 중…', en: 'Running…' },
  'admin.console.runIngestion': { ko: '수집 실행', en: 'Run Ingestion' },
  'admin.console.literatureRag.title': { ko: '문헌 RAG', en: 'Literature RAG' },
  'admin.console.literatureRag.description': {
    ko: 'PDF 업로드, RAG 쿼리, 평가 도구',
    en: 'PDF upload, RAG query, and evaluation tools'
  },
  'admin.console.indexed': { ko: '인덱싱', en: 'Indexed' },
  'admin.console.pending': { ko: '대기', en: 'Pending' },
  'admin.console.failed': { ko: '실패', en: 'Failed' },
  'admin.console.openLiteratureAdmin': { ko: '문헌 RAG Admin 열기', en: 'Open Literature RAG Admin' },
  'admin.console.jobHistory.title': { ko: '수집 작업 이력', en: 'Ingestion Job History' },
  'admin.console.jobHistory.empty': { ko: '작업 이력 없음', en: 'No job history' },
  'admin.console.table.id': { ko: 'ID', en: 'ID' },
  'admin.console.table.source': { ko: '소스', en: 'Source' },
  'admin.console.table.status': { ko: '상태', en: 'Status' },
  'admin.console.table.extractedToStored': { ko: '추출→저장', en: 'Extracted→Stored' },
  'admin.console.table.error': { ko: '오류', en: 'Error' },
  'admin.stat.total': { ko: '전체', en: 'Total' },
  'admin.stat.indexed': { ko: '인덱싱됨', en: 'Indexed' },
  'admin.stat.pending': { ko: '대기', en: 'Pending' },
  'admin.stat.failed': { ko: '실패', en: 'Failed' },
  'admin.stat.chunks': { ko: '청크', en: 'Chunks' },
  'admin.tab.papers': { ko: '논문 수집', en: 'Paper Ingestion' },
  'admin.tab.query': { ko: 'RAG 쿼리', en: 'RAG Query' },
  'admin.tab.evaluation': { ko: '평가', en: 'Evaluation' },
  'admin.ingestSample': { ko: '샘플 논문 텍스트 수집', en: 'Ingest Sample Paper Text' },
  'admin.uploadPdf': { ko: 'PDF 업로드', en: 'Upload PDF' },
  'admin.table.title': { ko: '제목', en: 'Title' },
  'admin.table.id': { ko: 'ID', en: 'ID' },
  'admin.table.status': { ko: '상태', en: 'Status' },
  'admin.table.chunks': { ko: '청크', en: 'Chunks' },
  'admin.table.empty': { ko: '수집된 논문이 없습니다.', en: 'No papers ingested yet.' },
  'admin.query.placeholder': { ko: 'RAG 쿼리', en: 'RAG query' },
  'admin.query.biomarkerPlaceholder': { ko: '바이오마커 (선택)', en: 'Biomarker (optional)' },
  'admin.query.generate': { ko: '바이오마커 추천 생성', en: 'Generate Biomarker Recommendations' },
  'admin.query.confidence': { ko: '신뢰도', en: 'confidence' },
  'admin.eval.queryPlaceholder': { ko: '평가 쿼리', en: 'Evaluation query' },
  'admin.eval.termsPlaceholder': { ko: '기대 키워드 (쉼표 구분)', en: 'Expected keywords (comma-separated)' },
  'admin.eval.run': { ko: '검색 품질 평가 실행', en: 'Run Retrieval Quality Evaluation' },
  'admin.eval.history': { ko: '평가 이력', en: 'Evaluation History' },
  'admin.error.loadFailed': { ko: '불러오기 실패', en: 'Failed to load' },
  'admin.error.ingestFailed': { ko: '수집 실패', en: 'Ingestion failed' },
  'admin.error.uploadFailed': { ko: '업로드 실패', en: 'Upload failed' },
  'admin.error.queryFailed': { ko: '쿼리 실패', en: 'Query failed' },
  'admin.error.evalFailed': { ko: '평가 실패', en: 'Evaluation failed' },

  // Citation drawer
  'citation.close': { ko: '닫기', en: 'Close' },
  'citation.title': { ko: '근거 문헌', en: 'Supporting Literature' },
  'citation.subtitleFor': { ko: '추천에 사용된 문헌', en: 'literature used for this recommendation' },
  'citation.subtitleDefault': { ko: '추천 근거 문헌', en: 'Recommendation supporting literature' },
  'citation.loading': { ko: '문헌을 불러오는 중…', en: 'Loading literature…' },
  'citation.loadFailed': { ko: '문헌을 불러오지 못했습니다', en: 'Failed to load literature' },
  'citation.empty.title': { ko: '연결된 근거 문헌이 없습니다', en: 'No linked supporting literature' },
  'citation.empty.description': {
    ko: '문헌 인제스트 후 추천을 다시 생성해 보세요.',
    en: 'Try regenerating the recommendation after ingesting literature.'
  },
  'citation.relevance': { ko: '관련도', en: 'Relevance' },
  'citation.noExcerpt': { ko: '원문 발췌가 없습니다.', en: 'No excerpt available.' },
  'citation.noDoiJournal': { ko: 'DOI / 저널 정보 없음', en: 'No DOI / journal info' },

  // Auth
  'auth.signOut': { ko: '로그아웃', en: 'Sign out' },
  'auth.profile': { ko: '프로필', en: 'Profile' },
  'auth.signIn': { ko: '로그인', en: 'Sign In' },
  'auth.signIn.description': {
    ko: 'Supabase 계정으로 BioSense-GovAI에 접속합니다.',
    en: 'Access BioSense-GovAI with your Supabase account.'
  },
  'auth.email': { ko: '이메일', en: 'Email' },
  'auth.password': { ko: '비밀번호', en: 'Password' },
  'auth.signingIn': { ko: '로그인 중…', en: 'Signing in…' },
  'auth.noAccount': { ko: '계정이 없으신가요?', en: "Don't have an account?" },
  'auth.signUp': { ko: '회원가입', en: 'Sign Up' },
  'auth.loading': { ko: '로딩 중…', en: 'Loading…' },
  'auth.signUp.description': {
    ko: 'Supabase Auth로 새 계정을 만듭니다.',
    en: 'Create a new account with Supabase Auth.'
  },
  'auth.signingUp': { ko: '가입 중…', en: 'Signing up…' },
  'auth.confirmationEmailSent': {
    ko: '확인 이메일을 발송했습니다. 메일함을 확인한 뒤 로그인하세요.',
    en: 'A confirmation email has been sent. Check your inbox, then sign in.'
  },
  'auth.haveAccount': { ko: '이미 계정이 있으신가요?', en: 'Already have an account?' },

  // Landing page
  'landing.nav.features': { ko: '기능', en: 'Features' },
  'landing.nav.workflow': { ko: '워크플로', en: 'Workflow' },
  'landing.nav.signIn': { ko: '로그인', en: 'Sign In' },
  'landing.nav.dashboard': { ko: '대시보드', en: 'Dashboard' },
  'landing.getStarted': { ko: '시작하기', en: 'Get Started' },
  'landing.hero.badge': { ko: 'ctDNA · 바이오센서 공동 설계 SaaS', en: 'ctDNA · Biosensor Co-design SaaS' },
  'landing.hero.title1': { ko: 'AI 기반 바이오마커–바이오센서', en: 'AI-Powered Biomarker–Biosensor' },
  'landing.hero.title2': { ko: '조기 암 진단 플랫폼', en: 'Early Cancer Detection Platform' },
  'landing.hero.description': {
    ko: 'ctDNA 분자 특성과 한국 공공 보건 데이터, 과학 문헌을 결합하여 최적의 바이오센서 전략을 추천하고 리포트로보냅니다.',
    en: 'Combines ctDNA molecular characteristics, Korean public health data, and scientific literature to recommend optimal biosensor strategies and deliver reports.'
  },
  'landing.hero.generate': { ko: '추천 생성하기', en: 'Generate Recommendations' },
  'landing.hero.viewDashboard': { ko: '대시보드 보기', en: 'View Dashboard' },
  'landing.hero.audience': {
    ko: '대상: 바이오센서 스타트업 · 대학 연구자 · 진단 기업',
    en: 'For: Biosensor startups · University researchers · Diagnostics companies'
  },
  'landing.features.title': { ko: '핵심 기능', en: 'Core Features' },
  'landing.features.description': {
    ko: '연구부터 프로토타입까지, 데이터 기반 의사결정을 지원합니다.',
    en: 'Supporting data-driven decisions from research to prototype.'
  },
  'landing.feature1.title': { ko: '하이브리드 추천 엔진', en: 'Hybrid Recommendation Engine' },
  'landing.feature1.description': {
    ko: '지식 그래프 + RAG 문헌 + 공공 보건 데이터를 결합한 센서 전략 추천',
    en: 'Sensor strategy recommendations combining knowledge graphs, RAG literature, and public health data'
  },
  'landing.feature2.title': { ko: '한국 공공 데이터', en: 'Korean Public Data' },
  'landing.feature2.description': {
    ko: 'KOSIS·KDCA 암 발생률·사망률을 지역별로 통합 분석',
    en: 'Integrated regional analysis of KOSIS/KDCA cancer incidence and mortality data'
  },
  'landing.feature3.title': { ko: '과학 문헌 RAG', en: 'Scientific Literature RAG' },
  'landing.feature3.description': {
    ko: 'PDF 파싱, 벡터 검색, 인용 기반 근거 제시',
    en: 'PDF parsing, vector search, and citation-backed evidence'
  },
  'landing.feature4.title': { ko: '성능 지표 예측', en: 'Performance Metric Prediction' },
  'landing.feature4.description': {
    ko: '민감도·특이도·LOD·비용·실험 프로토콜 자동 출력',
    en: 'Automatic output of sensitivity, specificity, LOD, cost, and experimental protocol'
  },
  'landing.feature5.title': { ko: '신뢰도 스코어링', en: 'Confidence Scoring' },
  'landing.feature5.description': {
    ko: '가중 랭킹과 confidence score로 추천 품질 정량화',
    en: 'Quantifying recommendation quality with weighted ranking and confidence scores'
  },
  'landing.feature6.title': { ko: '실시간 모니터링', en: 'Real-time Monitoring' },
  'landing.feature6.description': {
    ko: '데이터 수집 파이프라인·문헌 인덱싱 상태 대시보드',
    en: 'Dashboard for data ingestion pipeline and literature indexing status'
  },
  'landing.diagrams.title': { ko: '바이오센서 설계 개념도', en: 'Biosensor Design Concepts' },
  'landing.diagrams.description': {
    ko: 'BioSense-GovAI가 근거로 삼는 바이오센서 신호 변환, 멀티오믹스 바이오마커 발굴, 액체생검 랩온어칩, 생체인식-트랜스듀서 워크플로의 핵심 개념입니다.',
    en: 'The core biosensor signal transduction, multi-omics biomarker discovery, liquid-biopsy lab-on-a-chip, and biorecognition-transducer workflow concepts that BioSense-GovAI designs against.'
  },
  'landing.diagrams.signalPipeline.title': { ko: '바이오센서 신호 변환 경로', en: 'Biosensor Signal Transduction Path' },
  'landing.diagrams.signalPipeline.description': {
    ko: '분자 인식 → 신호 변환 → 신호 기록/디스플레이로 이어지는 전기화학 바이오센서의 기본 구조',
    en: 'The core electrochemical biosensor chain: molecular recognition → signal transformation → signal recording and display'
  },
  'landing.diagrams.multiOmics.title': { ko: '멀티오믹스 바이오마커 발굴', en: 'Multi-Omics Biomarker Discovery' },
  'landing.diagrams.multiOmics.description': {
    ko: 'DNA·RNA·단백질·대사체 각 오믹스 계층을 생물정보학·생물통계학으로 통합해 바이오마커를 도출',
    en: 'Integrating genomics, transcriptomics, proteomics, and metabolomics via bioinformatics and biostatistics to derive biomarkers'
  },
  'landing.diagrams.labOnChip.title': { ko: '액체생검 기반 Lab-on-a-Chip', en: 'Liquid-Biopsy Lab-on-a-Chip' },
  'landing.diagrams.labOnChip.description': {
    ko: '환자 혈액 샘플에서 ctDNA/CTC/엑소좀을 포집·분석해 다시 임상 판단으로 순환하는 흐름',
    en: 'Capturing and analyzing ctDNA/CTCs/exosomes from a patient blood sample, feeding back into clinical decisions'
  },
  'landing.diagrams.workflow.title': { ko: '생체인식-트랜스듀서 워크플로', en: 'Biorecognition–Transducer Workflow' },
  'landing.diagrams.workflow.description': {
    ko: '검체(타액/혈액/소변)에서 생체인식 소자(핵산·압타머·엑소좀·단백질·항체)를 거쳐 전기화학/광학/압전/FET 트랜스듀서로 신호를 처리',
    en: 'From sample (saliva/blood/urine) through biorecognition elements (nucleic acid, aptamer, exosome, protein, antibody) to electrochemical/optical/piezoelectric/FET transducers'
  },
  'landing.workflow.title': { ko: '워크플로', en: 'Workflow' },
  'landing.workflow.step1.title': { ko: '케이스 입력', en: 'Case Input' },
  'landing.workflow.step1.description': {
    ko: '암종·ctDNA·지역·바이오마커 조건 설정',
    en: 'Set cancer type, ctDNA, region, and biomarker conditions'
  },
  'landing.workflow.step2.title': { ko: 'AI 추천', en: 'AI Recommendation' },
  'landing.workflow.step2.description': {
    ko: '하이브리드 검색으로 센서 전략 Top-K 생성',
    en: 'Generate Top-K sensor strategies via hybrid search'
  },
  'landing.workflow.step3.title': { ko: '리포트', en: 'Report' },
  'landing.workflow.step3.description': { ko: 'PDF보내기 및 팀 공유', en: 'Export to PDF and share with your team' },
  'landing.footer.admin': { ko: '관리', en: 'Admin' },
  'landing.footer.apiDocs': { ko: 'API 문서', en: 'API Docs' },

  // R&D Design report (§13/§22)
  'rndDesign.title': { ko: 'R&D 설계 리포트', en: 'R&D Design Report' },
  'rndDesign.description': {
    ko: '암종·바이오마커·목표를 입력하면 근거 기반 바이오마커-센서 공동설계 리포트를 생성합니다',
    en: 'Enter a cancer, biomarker, and goal to generate an evidence-based biomarker–sensor co-design report'
  },
  'rndDesign.caseInput': { ko: '설계 조건', en: 'Design Input' },
  'rndDesign.field.cancer': { ko: '암종', en: 'Cancer' },
  'rndDesign.field.biomarkerType': { ko: 'ctDNA 분류 (선택)', en: 'ctDNA Class (optional)' },
  'rndDesign.field.biomarkerType.any': { ko: '전체', en: 'Any' },
  'rndDesign.field.targetGene': { ko: '타겟 유전자 (선택)', en: 'Target Gene (optional)' },
  'rndDesign.field.goal': { ko: '목표', en: 'Goal' },
  'rndDesign.field.goal.placeholder': {
    ko: '예: 조기진단용 ctDNA biosensor 설계',
    en: 'e.g. Design an early-detection ctDNA biosensor'
  },
  'rndDesign.field.region': { ko: '지역', en: 'Region' },
  'rndDesign.field.patientAge': { ko: '환자 연령', en: 'Patient Age' },
  'rndDesign.generate': { ko: '리포트 생성', en: 'Generate Report' },
  'rndDesign.loading': { ko: '파이프라인 실행 중…', en: 'Running design pipeline…' },
  'rndDesign.error.generateFailed': { ko: '리포트 생성 실패', en: 'Failed to generate report' },
  'rndDesign.empty.title': { ko: '리포트가 여기에 표시됩니다', en: 'The report will appear here' },
  'rndDesign.empty.description': {
    ko: '왼쪽에서 조건을 입력하고 리포트 생성을 눌러주세요',
    en: 'Enter your inputs on the left and click Generate Report'
  },
  'rndDesign.section.epidemiology': { ko: '1. 역학적 근거', en: '1. Epidemiological Evidence' },
  'rndDesign.section.biomarkerCandidates': { ko: '2. 바이오마커 후보', en: '2. Biomarker Candidates' },
  'rndDesign.section.molecular': { ko: '3. 분자적 특성', en: '3. Molecular Characteristics' },
  'rndDesign.section.recognition': { ko: '4. 인식 전략', en: '4. Recognition Strategy' },
  'rndDesign.section.sensors': { ko: '5-7. 센서 후보 및 성능 근거', en: '5-7. Sensor Candidates & Performance Evidence' },
  'rndDesign.section.evidence': { ko: '7. 기존 근거 문헌', en: '7. Existing Evidence' },
  'rndDesign.section.performance': { ko: '8. 예상 성능', en: '8. Expected Performance' },
  'rndDesign.section.confidence': { ko: '9. 근거 신뢰도', en: '9. Evidence Confidence' },
  'rndDesign.section.protocol': { ko: '10. 실험 설계 가설', en: '10. Experimental Design Hypothesis' },
  'rndDesign.section.limitations': { ko: '11. 한계 및 주의사항', en: '11. Data Limitations' },
  'rndDesign.section.references': { ko: '12. 참고 문헌', en: '12. References' },
  'rndDesign.noBiomarkerFound': {
    ko: '이 조건에 맞는 바이오마커 후보를 그래프에서 찾지 못했습니다',
    en: 'No biomarker candidates found in the graph for this input'
  },
  'rndDesign.missingData': { ko: '데이터 없음', en: 'No data' },
  'rndDesign.estimated': { ko: '문헌 기반 추정값', en: 'Literature-derived estimate' },
  'rndDesign.measured': { ko: '실측값', en: 'Measured' },
  'rndDesign.aiSuggested': { ko: 'AI 제안 (미검증)', en: 'AI-suggested (unvalidated)' },
  'rndDesign.curatedProtocol': { ko: '기존 프로토콜', en: 'Curated protocol' },
  'rndDesign.regionAverage': { ko: '전국 평균', en: 'National average' },
  'rndDesign.workflow.title': { ko: '바이오센서 파이프라인', en: 'Biosensor Pipeline' },
  'rndDesign.workflow.description': {
    ko: '검체 → 생체 인식 → 트랜스듀서 → 신호 판독 흐름으로 이 설계가 어디까지 근거를 확보했는지 보여줍니다.',
    en: 'Sample → biorecognition → transducer → signal readout — shows how far this design is backed by real evidence.'
  },
  'rndDesign.workflow.sample': { ko: '검체/적응증', en: 'Sample / Target' },
  'rndDesign.workflow.recognition': { ko: '생체 인식', en: 'Biorecognition' },
  'rndDesign.workflow.transducer': { ko: '트랜스듀서', en: 'Transducer' },
  'rndDesign.workflow.signal': { ko: '신호 판독', en: 'Signal Readout' },
  'rndDesign.workflow.sensitivity': { ko: '민감도', en: 'Sensitivity' }
} as const satisfies Record<string, Record<Locale, string>>;

export type TranslationKey = keyof typeof dictionary;
