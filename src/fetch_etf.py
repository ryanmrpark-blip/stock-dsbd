"""네이버 증권 ETF 실시간 API 데이터 수집 및 전처리 모듈.

이 모듈은 네이버 증권의 국내 ETF 목록 API(v2)를 페이지네이션으로 순회하여
상장된 전체 ETF 종목 데이터를 전수 수집하고, 결측치 보정, 운용사 브랜드 분류,
iNav 괴리율 계산, 자산군 대분류 매핑 등의 종합 EDA 파생변수를 산출하여 저장합니다.
"""

import json
import logging
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 상대 경로를 통한 유틸리티 모듈 참조 보장
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from utils import ensure_directory, resolve_relative_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 네이버 증권 ETF API 기본 엔드포인트 URL
NAVER_ETF_API_URL = "https://stock.naver.com/api/stockSecurity/etfs/v2/domestic"

# 주요 운용사 브랜드 목록 (종목명 시작 단어 기준 정합성 검증)
KNOWN_BRANDS = [
    "KODEX",   # 삼성자산운용
    "TIGER",   # 미래에셋자산운용
    "ACE",     # 한국투자신탁운용
    "RISE",    # KB자산운용
    "SOL",     # 신한자산운용
    "PLUS",    # 한화자산운용
    "HANARO",  # NH-Amundi자산운용
    "TIME",    # 타임폴리오자산운용
    "KoAct",   # 삼성액티브자산운용
    "WON",     # 우리자산운용
    "1Q",      # 하나자산운용
    "UNICORN", # 현대자산운용
    "WOORI",   # 우리자산운용 구 브랜드
    "FOCUS",   # 브레인자산운용
    "HI",      # 하이자산운용
    "TREX",    # 유진자산운용
]


def extract_brand(item_name: str) -> str:
    """ETF 종목명으로부터 운용사 브랜드를 식별하여 반환합니다.

    종목명의 맨 첫 어절(공백 기준 분리)을 분석하여 사전 정의된 주요 운용사 브랜드와
    매칭하고, 일치하지 않을 경우 '기타'로 분류합니다.

    Args:
        item_name (str): ETF 공식 종목명 (예: 'KODEX 200', 'TIGER 미국S&P500').

    Returns:
        str: 식별된 운용사 브랜드명 (예: 'KODEX', 'TIGER', '기타').

    Example:
        >>> extract_brand("KODEX 코스피100")
        'KODEX'
    """
    if not item_name or not isinstance(item_name, str):
        return "기타"

    first_word = item_name.strip().split()[0].upper()

    for brand in KNOWN_BRANDS:
        if first_word == brand.upper():
            return brand

    return "기타"


def calculate_disparity_rate(
    current_price: Optional[float], inav: Optional[float]
) -> Optional[float]:
    """iNav(순자산가치) 대비 현재 시장가격의 괴리율(%)을 계산합니다.

    괴리율 공식: ((현재가 - iNav) / iNav) * 100
    괴리율이 양수이면 시장가격이 iNav보다 고평가된 상태이고,
    음수이면 저평가(할인 거래) 상태를 나타냅니다.

    Args:
        current_price (Optional[float]): ETF 현재 시장 거래 가격.
        inav (Optional[float]): 순자산가치(Indicative Net Asset Value).

    Returns:
        Optional[float]: 소수점 둘째 자리까지 반올림된 괴리율(%), 계산 불가능 시 None.
    """
    if current_price is None or inav is None or inav <= 0:
        return None

    try:
        rate = ((current_price - inav) / inav) * 100.0
        return round(rate, 2)
    except (ZeroDivisionError, OverflowError):
        return None


