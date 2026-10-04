# 설계 명세서: 네이버 증권 ETF 실시간 종합 EDA 대시보드

- **작성일시**: 2026-10-04
- **프로젝트**: `stock-dsbd`
- **상태**: 승인됨 (Approved)

---

## 1. 개요 및 목적
본 프로젝트는 네이버 증권 ETF Open API(`stockSecurity/etfs/v2/domestic`)를 활용하여 국내 상장된 전체 ETF 종목(약 1,170여 개)의 실시간/스냅샷 데이터를 전수 수집하고, 종합 탐색적 데이터 분석(EDA)을 수행할 수 있는 독립형 정적 대시보드(HTML/JS)를 구축하는 것을 목표로 합니다.

정적 웹 호스팅(GitHub Pages 등) 환경에서 백엔드 서버 없이도 브라우저 단독으로 고성능 인터랙티브 차트 및 탐색 테이블을 이용할 수 있도록 설계합니다.

---

## 2. 시스템 아키텍처

```text
stock-dsbd/
├── data/
│   ├── raw/
│   │   └── etf_raw.json           # API 원본 응답 스냅샷
│   └── processed/
│       └── etf_processed.json     # 전처리 및 파생지표 산출 데이터
├── docs/
│   ├── overview.md
│   ├── plan.md
│   └── superpowers/specs/
│       └── 2026-10-04-etf-eda-dashboard-design.md
├── reports/
│   ├── figures/
│   ├── report.md
│   └── etf_dashboard.html         # 배포용 독립형 정적 대시보드 HTML
├── src/
│   ├── __init__.py
│   ├── utils.py                   # 경로 및 입출력 보조 유틸리티
│   ├── fetch_etf.py               # 네이버 API 전수 수집 및 전처리 모듈
│   ├── generate_dashboard.py      # 정적 대시보드 HTML 렌더러/빌더
│   └── main.py                    # 전체 파이프라인 원클릭 실행 진입점
├── pyproject.toml
└── README.md
```

---

## 3. 데이터 파이프라인 명세

### 3.1 네이버 증권 ETF API 수집 (`src/fetch_etf.py`)
- **엔드포인트**: `https://stock.naver.com/api/stockSecurity/etfs/v2/domestic?listingType=aumDesc&size=100&index={page}`
- **수집 방식**:
  - `index=1`부터 `hasNext`가 `false`가 되거나 전체 `totalCount`에 도달할 때까지 순차 호출 (약 12회 요청)
  - `requests` 또는 `urllib` 활용, 적절한 User-Agent 헤더 및 10초 타임아웃 적용
  - 오류 발생 시 최대 3회 재시도(Retry)
- **원본 저장**: `data/raw/etf_raw.json`

### 3.2 데이터 전처리 및 파생 변수 계산
수집된 각 종목에 대해 다음과 같은 가공을 거쳐 `data/processed/etf_processed.json`에 저장:
1. **수치형 변환**: 문자열로 수신되는 가격, 등락률, 거래량, 거래대금, AUM, 수익률, iNav를 `float`/`int`로 변환 (결측치는 `None` 처리)
2. **운용사 브랜드 (`brand`)**:
   - 종목명(예: `KODEX 200`, `TIGER 차이나전기차`, `ACE 미국배당다우존스`)의 첫 어절을 기준으로 브랜드 추출
   - 주요 브랜드: KODEX(삼성), TIGER(미래에셋), ACE(한국투자), RISE(KB), SOL(신한), PLUS(한화), HANARO(NH), TIME(타임폴리오), KoAct(삼성액티브), WON(우리), 1Q(하나) 등
3. **iNav 괴리율 (`disparity_rate`)**:
   - 공식: `((currentPrice - iNav) / iNav) * 100` (소수점 둘째 자리 반올림)
   - iNav가 0이거나 결측인 경우 `None`
4. **자산군 분류 (`asset_class`)**:
   - `etfType` 분석을 통해 대분류 부여: 국내주식형, 해외주식형, 국내채권형, 해외채권형, 혼합자산형, 원자재/상품형 등
5. **특수 전략 태그 (`strategies`)**:
   - 레버리지, 인버스, 커버드콜, 액티브, 환헤지(H), TR(Total Return) 여부 플래그

---

## 4. 정적 대시보드 UI/UX 사양 (`reports/etf_dashboard.html`)

### 4.1 기술 스택
- **HTML5 & Vanilla JavaScript**: 외부 프레임워크 빌드 과정 없이 즉시 실행
- **Tailwind CSS (CDN)**: 모던하고 일관된 핀테크 스타일 UI
- **Apache ECharts (CDN)**: 1,100여 개 데이터 포인트의 고속 렌더링, 줌/팬, 인터랙티브 툴팁 지원
- **Lucide Icons (CDN)**: 직관적인 아이콘 제공

### 4.2 화면 구성
1. **상단 컨트롤 및 메타 정보 헤더**:
   - 대시보드 제목 및 데이터 기준 시각, 총 종목 수 표시
   - "JSON 다운로드", "CSV 내보내기", "다크/라이트 테마 전환" 버튼
2. **핵심 시장 요약 KPI 카드 (4종)**:
   - 전체 ETF 순자산총액 (AUM 합계, 조원 단위)
   - 당일 총 거래대금 (억원 단위)
   - 시장 등락 현황 (상승/하락/보합 종목 수 및 비율 바)
   - 평균 괴리율 및 이상 괴리(±1% 이상) 종목 수
3. **종합 EDA 시각화 차트 그리드**:
   - **Chart 1: 운용사(브랜드)별 AUM 점유율 및 종목 수** (Treemap & Donut)
   - **Chart 2: 자산군/유형별 AUM 규모 및 평균 수익률** (Bar & Line 복합)
   - **Chart 3: 기간별(1M/3M/6M) 수익률 분포 및 TOP 10 랭킹** (Histogram & Rank Bar)
   - **Chart 4: 유동성(거래대금) vs 괴리율(iNav) 분석** (Scatter Plot, AUM 크기 버블)
4. **인터랙티브 종목 탐색 테이블**:
   - 검색창: 종목명 및 6자리 종목코드 실시간 필터
   - 셀렉트 필터: 운용사(브랜드), 자산군, 특수전략(레버리지/인버스/커버드콜 등)
   - 컬럼 정렬: AUM, 거래대금, 현재가, 등락률, 1M/3M/6M 수익률, 괴리율 기준 오름차순/내림차순
   - 페이지네이션: 25 / 50 / 100개씩 보기

---

## 5. 검증 및 테스트 계획
1. **데이터 수집 검증**:
   - `python src/fetch_etf.py`를 실행하여 1,170여 개 전 종목이 정상 저장되는지 확인
   - `data/processed/etf_processed.json` 파일 생성 및 스키마 검증
2. **대시보드 빌드 검증**:
   - `python src/generate_dashboard.py` 실행하여 `reports/etf_dashboard.html` 생성
3. **브라우저 테스트**:
   - HTML 파일을 브라우저로 열어 모든 ECharts 차트 렌더링, 필터링, 정렬, 검색 동작 확인
