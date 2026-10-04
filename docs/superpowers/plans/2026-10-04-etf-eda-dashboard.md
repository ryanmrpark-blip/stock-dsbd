# ETF 종합 EDA 대시보드 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 네이버 증권 ETF 실시간 API를 통해 전체 ETF 종목(약 1,170개)을 전수 수집하고, 종합 EDA(운용사, 자산군, 수익률, 괴리율, 유동성)를 지원하는 독립형 정적 HTML 대시보드를 구축한다.

**Architecture:** Python 모듈(`src/fetch_etf.py`)이 네이버 증권 API를 페이지네이션 순회하여 전수 수집 및 파생변수를 산출하여 `data/processed/etf_processed.json`에 저장하고, 대시보드 생성기(`src/generate_dashboard.py`)가 Apache ECharts와 Tailwind CSS를 결합한 독립 실행형 HTML 파일(`reports/etf_dashboard.html`)을 생성한다.

**Tech Stack:** Python 3.12 (uv), urllib/requests, HTML5, Vanilla JS, Apache ECharts 5, Tailwind CSS

**Spec:** `docs/superpowers/specs/2026-10-04-etf-eda-dashboard-design.md`

## Global Constraints
- Python 가상환경은 `uv` 전용 가상환경(`.venv`)을 사용한다.
- 파일 입출력 및 모듈 참조는 상대 경로를 엄격히 준수한다.
- 모든 파이썬 파일에는 표준 한국어 Docstring(Google Style)과 타입 힌트(`typing`)를 적용한다.
- 생성되는 대시보드는 외부 웹 서버 없이 로컬 브라우저 더블클릭이나 정적 호스팅(GitHub Pages 등) 환경에서 단독 실행 가능해야 한다.

## Review Focus
- 수집 도중 특정 페이지 응답 실패 또는 타임아웃 발생 시 재시도 로직 및 에러 핸들링
- 신규 상장 등으로 인한 결측치(6M 수익률 null, iNav 0 등) 발생 시 안전한 기본값 처리
- 1,100개 이상의 종목 데이터가 ECharts 차트 및 데이터 테이블에서 지연 없이 부드럽게 렌더링되는지 확인
- 종목 검색 및 다중 필터(브랜드, 자산군, 특수전략) 동시 적용 시 정상 필터링 동작
- CSV 내보내기 시 한글 깨짐 방지를 위한 UTF-8 BOM 인코딩 처리

---

### Task 1: API 전수 수집 및 파생변수 연산 모듈 (`src/fetch_etf.py`)

**Files:**
- Create: `src/fetch_etf.py`
- Create: `tests/test_fetch_etf.py`
- Output: `data/raw/etf_raw.json`, `data/processed/etf_processed.json`

**Interfaces:**
- Consumes: `src/utils.py:resolve_relative_path`, `ensure_directory`
- Produces: `fetch_all_etf_data() -> list[dict]`, `process_etf_data(raw_items: list[dict]) -> dict`, `save_etf_dataset(data: dict) -> None`

- [ ] **Step 1: Write test for ETF data processing and derivation logic**
  - 브랜드명 파싱 테스트 (KODEX, TIGER, ACE 등)
  - iNav 괴리율 계산식 테스트 `((currentPrice - iNav) / iNav) * 100`
  - 결측치 및 문자열 숫자 변환 테스트

- [ ] **Step 2: Run test to verify it fails**
  - Run: `uv run python -m unittest tests/test_fetch_etf.py`

- [ ] **Step 3: Implement `src/fetch_etf.py`**
  - `fetch_naver_etf_page(page: int, size: int = 100) -> dict`
  - `fetch_all_etf_data() -> list[dict]`: 1부터 hasNext=False까지 순회 수집
  - `process_etf_item(item: dict) -> dict`: 수치형 변환, 브랜드 추출, 괴리율 계산, 자산분류 매핑
  - `save_dataset()`: `data/raw/etf_raw.json`, `data/processed/etf_processed.json` 저장

- [ ] **Step 4: Run test to verify it passes**
  - Run: `uv run python -m unittest tests/test_fetch_etf.py`

- [ ] **Step 5: Run actual API fetch and verify outputs**
  - Run: `uv run python src/fetch_etf.py`
  - Output: `data/processed/etf_processed.json` 생성 및 1,170여 개 종목 수집 확인

---

### Task 2: 정적 대시보드 HTML 생성기 및 인터랙티브 뷰어 (`src/generate_dashboard.py`)

**Files:**
- Create: `src/generate_dashboard.py`
- Output: `reports/etf_dashboard.html`

**Interfaces:**
- Consumes: `data/processed/etf_processed.json`
- Produces: `generate_html_dashboard(data: dict) -> str`, `build_dashboard_file() -> Path`

- [ ] **Step 1: Write HTML 템플릿 및 렌더러 설계**
  - Tailwind CSS CDN, Apache ECharts 5 CDN, Lucide Icons CDN 적용
  - 헤더: 메타데이터, 새로고침, CSV/JSON 다운로드
  - KPI 카드 4종: 총 AUM, 총 거래대금, 상승/하락 비중, 평균 괴리율
  - ECharts 1: 운용사 점유율 Treemap / Donut
  - ECharts 2: 자산군별 AUM 및 평균 수익률
  - ECharts 3: 수익률 분포 히스토그램 & 상위/하위 TOP 10
  - ECharts 4: 거래대금 vs 괴리율 산점도 (Scatter Plot)
  - Interactive Table: 검색, 필터, 다중 정렬, 페이지네이션

- [ ] **Step 2: Implement `src/generate_dashboard.py`**
  - JSON 데이터 번들링 및 정적 HTML 생성 로직 구현
  - 브라우저 클라이언트 JS 내 CSV Export(BOM 포함) 및 실시간 필터/소팅 로직 포함

- [ ] **Step 3: Run generator and check file creation**
  - Run: `uv run python src/generate_dashboard.py`
  - Expected: `reports/etf_dashboard.html` 정상 생성 (파일 크기 및 유효성 확인)

---

### Task 3: 메인 실행 진입점 통합 (`src/main.py`)

**Files:**
- Modify: `src/main.py`
- Modify: `docs/plan.md`

**Interfaces:**
- Consumes: `src/fetch_etf.py:run_pipeline`, `src/generate_dashboard.py:build_dashboard_file`

- [ ] **Step 1: Update `src/main.py` to run full pipeline**
  - 데이터 수집 -> 전처리 -> 대시보드 HTML 빌드 원클릭 수행
  - 진행 상황 및 생성 파일 경로 출력

- [ ] **Step 2: Run full pipeline verification**
  - Run: `uv run python src/main.py`
  - Expected: 0 종료 코드, 정상 수집 및 대시보드 빌드 완료

---

### Task 4: 브라우저 동작 검증 및 최종 점검

**Files:**
- View: `reports/etf_dashboard.html`

- [ ] **Step 1: 정적 대시보드 파일 검증**
  - HTML 파일 내 문법 오류, CDN 로드 실패 여부 확인
  - ECharts 초기화 및 데이터 바인딩 확인
  - 검색 및 정렬, 다운로드 기능 테스트

- [ ] **Step 2: 최종 보고서 및 문서 업데이트**
  - `reports/report.md`에 수집 통계 및 EDA 요약 기록
  - `docs/overview.md` 및 `docs/plan.md` 진행 완료 상태 갱신