def classify_asset_category(etf_type: Optional[str]) -> str:
    """네이버 ETF API의 etfType 문자열을 기반으로 직관적인 대분류 자산군을 반환합니다.

    복잡한 원본 분류(`국내주식형, 대표지수`, `해외채권형, 파생` 등)를
    통계 분석과 대시보드 시각화에 적합한 7대 대분류 카테고리로 매핑합니다.

    Args:
        etf_type (Optional[str]): API에서 제공하는 원본 etfType 문자열.

    Returns:
        str: 정규화된 자산군 대분류 ('국내주식', '해외주식', '국내채권', '해외채권',
             '파생/레버리지', '원자재/상품', '혼합자산', '기타').
    """
    if not etf_type:
        return "기타"

    type_str = str(etf_type).strip()

    if "레버리지" in type_str or "인버스" in type_str or "파생" in type_str and "채권" not in type_str and "주식" not in type_str:
        return "파생/레버리지"
    if "국내주식" in type_str:
        return "국내주식"
    if "해외주식" in type_str:
        return "해외주식"
    if "국내채권" in type_str:
        return "국내채권"
    if "해외채권" in type_str:
        return "해외채권"
    if "상품" in type_str or "원자재" in type_str or "부동산" in type_str or "리츠" in type_str:
        return "원자재/상품"
    if "혼합" in type_str:
        return "혼합자산"

    return "기타"


def _safe_float(val: Any) -> Optional[float]:
    """문자열 또는 숫자 값을 안전하게 float으로 변환하는 내부 헬퍼 함수."""
    if val is None or val == "" or val == "null":
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    """문자열 또는 숫자 값을 안전하게 int로 변환하는 내부 헬퍼 함수."""
    if val is None or val == "" or val == "null":
        return None
    try:
        return int(float(str(val).replace(",", "").strip()))
    except (ValueError, TypeError):
        return None


def process_etf_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """API 응답 단일 종목 데이터를 분석에 최적화된 딕셔너리로 전처리합니다.

    문자열로 수신된 가격, 자산, 수익률 지표를 수치형으로 안전하게 변환하고,
    브랜드, 괴리율, 자산군, 특수전략 플래그 등의 파생변수를 생성합니다.

    Args:
        item (Dict[str, Any]): 네이버 ETF API에서 반환한 단일 종목 원본 딕셔너리.

    Returns:
        Dict[str, Any]: 전처리 및 파생변수가 포함된 정제된 종목 데이터 딕셔너리.
    """
    item_name = str(item.get("itemName", "")).strip()
    item_code = str(item.get("itemCode", "")).strip()
    etf_type = str(item.get("etfType", "")).strip()

    current_price = _safe_float(item.get("currentPrice"))
    inav = _safe_float(item.get("iNav"))
    change_rate = _safe_float(item.get("changeRate"))
    change_price = _safe_float(item.get("changePrice"))
    trading_volume = _safe_int(item.get("tradingVolume"))
    trading_value = _safe_int(item.get("tradingValue"))
    total_net_assets = _safe_int(item.get("totalNetAssets"))

    return_1m = _safe_float(item.get("returnRate1m"))
    return_3m = _safe_float(item.get("returnRate3m"))
    return_6m = _safe_float(item.get("returnRate6m"))

    disparity_rate = calculate_disparity_rate(current_price, inav)
    brand = extract_brand(item_name)
    asset_class = classify_asset_category(etf_type)

    # 억원 단위 환산 (시각화 및 가독성 개선)
    aum_eok = round(total_net_assets / 100_000_000, 1) if total_net_assets is not None else 0.0
    trading_value_eok = round(trading_value / 100_000_000, 2) if trading_value is not None else 0.0

    # 특수 전략 태그 식별
    is_leverage = "레버리지" in item_name or "2X" in item_name
    is_inverse = "인버스" in item_name
    is_covered_call = "커버드콜" in item_name
    is_active = "액티브" in item_name
    is_hedged = "(H)" in item_name
    is_tr = "TR" in item_name

    return {
        "item_code": item_code,
        "item_name": item_name,
        "brand": brand,
        "current_price": current_price,
        "change_price": change_price,
        "change_rate": change_rate,
        "price_movement": item.get("priceMovement", "unchanged"),
        "trading_volume": trading_volume,
        "trading_value_krw": trading_value,
        "trading_value_eok": trading_value_eok,
        "aum_krw": total_net_assets,
        "aum_eok": aum_eok,
        "etf_type": etf_type,
        "asset_class": asset_class,
        "return_1m": return_1m,
        "return_3m": return_3m,
        "return_6m": return_6m,
        "inav": inav,
        "disparity_rate": disparity_rate,
        "is_leverage": is_leverage,
        "is_inverse": is_inverse,
        "is_covered_call": is_covered_call,
        "is_active": is_active,
        "is_hedged": is_hedged,
        "is_tr": is_tr,
    }


