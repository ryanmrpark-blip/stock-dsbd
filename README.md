# stock-dsbd

네이버 증권 ETF 실시간 API(전체 약 1,070여 개 종목)를 전수 수집하여 가공 및 종합 EDA를 수행하고, 정적 웹 호스팅(GitHub Pages 등)에 바로 배포 가능한 단일 인터랙티브 HTML 대시보드를 생성하는 프로젝트입니다.

---

## 📊 대시보드 미리보기 및 주요 기능

- **독립형 정적 HTML 배포**: 백엔드 서버 없이 브라우저 단독 구동 가능 ([`reports/etf_dashboard.html`](file:///c:/Users/ryanm/OneDrive/문서/antigravity/eda/stock-dsbd/reports/etf_dashboard.html), GitHub Pages 배포용 [`docs/index.html`](file:///c:/Users/ryanm/OneDrive/문서/antigravity/eda/stock-dsbd/docs/index.html))
- **실시간 데이터 새로고침**: 대시보드 상단의 **'실시간 새로고침'** 버튼 클릭 시, 브라우저에서 직접 네이버 증권 API를 호출(CORS 프록시 자동 폴백)하여 백엔드 재배포 없이 1,070여 개 전 종목 시세 및 지표를 즉시 최신화
- **핵심 KPI 카드**: 전체 AUM(조원), 당일 거래대금(억원), 시장 등락 비율 바, 평균 iNav 괴리율
- **4대 ECharts 시각화**:
  1. **운용사별 점유율**: KODEX, TIGER, ACE, RISE 등 트리맵 / 도넛 차트 토글
  2. **자산군별 규모 및 수익률**: 국내/해외 주식, 채권, 원자재 등 AUM 및 1M 평균 수익률 복합 차트
  3. **기간별 수익률 분석**: 1M / 3M / 6M 수익률 TOP 10 랭킹 및 분포
  4. **유동성 vs 괴리율 산점도**: 거래대금(Log) vs iNav 괴리율(%) 버블 차트 (AUM 비례)
- **인터랙티브 종목 탐색 테이블**:
  - 실시간 검색(종목명/6자리 코드)
  - 다중 필터(운용사, 자산군, 레버리지/인버스/커버드콜/액티브 등 특수전략)
  - 다중 컬럼 정렬 & 페이지네이션 (15/30/50/100개)
  - 종목 클릭 시 네이버 증권 바로가기 상세 팝업 모달
  - **CSV 내보내기**(엑셀 한글 깨짐 방지 UTF-8 BOM 탑재) & **JSON 다운로드**
  - 다크 / 라이트 테마 전환

---

## 📁 디렉토리 구조

```text
stock-dsbd/
├── .venv/                         # uv 기반 Python 가상환경
├── data/
│   ├── raw/
│   │   └── etf_raw.json           # API 원본 응답 스냅샷 (1,071개 종목)
│   └── processed/
│       └── etf_processed.json     # 전처리 및 파생변수 산출 데이터
├── docs/
│   ├── index.html                 # GitHub Pages 등 정적 웹 호스팅용 복제본
│   ├── overview.md                # 프로젝트 개요서
│   ├── plan.md                    # 단계별 개발 계획서
│   └── superpowers/               # 설계 명세서 및 구현 계획서
├── reports/
│   ├── etf_dashboard.html         # 배포용 독립형 정적 대시보드 HTML
│   └── report.md                  # 종합 EDA 결과 분석 보고서
├── src/
│   ├── __init__.py                # 패키지 초기화
│   ├── utils.py                   # 경로 보조 함수 및 공통 유틸리티
│   ├── fetch_etf.py               # 네이버 API 전수 수집 및 전처리 모듈
│   ├── template.html              # 대시보드 프론트엔드 HTML/JS 템플릿
│   ├── generate_dashboard.py      # 정적 대시보드 HTML 렌더러
│   └── main.py                    # 원클릭 실행 메인 스크립트
├── tests/
│   ├── test_fetch_etf.py          # 수집 및 파생변수 단위 테스트
│   └── test_generate_dashboard.py # 대시보드 생성기 단위 테스트
├── pyproject.toml                 # uv 프로젝트 설정
└── README.md
```

---

## 🚀 빠른 시작 (Quick Start)

### 1. 전체 파이프라인 원클릭 실행 (데이터 수집 + 대시보드 생성)
```bash
uv run python src/main.py
```
> 단 2~3초 만에 1,070여 개 전체 ETF를 수집하고 `reports/etf_dashboard.html` 및 `docs/index.html`을 생성합니다.

### 2. 대시보드 확인하기
- 로컬 파일 탐색기에서 `reports/etf_dashboard.html` 또는 `docs/index.html` 파일을 더블클릭하여 Chrome, Edge 등 어떤 브라우저에서든 바로 확인하실 수 있습니다.

### 3. 단위 테스트 실행
```bash
uv run python -m unittest discover tests
```
