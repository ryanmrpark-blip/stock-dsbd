# 프로젝트 개요: stock-dsbd

## 1. 프로젝트 목적
- 주식/금융 데이터 수집, 가공 및 탐색적 데이터 분석(EDA)
- 대시보드(Dashboard) 시각화 및 주요 지표 모니터링 환경 구축

## 2. 디렉토리 구조
```text
stock-dsbd/
├── .venv/                     # uv 기반 파이썬 가상환경
├── data/
│   ├── raw/                   # 원본 데이터 수집 저장소
│   └── processed/             # 가공 및 정제된 데이터셋
├── docs/
│   ├── overview.md            # 프로젝트 개요 및 명세서
│   └── plan.md                # 진행 계획 및 마일스톤
├── reports/
│   ├── figures/               # 시각화 차트 및 이미지
│   └── report.md              # 분석 및 대시보드 결과 보고서
├── src/
│   ├── __init__.py            # 소스 패키지 초기화
│   ├── utils.py               # 공통 보조 함수 및 데이터 로더 유틸리티
│   └── main.py                # 실행 진입점 메인 스크립트
├── pyproject.toml             # uv 패키지 및 의존성 설정
├── README.md                  # 프로젝트 안내 문서
└── .gitignore
```

## 3. 작업 원칙
- **가상환경**: Python 가상환경은 항상 `uv`만 사용 (`.venv`)
- **경로 관리**: 모든 파일 참조 및 입출력은 세부 프로젝트 기준 **상대 경로** 사용