def fetch_naver_etf_page(page: int, size: int = 100, max_retries: int = 3) -> Dict[str, Any]:
    """네이버 증권 ETF API의 특정 페이지 데이터를 HTTP 요청을 통해 가져옵니다.

    Args:
        page (int): 요청할 페이지 번호 (1부터 시작).
        size (int): 한 페이지당 조회 항목 수 (기본값: 100).
        max_retries (int): 네트워크 장애 시 재시도 횟수.

    Returns:
        Dict[str, Any]: API 파싱 JSON 딕셔너리.

    Raises:
        RuntimeError: 최대 재시도 초과 또는 API 호출 실패 시 발생.
    """
    params = urllib.parse.urlencode({
        "listingType": "aumDesc",
        "size": size,
        "index": page,
    })
    url = f"{NAVER_ETF_API_URL}?{params}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://finance.naver.com/",
    }

    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    raw_data = response.read().decode("utf-8")
                    return json.loads(raw_data)
                else:
                    logger.warning("페이지 %d 수신 상태 코드 비정상: %d", page, response.status)
        except Exception as e:
            logger.warning("페이지 %d 수집 시도 %d/%d 실패: %s", page, attempt, max_retries, e)
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
            else:
                raise RuntimeError(f"네이버 ETF API 페이지 {page} 수집에 최종 실패했습니다: {e}") from e

    raise RuntimeError(f"네이버 ETF API 페이지 {page} 수집 실패")


def fetch_all_etf_data(max_pages: int = 30) -> List[Dict[str, Any]]:
    """네이버 증권 API의 전체 페이지를 순회하여 모든 ETF 종목을 수집합니다.

    Args:
        max_pages (int): 무한 루프 방지를 위한 최대 허용 페이지 수 (기본값: 30).

    Returns:
        List[Dict[str, Any]]: 수집된 전체 ETF 종목 원본 딕셔너리 리스트.
    """
    all_items: List[Dict[str, Any]] = []
    page = 1

    logger.info("네이버 증권 ETF 전수 수집을 시작합니다...")

    while page <= max_pages:
        logger.info("ETF 데이터 수집 중: 페이지 %d", page)
        res = fetch_naver_etf_page(page=page, size=100)
        items = res.get("items", [])
        if not items:
            break

        all_items.extend(items)
        has_next = res.get("hasNext", False)
        total_count = int(res.get("totalCount", 0))

        if not has_next or len(all_items) >= total_count:
            break

        page += 1
        time.sleep(0.1)  # 서버 부하 방지를 위한 미세 대기

    logger.info("전체 ETF 수집 완료: 총 %d개 종목", len(all_items))
    return all_items


