"""정적 ETF 종합 EDA 대시보드 HTML 생성 및 빌드 모듈.

이 모듈은 전처리 완료된 ETF 데이터셋(`etf_processed.json`)을 읽어들여,
외부 웹서버 없이도 브라우저에서 단독 구동되는 인터랙티브 정적 HTML 대시보드
(`reports/etf_dashboard.html` 및 `docs/index.html`)를 생성합니다.

HTML 템플릿(`src/template.html`)을 기반으로 데이터셋을 인라인 임베딩하며,
브라우저 상에서 직접 네이버 API를 호출해 시세를 실시간 갱신할 수 있는
'실시간 새로고침' 기능과 4대 ECharts 시각화 및 인터랙티브 필터/테이블을 제공합니다.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# 상대 경로를 통한 유틸리티 모듈 참조 보장
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from utils import ensure_directory, resolve_relative_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def render_html_dashboard(data: Dict[str, Any]) -> str:
    """전처리된 ETF 데이터셋을 포함하는 독립형 HTML 대시보드 마크업 문자열을 생성합니다.

    `src/template.html` 템플릿 파일을 읽어 `__JSON_DATA_PAYLOAD__` 위치에
    JSON 데이터셋을 인라인 주입합니다. 이 방식은 파이썬 f-string의 자바스크립트 중괄호
    충돌(SyntaxError)을 방지하고, 프론트엔드 마크업과 백엔드 로직의 결합도를 낮춥니다.

    Args:
        data (Dict[str, Any]): 'meta', 'summary', 'items'가 포함된 종합 데이터셋.

    Returns:
        str: 데이터셋이 임베딩된 완성형 정적 HTML 마크업 문자열.

    Raises:
        FileNotFoundError: `src/template.html` 템플릿 파일이 존재하지 않는 경우 발생.
    """
    template_path = resolve_relative_path("src/template.html")
    if not template_path.exists():
        raise FileNotFoundError(f"HTML 템플릿 파일을 찾을 수 없습니다: {template_path}")

    # JSON 직렬화 시 한글 깨짐 방지를 위해 ensure_ascii=False 설정
    json_data_str = json.dumps(data, ensure_ascii=False)

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # 인라인 데이터 플레이스홀더 치환
    rendered_html = template_content.replace("__JSON_DATA_PAYLOAD__", json_data_str)
    return rendered_html


def build_dashboard_file() -> Path:
    """가공된 JSON 데이터셋을 읽어들여 대시보드 정적 HTML 파일을 빌드합니다.

    빌드 산출물:
    1. `reports/etf_dashboard.html`: 로컬 보고서 및 검토용 대시보드.
    2. `docs/index.html`: GitHub Pages 정적 웹 호스팅 배포용 복제본.

    Returns:
        Path: 생성된 정적 대시보드 HTML 파일 경로 (`reports/etf_dashboard.html`).

    Raises:
        FileNotFoundError: `data/processed/etf_processed.json`이 존재하지 않을 때 발생.
    """
    json_path = resolve_relative_path("data/processed/etf_processed.json")
    if not json_path.exists():
        raise FileNotFoundError(f"가공된 데이터셋 파일을 찾을 수 없습니다: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 대시보드 마크업 렌더링
    html_content = render_html_dashboard(data)

    # 1. reports/etf_dashboard.html 저장
    output_path = resolve_relative_path("reports/etf_dashboard.html")
    ensure_directory(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. docs/index.html 저장 (GitHub Pages 배포 호환)
    docs_index_path = resolve_relative_path("docs/index.html")
    ensure_directory(docs_index_path.parent)
    with open(docs_index_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("정적 대시보드 HTML 파일 생성 완료: %s (크기: %d bytes)", output_path, len(html_content.encode("utf-8")))
    logger.info("정적 호스팅 배포용 복제 완료: %s", docs_index_path)

    return output_path


if __name__ == "__main__":
    build_dashboard_file()
