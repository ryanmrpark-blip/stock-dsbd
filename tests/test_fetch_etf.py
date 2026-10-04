"""네이버 증권 ETF 데이터 수집 및 전처리 단위 테스트 모듈.

이 테스트 모듈은 API 응답 파싱, 브랜드명 추출, iNav 괴리율 계산,
결측치 안전 처리 및 자산군 분류 로직의 정확성을 검증합니다.
"""

import unittest
from typing import Any, Dict


class TestFetchETF(unittest.TestCase):
    """ETF 데이터 파싱 및 파생변수 산출 로직 검증 테스트 케이스."""

    def test_extract_brand(self) -> None:
        """종목명으로부터 운용사 브랜드를 정확히 추출하는지 검증합니다."""
        from src.fetch_etf import extract_brand

        self.assertEqual(extract_brand("KODEX 200"), "KODEX")
        self.assertEqual(extract_brand("TIGER 차이나전기차SOLACTIVE"), "TIGER")
        self.assertEqual(extract_brand("ACE 미국배당다우존스"), "ACE")
        self.assertEqual(extract_brand("RISE 200위클리커버드콜"), "RISE")
        self.assertEqual(extract_brand("SOL 코리아고배당"), "SOL")
        self.assertEqual(extract_brand("1Q 머니마켓액티브"), "1Q")
        self.assertEqual(extract_brand("알수없는ETF"), "기타")

    def test_calculate_disparity_rate(self) -> None:
        """iNav 대비 시장가격의 괴리율(%) 산출 공식을 검증합니다."""
        from src.fetch_etf import calculate_disparity_rate

        # 정상 케이스: 현재가 10100, iNav 10000 -> +1.0%
        rate = calculate_disparity_rate(10100.0, 10000.0)
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, 1.0, places=2)

        # 음수 괴리율: 현재가 9900, iNav 10000 -> -1.0%
        rate_neg = calculate_disparity_rate(9900.0, 10000.0)
        self.assertIsNotNone(rate_neg)
        self.assertAlmostEqual(rate_neg, -1.0, places=2)

        # 0 나누기 방어: iNav가 0이거나 None일 경우 None 반환
        self.assertIsNone(calculate_disparity_rate(10000.0, 0.0))
        self.assertIsNone(calculate_disparity_rate(10000.0, None))

    def test_classify_asset_category(self) -> None:
        """etfType 문자열 기반 자산군 대분류 매핑을 검증합니다."""
        from src.fetch_etf import classify_asset_category

        self.assertEqual(classify_asset_category("국내주식형, 대표지수"), "국내주식")
        self.assertEqual(classify_asset_category("해외주식형, 테마"), "해외주식")
        self.assertEqual(classify_asset_category("국내채권형, 일반"), "국내채권")
        self.assertEqual(classify_asset_category("해외채권형, 파생"), "해외채권")
        self.assertEqual(classify_asset_category("국내파생, 레버리지"), "파생/레버리지")
        self.assertEqual(classify_asset_category("해외상품"), "원자재/상품")
        self.assertEqual(classify_asset_category("국내혼합형, 주식/채권"), "혼합자산")

    def test_process_etf_item(self) -> None:
        """단일 종목 원본 딕셔너리의 수치 정제 및 파생변수 생성 종합 검증."""
        from src.fetch_etf import process_etf_item

        mock_item: Dict[str, Any] = {
            "itemCode": "237350",
            "itemName": "KODEX 코스피100",
            "currentPrice": "89275",
            "changePrice": "275",
            "changeRate": "0.31",
            "priceMovement": "rising",
            "tradingVolume": "100873",
            "tradingValue": "8983000000",
            "totalNetAssets": "953234740474",
            "etfType": "국내주식형, 대표지수",
            "returnRate1m": "3.80",
            "returnRate3m": "-17.77",
            "returnRate6m": "38.26",
            "iNav": "89465.04",
        }

        processed = process_etf_item(mock_item)

        self.assertEqual(processed["item_code"], "237350")
        self.assertEqual(processed["item_name"], "KODEX 코스피100")
        self.assertEqual(processed["brand"], "KODEX")
        self.assertEqual(processed["current_price"], 89275)
        self.assertEqual(processed["change_rate"], 0.31)
        self.assertEqual(processed["price_movement"], "rising")
        self.assertEqual(processed["trading_value_krw"], 8983000000)
        self.assertEqual(processed["aum_krw"], 953234740474)
        self.assertEqual(processed["asset_class"], "국내주식")
        self.assertEqual(processed["return_1m"], 3.80)
        self.assertEqual(processed["return_3m"], -17.77)
        self.assertEqual(processed["return_6m"], 38.26)
        self.assertAlmostEqual(processed["disparity_rate"], -0.21, places=2)


if __name__ == "__main__":
    unittest.main()