def process_all_etf_data(raw_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """수집된 전체 ETF 원본 리스트를 전처리하고 집계 통계와 함께 패키징합니다.

    Args:
        raw_items (List[Dict[str, Any]]): API로부터 수집된 원본 종목 리스트.

    Returns:
        Dict[str, Any]: 'meta', 'summary', 'items'가 포함된 종합 데이터셋 딕셔너리.
    """
    processed_items = [process_etf_item(item) for item in raw_items]

    total_count = len(processed_items)
    total_aum_krw = sum(it["aum_krw"] or 0 for it in processed_items)
    total_trading_value_krw = sum(it["trading_value_krw"] or 0 for it in processed_items)

    rising_count = sum(1 for it in processed_items if (it["change_rate"] or 0) > 0)
    falling_count = sum(1 for it in processed_items if (it["change_rate"] or 0) < 0)
    unchanged_count = total_count - rising_count - falling_count

    valid_disparities = [it["disparity_rate"] for it in processed_items if it["disparity_rate"] is not None]
    avg_disparity = round(sum(valid_disparities) / len(valid_disparities), 3) if valid_disparities else 0.0

    # 운용사별 AUM 및 종목수 집계
    brand_stats: Dict[str, Dict[str, Any]] = {}
    for it in processed_items:
        b = it["brand"]
        if b not in brand_stats:
            brand_stats[b] = {"brand": b, "count": 0, "aum_krw": 0, "aum_eok": 0.0}
        brand_stats[b]["count"] += 1
        brand_stats[b]["aum_krw"] += it["aum_krw"] or 0

    for b, s in brand_stats.items():
        s["aum_eok"] = round(s["aum_krw"] / 100_000_000, 1)

    # 자산군별 집계
    asset_stats: Dict[str, Dict[str, Any]] = {}
    for it in processed_items:
        ac = it["asset_class"]
        if ac not in asset_stats:
            asset_stats[ac] = {"asset_class": ac, "count": 0, "aum_krw": 0, "aum_eok": 0.0}
        asset_stats[ac]["count"] += 1
        asset_stats[ac]["aum_krw"] += it["aum_krw"] or 0

    for ac, s in asset_stats.items():
        s["aum_eok"] = round(s["aum_krw"] / 100_000_000, 1)

    return {
        "meta": {
            "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_items": total_count,
            "source": NAVER_ETF_API_URL,
        },
        "summary": {
            "total_count": total_count,
            "total_aum_krw": total_aum_krw,
            "total_aum_jo": round(total_aum_krw / 1_000_000_000_000, 2),
            "total_trading_value_krw": total_trading_value_krw,
            "total_trading_value_eok": round(total_trading_value_krw / 100_000_000, 1),
            "rising_count": rising_count,
            "falling_count": falling_count,
            "unchanged_count": unchanged_count,
            "avg_disparity_rate": avg_disparity,
            "brand_stats": sorted(brand_stats.values(), key=lambda x: x["aum_krw"], reverse=True),
            "asset_stats": sorted(asset_stats.values(), key=lambda x: x["aum_krw"], reverse=True),
        },
        "items": processed_items,
    }


def save_dataset(raw_items: List[Dict[str, Any]], processed_data: Dict[str, Any]) -> Tuple[Path, Path]:
    """수집된 원본 및 가공 데이터셋을 각각 지정된 JSON 파일로 저장합니다.

    Args:
        raw_items (List[Dict[str, Any]]): API 원본 응답 종목 리스트.
        processed_data (Dict[str, Any]): 전처리 및 종합 집계 데이터셋.

    Returns:
        Tuple[Path, Path]: (raw_file_path, processed_file_path) 튜플.
    """
    raw_path = resolve_relative_path("data/raw/etf_raw.json")
    processed_path = resolve_relative_path("data/processed/etf_processed.json")

    ensure_directory(raw_path.parent)
    ensure_directory(processed_path.parent)

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_items, f, ensure_ascii=False, indent=2)

    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

    logger.info("원본 데이터셋 저장 완료: %s", raw_path)
    logger.info("가공 데이터셋 저장 완료: %s", processed_path)

    return raw_path, processed_path


def run_pipeline() -> Dict[str, Any]:
    """ETF 데이터 수집 및 전처리 전체 파이프라인을 실행합니다.

    Returns:
        Dict[str, Any]: 처리 완료된 데이터셋.
    """
    raw_items = fetch_all_etf_data()
    processed_data = process_all_etf_data(raw_items)
    save_dataset(raw_items, processed_data)
    return processed_data


if __name__ == "__main__":
    run_pipeline()
