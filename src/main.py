"""stock-dsbd 메인 실행 진입점 모듈.

이 모듈은 네이버 증권 ETF 실시간 API 수집 파이프라인과
종합 EDA 대시보드(정적 HTML) 생성기를 통합하여 원클릭으로 구동하는 메인 스크립트입니다.
"""

import logging
import sys
import time
from pathlib import Path

# 상대 경로를 통한 모듈 참조 보장
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

# Windows 콘솔 인코딩(CP949) 이모지 및 다국어 인코딩 에러 방지
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fetch_etf import run_pipeline as fetch_and_process_etf
from generate_dashboard import build_dashboard_file
from utils import ensure_directory, get_project_root, resolve_relative_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def initialize_workspace() -> None:
    """프로젝트 실행에 필요한 데이터 및 산출물 디렉토리를 자동 점검하고 생성합니다.

    실행 환경이 새로 클론되었거나 디렉토리가 부재할 경우 발생할 수 있는
    `FileNotFoundError`를 방지하기 위해 사전 실행됩니다.
    """
    ensure_directory(resolve_relative_path("data/raw"))
    ensure_directory(resolve_relative_path("data/processed"))
    ensure_directory(resolve_relative_path("reports/figures"))
    ensure_directory(resolve_relative_path("docs"))


def main() -> int:
    """전체 데이터 수집 및 대시보드 빌드 파이프라인을 실행합니다.

    실행 단계:
    1. 작업 디렉토리 점검 및 초기화
    2. 네이버 증권 ETF 실시간 API 전수 수집 및 가공 (`data/processed/etf_processed.json`)
    3. 고성능 정적 대시보드 HTML 생성 (`reports/etf_dashboard.html`, `docs/index.html`)

    Returns:
        int: 정상 수행 시 0 반환, 예외 발생 시 1 반환.
    """
    start_time = time.time()
    root_dir: Path = get_project_root()

    print("=" * 70)
    print("  [stock-dsbd] 네이버 증권 ETF 종합 EDA 대시보드 파이프라인")
    print("=" * 70)
    print(f"  * 프로젝트 루트: {root_dir}")
    print("  * 작업 환경 초기화 점검 중...")
    initialize_workspace()

    try:
        # 1단계: 실시간 데이터 전수 수집 및 전처리
        print("\n  [1/2] 네이버 증권 ETF 전 종목 데이터 수집 및 EDA 파생변수 산출 중...")
        processed_data = fetch_and_process_etf()
        summary = processed_data.get("summary", {})
        total_items = summary.get("total_count", 0)
        total_aum_jo = summary.get("total_aum_jo", 0.0)
        total_trading_eok = summary.get("total_trading_value_eok", 0.0)

        print(f"  -> 수집 완료: 총 {total_items:,}개 ETF 종목")
        print(f"  -> 전체 순자산(AUM): {total_aum_jo:,.2f}조 원 | 일일 거래대금: {total_trading_eok:,.1f}억 원")

        # 2단계: 정적 대시보드 HTML 빌드
        print("\n  [2/2] 정적 대시보드 HTML(ECharts + Tailwind) 빌드 중...")
        dashboard_path = build_dashboard_file()
        elapsed = time.time() - start_time

        print("\n" + "=" * 70)
        print("  [SUCCESS] 대시보드 생성 성공!")
        print("=" * 70)
        print(f"  * 소요 시간: {elapsed:.2f}초")
        print(f"  * 대시보드 파일: {dashboard_path}")
        print(f"  * 정적 호스팅 파일: {resolve_relative_path('docs/index.html')}")
        print("  * 브라우저에서 'reports/etf_dashboard.html'을 더블클릭하여 바로 확인하실 수 있습니다.")
        print("=" * 70)
        return 0

    except Exception as e:
        logger.exception("대시보드 생성 파이프라인 실행 중 오류 발생: %s", e)
        print(f"\n[ERROR] 오류 발생: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
