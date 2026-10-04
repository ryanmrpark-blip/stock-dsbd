"""정적 대시보드 HTML 생성기 단위 테스트 모듈.

이 모듈은 가공된 ETF JSON 데이터셋을 기반으로 완전한 독립형 HTML 대시보드가
정상적으로 생성되고 필수 차트 요소 및 데이터가 포함되는지 검증합니다.
"""

import unittest
from pathlib import Path
from typing import Any, Dict


class TestGenerateDashboard(unittest.TestCase):
    """대시보드 생성기 검증 테스트 케이스."""

    def setUp(self) -> None:
        """테스트용 모의 ETF 데이터셋 준비."""
        self.mock_data: Dict[str, Any] = {
            "meta": {
                "collected_at": "2026-10-04 21:00:00",
                "total_items": 2,
                "source": "https://stock.naver.com",
            },
            "summary": {
                "total_count": 2,
                "total_aum_krw": 2000000000000,
                "total_aum_jo": 2.0,
                "total_trading_value_krw": 50000000000,
                "total_trading_value_eok": 500.0,
                "rising_count": 1,
                "falling_count": 1,
                "unchanged_count": 0,
                "avg_disparity_rate": 0.15,
                "brand_stats": [
                    {"brand": "KODEX", "count": 1, "aum_krw": 1000000000000, "aum_eok": 10000.0},
                    {"brand": "TIGER", "count": 1, "aum_krw": 1000000000000, "aum_eok": 10000.0},
                ],
                "asset_stats": [
                    {"asset_class": "국내주식", "count": 1, "aum_krw": 1000000000000, "aum_eok": 10000.0},
                    {"asset_class": "해외주식", "count": 1, "aum_krw": 1000000000000, "aum_eok": 10000.0},
                ],
            },
            "items": [
                {
                    "item_code": "069500",
                    "item_name": "KODEX 200",
                    "brand": "KODEX",
                    "current_price": 35000.0,
                    "change_price": 350.0,
                    "change_rate": 1.01,
                    "price_movement": "rising",
                    "trading_volume": 1000000,
                    "trading_value_krw": 35000000000,
                    "trading_value_eok": 350.0,
                    "aum_krw": 1000000000000,
                    "aum_eok": 10000.0,
                    "etf_type": "국내주식형, 대표지수",
                    "asset_class": "국내주식",
                    "return_1m": 2.5,
                    "return_3m": 5.0,
                    "return_6m": 12.0,
                    "inav": 34950.0,
                    "disparity_rate": 0.14,
                    "is_leverage": False,
                    "is_inverse": False,
                    "is_covered_call": False,
                    "is_active": False,
                    "is_hedged": False,
                    "is_tr": False,
                },
                {
                    "item_code": "133690",
                    "item_name": "TIGER 미국나스닥100",
                    "brand": "TIGER",
                    "current_price": 105000.0,
                    "change_price": -500.0,
                    "change_rate": -0.47,
                    "price_movement": "falling",
                    "trading_volume": 200000,
                    "trading_value_krw": 15000000000,
                    "trading_value_eok": 150.0,
                    "aum_krw": 1000000000000,
                    "aum_eok": 10000.0,
                    "etf_type": "해외주식형, 시장대표",
                    "asset_class": "해외주식",
                    "return_1m": 4.1,
                    "return_3m": 10.2,
                    "return_6m": 22.5,
                    "inav": 104850.0,
                    "disparity_rate": 0.14,
                    "is_leverage": False,
                    "is_inverse": False,
                    "is_covered_call": False,
                    "is_active": False,
                    "is_hedged": False,
                    "is_tr": False,
                },
            ],
        }

    def test_render_html_contains_critical_sections(self) -> None:
        """HTML 렌더링 결과에 필수 스크립트 라이브러리 및 주요 컴포넌트가 포함되는지 검증."""
        from src.generate_dashboard import render_html_dashboard

        html_content = render_html_dashboard(self.mock_data)

        # 필수 CDN 라이브러리 확인
        self.assertIn("echarts", html_content.lower())
        self.assertIn("tailwindcss", html_content.lower())

        # 주요 컴포넌트 ID 및 구조 확인
        self.assertIn("chart-brand", html_content)
        self.assertIn("chart-asset", html_content)
        self.assertIn("chart-return", html_content)
        self.assertIn("chart-scatter", html_content)
        self.assertIn("etf-table", html_content)

        # 데이터 내장 여부 확인
        self.assertIn("069500", html_content)
        self.assertIn("KODEX 200", html_content)


if __name__ == "__main__":
    unittest.main()
