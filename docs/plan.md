# 프로젝트 계획서: stock-dsbd

## 1. 개요
네이버 증권 실시간 ETF API를 기반으로 전체 상장 종목을 전수 수집하고 종합 EDA를 수행하는 독립형 정적 대시보드 구축 프로젝트입니다.

## 2. 단계별 마일스톤 및 진행 현황

### 1단계: 환경 설정 및 기획 (Phase 1) - [완료]
- [x] 프로젝트 워크스페이스 디렉토리 및 표준 폴더 구조 생성
- [x] uv 가상환경(`.venv`) 초기화 및 `pyproject.toml` 구성
- [x] 설계 명세서(`docs/superpowers/specs/2026-10-04-etf-eda-dashboard-design.md`) 작성

### 2단계: 데이터 수집 및 전처리 파이프라인 (Phase 2) - [완료]
- [x] 네이버 증권 ETF API 1,071개 전 종목 자동 순회 수집 모듈 구현 (`src/fetch_etf.py`)
- [x] 단위 테스트 작성 및 통과 (`tests/test_fetch_etf.py`)
- [x] 브랜드 추출, iNav 괴리율, 자산군 분류, 특수전략 태그 파생변수 산출
- [x] 원본(`data/raw/etf_raw.json`) 및 가공 데이터(`data/processed/etf_processed.json`) 저장

### 3단계: 정적 대시보드 HTML 생성기 (Phase 3) - [완료]
- [x] Apache ECharts 5 및 Tailwind CSS 기반의 독립형 대시보드 빌더 구현 (`src/generate_dashboard.py`)
- [x] 단위 테스트 작성 및 통과 (`tests/test_generate_dashboard.py`)
- [x] 4대 EDA 시각화(운용사 점유율, 자산군 AUM/수익률, 기간별 수익률, 유동성-괴리율 산점도) 탑재
- [x] 인터랙티브 필터, 정렬, 검색, 페이지네이션 및 CSV/JSON 다운로드 지원
- [x] 배포용 파일 생성: `reports/etf_dashboard.html` 및 `docs/index.html`

### 4단계: 통합 파이프라인 및 문서화 (Phase 4) - [완료]
- [x] 원클릭 실행 진입점 통합 (`src/main.py`)
- [x] 종합 EDA 결과 분석 보고서 작성 (`reports/report.md`)
- [x] 프로젝트 사용 안내서(`README.md`) 업데이트
