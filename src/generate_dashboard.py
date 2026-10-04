"""정적 ETF 종합 EDA 대시보드 HTML 생성 및 빌드 모듈.

이 모듈은 전처리 완료된 ETF 데이터셋(`etf_processed.json`)을 읽어들여,
외부 웹서버 없이도 브라우저에서 단독 구동되는 인터랙티브 정적 HTML 대시보드
(`reports/etf_dashboard.html`)를 생성합니다.
Apache ECharts 5, Tailwind CSS, Lucide Icons를 활용하여 고성능 핀테크 시각화를 제공합니다.
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

    JSON 데이터가 HTML 내부에 안전하게 인라인 임베딩되므로,
    로컬 파일 시스템(`file:///`)이나 GitHub Pages 등 어떤 정적 호스팅 환경에서도
    CORS 문제나 백엔드 의존성 없이 즉시 작동합니다.

    Args:
        data (Dict[str, Any]): 'meta', 'summary', 'items'가 포함된 종합 데이터셋.

    Returns:
        str: 완성된 정적 HTML 문서 문자열.
    """
    json_data_str = json.dumps(data, ensure_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>네이버 증권 ETF 실시간 종합 EDA 대시보드</title>
  
  <!-- Tailwind CSS & Font -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            navy: {{
              800: '#0f172a',
              900: '#0b0f19',
              950: '#050811'
            }},
            brand: {{
              primary: '#06b6d4',
              accent: '#3b82f6',
              success: '#10b981',
              danger: '#f43f5e',
              warning: '#f59e0b'
            }}
          }}
        }}
      }}
    }}
  </script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  
  <!-- Apache ECharts & Lucide Icons -->
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    body {{
      font-family: "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }}
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(15, 23, 42, 0.6);
    }}
    ::-webkit-scrollbar-thumb {{
      background: rgba(71, 85, 105, 0.8);
      border-radius: 9999px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: rgba(100, 116, 139, 1);
    }}
    .glass-card {{
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .light .glass-card {{
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(0, 0, 0, 0.08);
    }}
  </style>
</head>
<body class="bg-navy-950 text-slate-100 min-h-screen transition-colors duration-200">

  <!-- 인라인 데이터 보관소 -->
  <script id="etf-dataset" type="application/json">
{json_data_str}
  </script>

  <!-- Navigation / Header -->
  <header class="sticky top-0 z-40 glass-card border-b border-slate-800/80 px-6 py-4">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <i data-lucide="line-chart" class="w-5 h-5 text-white"></i>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
              네이버 증권 ETF 실시간 종합 EDA
            </h1>
            <span id="badge-total-count" class="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-semibold">
              총 0개 종목
            </span>
          </div>
          <p class="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            수집 기준 시점: <span id="meta-collected-at" class="font-medium text-slate-300">-</span>
          </p>
        </div>
      </div>

      <!-- Action Controls -->
      <div class="flex items-center gap-2 self-end md:self-auto">
        <button id="btn-export-csv" class="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">
          <i data-lucide="file-spreadsheet" class="w-4 h-4 text-emerald-400"></i>
          CSV 다운로드
        </button>
        <button id="btn-export-json" class="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">
          <i data-lucide="file-json" class="w-4 h-4 text-amber-400"></i>
          JSON 다운로드
        </button>
        <button id="btn-theme-toggle" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition" title="테마 전환">
          <i data-lucide="sun" class="w-4 h-4"></i>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Dashboard Container -->
  <main class="max-w-7xl mx-auto px-4 md:px-6 py-6 space-y-6">

    <!-- KPI Cards Grid (4개) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- KPI 1: 순자산 총액 -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden group hover:border-cyan-500/40 transition">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">전체 순자산(AUM) 합계</p>
            <h3 id="kpi-total-aum" class="text-2xl font-bold text-white mt-1.5">- 조원</h3>
            <p id="kpi-aum-detail" class="text-xs text-slate-400 mt-1">총 0개 ETF 기준</p>
          </div>
          <div class="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <i data-lucide="wallet" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 to-blue-500"></div>
      </div>

      <!-- KPI 2: 일일 총 거래대금 -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden group hover:border-blue-500/40 transition">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">당일 총 거래대금</p>
            <h3 id="kpi-total-trading-val" class="text-2xl font-bold text-white mt-1.5">- 억원</h3>
            <p class="text-xs text-slate-400 mt-1">시장 유동성 총합</p>
          </div>
          <div class="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <i data-lucide="activity" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500"></div>
      </div>

      <!-- KPI 3: 시장 등락 비중 -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden group hover:border-rose-500/40 transition">
        <div class="flex justify-between items-start">
          <div class="w-full mr-2">
            <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">시장 등락 현황</p>
            <div class="flex items-baseline gap-2 mt-1.5">
              <span id="kpi-rising-count" class="text-xl font-bold text-rose-400">▲ 0</span>
              <span id="kpi-falling-count" class="text-xl font-bold text-blue-400">▼ 0</span>
              <span id="kpi-unchanged-count" class="text-sm font-semibold text-slate-400">- 0</span>
            </div>
            <!-- Progress Bar -->
            <div class="w-full bg-slate-800 rounded-full h-2 mt-2 flex overflow-hidden">
              <div id="bar-rising" class="bg-rose-500 h-full transition-all duration-500" style="width: 50%"></div>
              <div id="bar-unchanged" class="bg-slate-500 h-full transition-all duration-500" style="width: 10%"></div>
              <div id="bar-falling" class="bg-blue-500 h-full transition-all duration-500" style="width: 40%"></div>
            </div>
          </div>
          <div class="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <i data-lucide="trending-up" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 to-amber-500"></div>
      </div>

      <!-- KPI 4: 평균 괴리율 & 이상 괴리 -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden group hover:border-emerald-500/40 transition">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">평균 iNav 괴리율</p>
            <h3 id="kpi-avg-disparity" class="text-2xl font-bold text-white mt-1.5">0.00 %</h3>
            <p id="kpi-abnormal-disparity" class="text-xs text-amber-400 mt-1">이상 괴리(±1% 초과): 0개</p>
          </div>
          <div class="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <i data-lucide="scale" class="w-5 h-5"></i>
          </div>
        </div>
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-500"></div>
      </div>

    </div>

    <!-- EDA Visualizations Grid (2x2) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Chart 1: 운용사 점유율 -->
      <div class="glass-card rounded-2xl p-5 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <i data-lucide="pie-chart" class="w-4 h-4 text-cyan-400"></i>
            <h3 class="font-bold text-sm text-slate-200">운용사 브랜드별 AUM 점유율</h3>
          </div>
          <div class="flex items-center gap-1 bg-slate-800/80 p-0.5 rounded-lg border border-slate-700 text-xs">
            <button id="btn-chart-treemap" class="px-2.5 py-1 rounded-md bg-cyan-500 text-white font-medium transition">트리맵</button>
            <button id="btn-chart-donut" class="px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition">도넛</button>
          </div>
        </div>
        <div id="chart-brand" class="w-full h-80"></div>
      </div>

      <!-- Chart 2: 자산군별 AUM 및 평균 수익률 -->
      <div class="glass-card rounded-2xl p-5 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <i data-lucide="bar-chart-3" class="w-4 h-4 text-blue-400"></i>
            <h3 class="font-bold text-sm text-slate-200">자산군별 AUM 규모 및 1개월 평균 수익률</h3>
          </div>
        </div>
        <div id="chart-asset" class="w-full h-80"></div>
      </div>

      <!-- Chart 3: 기간별 수익률 분포 -->
      <div class="glass-card rounded-2xl p-5 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <i data-lucide="sliders" class="w-4 h-4 text-purple-400"></i>
            <h3 class="font-bold text-sm text-slate-200">기간별 수익률 분포 및 상위 TOP 10</h3>
          </div>
          <div class="flex items-center gap-1 bg-slate-800/80 p-0.5 rounded-lg border border-slate-700 text-xs">
            <button class="btn-return-period px-2.5 py-1 rounded-md bg-purple-500 text-white font-medium transition" data-period="1m">1개월</button>
            <button class="btn-return-period px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition" data-period="3m">3개월</button>
            <button class="btn-return-period px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition" data-period="6m">6개월</button>
          </div>
        </div>
        <div id="chart-return" class="w-full h-80"></div>
      </div>

      <!-- Chart 4: 유동성 vs 괴리율 산점도 -->
      <div class="glass-card rounded-2xl p-5 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <i data-lucide="scatter-chart" class="w-4 h-4 text-emerald-400"></i>
            <h3 class="font-bold text-sm text-slate-200">유동성(거래대금) vs iNav 괴리율</h3>
          </div>
          <span class="text-xs text-slate-400">버블 크기: AUM 순자산</span>
        </div>
        <div id="chart-scatter" class="w-full h-80"></div>
      </div>

    </div>

    <!-- Data Table & Search / Filter Section -->
    <div class="glass-card rounded-2xl p-5 space-y-4">
      
      <!-- Filter Controls Header -->
      <div class="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <i data-lucide="table-2" class="w-5 h-5 text-cyan-400"></i>
          <h2 class="text-base font-bold text-white">전체 ETF 종목 탐색기</h2>
          <span id="filtered-count" class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">0 / 0</span>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <!-- Search Input -->
          <div class="relative flex-1 sm:w-64">
            <i data-lucide="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
            <input id="input-search" type="text" placeholder="종목명 또는 6자리 코드 검색..." 
                   class="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition">
          </div>

          <!-- Brand Filter -->
          <select id="select-brand" class="px-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-500 transition">
            <option value="">운용사 전체</option>
          </select>

          <!-- Asset Filter -->
          <select id="select-asset" class="px-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-500 transition">
            <option value="">자산군 전체</option>
          </select>

          <!-- Strategy Filter -->
          <select id="select-strategy" class="px-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-500 transition">
            <option value="">전략 전체</option>
            <option value="leverage">레버리지 / 2X</option>
            <option value="inverse">인버스</option>
            <option value="covered_call">커버드콜</option>
            <option value="active">액티브</option>
            <option value="hedged">환헤지(H)</option>
          </select>

          <!-- Reset Filter Button -->
          <button id="btn-reset-filters" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition" title="필터 초기화">
            <i data-lucide="rotate-ccw" class="w-4 h-4"></i>
          </button>
        </div>
      </div>

      <!-- Table Container -->
      <div class="overflow-x-auto rounded-xl border border-slate-800">
        <table id="etf-table" class="w-full text-left text-xs text-slate-300">
          <thead class="bg-slate-900/90 text-slate-400 border-b border-slate-800 uppercase tracking-wider select-none font-semibold">
            <tr>
              <th class="py-3 px-3 cursor-pointer hover:text-cyan-400 transition" data-sort="item_code">코드</th>
              <th class="py-3 px-3 cursor-pointer hover:text-cyan-400 transition" data-sort="item_name">종목명</th>
              <th class="py-3 px-3 cursor-pointer hover:text-cyan-400 transition" data-sort="brand">운용사</th>
              <th class="py-3 px-3 cursor-pointer hover:text-cyan-400 transition" data-sort="asset_class">자산군</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="current_price">현재가</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="change_rate">등락률</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="trading_value_krw">거래대금</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="aum_krw">순자산(AUM)</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="return_1m">1개월</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="return_3m">3개월</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="return_6m">6개월</th>
              <th class="py-3 px-3 text-right cursor-pointer hover:text-cyan-400 transition" data-sort="disparity_rate">괴리율</th>
              <th class="py-3 px-2 text-center">상세</th>
            </tr>
          </thead>
          <tbody id="table-body" class="divide-y divide-slate-800/60 bg-slate-950/40">
            <!-- Dynamic Rows -->
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        <div class="flex items-center gap-2 text-xs text-slate-400">
          <span>페이지당 항목:</span>
          <select id="select-page-size" class="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200">
            <option value="15">15개</option>
            <option value="30" selected>30개</option>
            <option value="50">50개</option>
            <option value="100">100개</option>
          </select>
        </div>

        <div class="flex items-center gap-1.5">
          <button id="btn-page-first" class="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition">
            <i data-lucide="chevrons-left" class="w-4 h-4"></i>
          </button>
          <button id="btn-page-prev" class="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition">
            <i data-lucide="chevron-left" class="w-4 h-4"></i>
          </button>
          <span id="page-indicator" class="text-xs text-slate-300 px-3 font-medium">1 / 1</span>
          <button id="btn-page-next" class="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition">
            <i data-lucide="chevron-right" class="w-4 h-4"></i>
          </button>
          <button id="btn-page-last" class="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition">
            <i data-lucide="chevrons-right" class="w-4 h-4"></i>
          </button>
        </div>
      </div>

    </div>

  </main>

  <!-- Modal: Item Detail Popup -->
  <div id="detail-modal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-4">
    <div class="glass-card rounded-2xl max-w-lg w-full p-6 border border-slate-700 shadow-2xl relative">
      <button id="btn-close-modal" class="absolute top-4 right-4 p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white">
        <i data-lucide="x" class="w-5 h-5"></i>
      </button>

      <div class="flex items-center gap-2 mb-2">
        <span id="modal-item-code" class="text-xs px-2.5 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono font-bold">000000</span>
        <span id="modal-brand" class="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300">BRAND</span>
        <span id="modal-asset-class" class="text-xs px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400">자산군</span>
      </div>

      <h3 id="modal-item-name" class="text-lg font-bold text-white mb-4">-</h3>

      <div class="grid grid-cols-2 gap-3 text-xs mb-5">
        <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span class="text-slate-400 block mb-0.5">현재가</span>
          <span id="modal-price" class="text-base font-bold text-white">- 원</span>
          <span id="modal-change" class="text-xs block mt-0.5">-</span>
        </div>
        <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span class="text-slate-400 block mb-0.5">순자산가치 (iNav)</span>
          <span id="modal-inav" class="text-base font-bold text-white">- 원</span>
          <span id="modal-disparity" class="text-xs block mt-0.5">-</span>
        </div>
        <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span class="text-slate-400 block mb-0.5">순자산규모 (AUM)</span>
          <span id="modal-aum" class="text-sm font-semibold text-slate-200">- 억원</span>
        </div>
        <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <span class="text-slate-400 block mb-0.5">일일 거래대금</span>
          <span id="modal-trading-val" class="text-sm font-semibold text-slate-200">- 억원</span>
        </div>
      </div>

      <!-- Return Rates -->
      <div class="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 mb-5">
        <span class="text-xs font-semibold text-slate-300 block mb-2">기간별 수익률</span>
        <div class="grid grid-cols-3 gap-2 text-center text-xs">
          <div>
            <span class="text-slate-400 block">1개월</span>
            <span id="modal-return-1m" class="font-bold mt-1 inline-block">-</span>
          </div>
          <div>
            <span class="text-slate-400 block">3개월</span>
            <span id="modal-return-3m" class="font-bold mt-1 inline-block">-</span>
          </div>
          <div>
            <span class="text-slate-400 block">6개월</span>
            <span id="modal-return-6m" class="font-bold mt-1 inline-block">-</span>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2">
        <a id="modal-naver-link" href="#" target="_blank" rel="noopener noreferrer" 
           class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-xs font-bold shadow-lg shadow-emerald-500/20 hover:brightness-110 transition">
          <i data-lucide="external-link" class="w-4 h-4"></i>
          네이버 증권 상세 보기
        </a>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <footer class="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
    <p>네이버 증권 ETF 실시간 종합 EDA 대시보드 | Powered by Python, Apache ECharts & Tailwind CSS</p>
  </footer>

  <!-- Application Logic -->
  <script>
    (function() {{
      // 1. Data Initialization
      const rawPayloadEl = document.getElementById('etf-dataset');
      let dataset = {{ meta: {{}}, summary: {{}}, items: [] }};
      try {{
        dataset = JSON.parse(rawPayloadEl.textContent);
      }} catch(e) {{
        console.error('Failed to parse embedded dataset:', e);
      }}

      const allItems = dataset.items || [];
      const summary = dataset.summary || {{}};
      const meta = dataset.meta || {{}};

      // 2. State Management
      let filteredItems = [...allItems];
      let currentSortKey = 'aum_krw';
      let currentSortOrder = 'desc';
      let currentPage = 1;
      let pageSize = 30;
      let brandChartMode = 'treemap'; // 'treemap' | 'donut'
      let returnPeriod = '1m'; // '1m' | '3m' | '6m'

      // ECharts instances
      let chartBrandInstance = null;
      let chartAssetInstance = null;
      let chartReturnInstance = null;
      let chartScatterInstance = null;

      // Number formatting helpers
      const formatNumber = (num) => (num !== null && num !== undefined) ? num.toLocaleString() : '-';
      const formatCurrencyEok = (val) => {{
        if (!val && val !== 0) return '-';
        return (val / 100000000).toLocaleString(undefined, {{ maximumFractionDigits: 1 }}) + ' 억';
      }};
      const formatPercent = (val) => {{
        if (val === null || val === undefined) return '-';
        const sign = val > 0 ? '+' : '';
        return `${{sign}}${{val.toFixed(2)}}%`;
      }};

      // Initialize Icons
      lucide.createIcons();

      // Render Meta & KPI Cards
      function renderKPIs() {{
        document.getElementById('badge-total-count').textContent = `총 ${{summary.total_count || allItems.length}}개 종목`;
        document.getElementById('meta-collected-at').textContent = meta.collected_at || '-';

        document.getElementById('kpi-total-aum').textContent = `${{summary.total_aum_jo ? summary.total_aum_jo.toLocaleString() : 0}} 조원`;
        document.getElementById('kpi-aum-detail').textContent = `총 ${{allItems.length}}개 종목 순자산 합산`;

        document.getElementById('kpi-total-trading-val').textContent = `${{summary.total_trading_value_eok ? summary.total_trading_value_eok.toLocaleString() : 0}} 억원`;

        const rising = summary.rising_count || 0;
        const falling = summary.falling_count || 0;
        const unchanged = summary.unchanged_count || 0;
        const total = (rising + falling + unchanged) || 1;

        document.getElementById('kpi-rising-count').textContent = `▲ ${{rising}}`;
        document.getElementById('kpi-falling-count').textContent = `▼ ${{falling}}`;
        document.getElementById('kpi-unchanged-count').textContent = `- ${{unchanged}}`;

        document.getElementById('bar-rising').style.width = `${{(rising / total) * 100}}%`;
        document.getElementById('bar-unchanged').style.width = `${{(unchanged / total) * 100}}%`;
        document.getElementById('bar-falling').style.width = `${{(falling / total) * 100}}%`;

        document.getElementById('kpi-avg-disparity').textContent = `${{summary.avg_disparity_rate ? summary.avg_disparity_rate.toFixed(2) : '0.00'}} %`;
        
        const abnormalCount = allItems.filter(it => it.disparity_rate !== null && Math.abs(it.disparity_rate) >= 1.0).length;
        document.getElementById('kpi-abnormal-disparity').textContent = `이상 괴리(±1% 이상): ${{abnormalCount}}개`;
      }}

      // Populate Filter Dropdowns
      function initFilters() {{
        const brandSelect = document.getElementById('select-brand');
        const assetSelect = document.getElementById('select-asset');

        const brands = [...new Set(allItems.map(it => it.brand))].filter(Boolean).sort();
        brands.forEach(b => {{
          const opt = document.createElement('option');
          opt.value = b;
          opt.textContent = b;
          brandSelect.appendChild(opt);
        }});

        const assets = [...new Set(allItems.map(it => it.asset_class))].filter(Boolean).sort();
        assets.forEach(a => {{
          const opt = document.createElement('option');
          opt.value = a;
          opt.textContent = a;
          assetSelect.appendChild(opt);
        }});
      }}

      // Render Chart 1: Brand Market Share (Treemap / Donut)
      function renderBrandChart() {{
        if (!chartBrandInstance) {{
          chartBrandInstance = echarts.init(document.getElementById('chart-brand'), 'dark', {{ renderer: 'canvas' }});
        }}

        const brandStats = summary.brand_stats || [];
        const topBrands = brandStats.slice(0, 10);
        const othersAum = brandStats.slice(10).reduce((acc, cur) => acc + cur.aum_krw, 0);
        const othersCount = brandStats.slice(10).reduce((acc, cur) => acc + cur.count, 0);

        const chartData = topBrands.map(b => ({{
          name: b.brand,
          value: Math.round(b.aum_krw / 100000000), // 억원
          itemCount: b.count,
        }}));

        if (othersAum > 0) {{
          chartData.push({{
            name: '기타 운용사',
            value: Math.round(othersAum / 100000000),
            itemCount: othersCount,
          }});
        }}

        let option = {{}};

        if (brandChartMode === 'treemap') {{
          option = {{
            backgroundColor: 'transparent',
            tooltip: {{
              trigger: 'item',
              formatter: function(params) {{
                const val = (params.value || 0).toLocaleString();
                const count = params.data.itemCount || 0;
                return `<b>${{params.name}}</b><br/>AUM: ${{val}} 억원<br/>종목 수: ${{count}}개`;
              }}
            }},
            series: [{{
              type: 'treemap',
              data: chartData,
              roam: false,
              nodeClick: false,
              breadcrumb: {{ show: false }},
              label: {{
                show: true,
                formatter: '{{b}}\\n{{c}} 억원'
              }},
              levels: [{{
                color: ['#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#ec4899', '#14b8a6', '#64748b'],
                itemStyle: {{
                  borderColor: '#0f172a',
                  borderWidth: 2,
                  gapWidth: 2
                }}
              }}]
            }}]
          }};
        }} else {{
          option = {{
            backgroundColor: 'transparent',
            tooltip: {{
              trigger: 'item',
              formatter: '{{b}}: {{c}} 억원 ({{d}}%)'
            }},
            legend: {{
              orient: 'vertical',
              right: 10,
              top: 'center',
              textStyle: {{ color: '#94a3b8', fontSize: 11 }}
            }},
            series: [{{
              name: '운용사 점유율',
              type: 'pie',
              radius: ['45%', '70%'],
              center: ['40%', '50%'],
              avoidLabelOverlap: false,
              itemStyle: {{
                borderRadius: 8,
                borderColor: '#0b0f19',
                borderWidth: 2
              }},
              label: {{ show: false }},
              emphasis: {{
                label: {{
                  show: true,
                  fontSize: 14,
                  fontWeight: 'bold',
                  formatter: '{{b}}\\n{{d}}%'
                }}
              }},
              data: chartData
            }}]
          }};
        }}

        chartBrandInstance.setOption(option, true);
      }}

      // Render Chart 2: Asset Class AUM & Avg Return
      function renderAssetChart() {{
        if (!chartAssetInstance) {{
          chartAssetInstance = echarts.init(document.getElementById('chart-asset'), 'dark');
        }}

        // Calculate avg 1m return per asset class
        const assetMap = {{}};
        allItems.forEach(it => {{
          const ac = it.asset_class || '기타';
          if (!assetMap[ac]) assetMap[ac] = {{ aum: 0, returns: [] }};
          assetMap[ac].aum += (it.aum_krw || 0);
          if (it.return_1m !== null) assetMap[ac].returns.push(it.return_1m);
        }});

        const categories = Object.keys(assetMap).sort((a, b) => assetMap[b].aum - assetMap[a].aum);
        const aumValues = categories.map(c => Math.round(assetMap[c].aum / 100000000));
        const avgReturns = categories.map(c => {{
          const rets = assetMap[c].returns;
          return rets.length > 0 ? parseFloat((rets.reduce((a, b) => a + b, 0) / rets.length).toFixed(2)) : 0;
        }});

        const option = {{
          backgroundColor: 'transparent',
          tooltip: {{
            trigger: 'axis',
            axisPointer: {{ type: 'cross' }}
          }},
          legend: {{
            data: ['AUM(억원)', '1M 평균 수익률(%)'],
            textStyle: {{ color: '#94a3b8' }}
          }},
          grid: {{ left: '3%', right: '4%', bottom: '8%', containLabel: true }},
          xAxis: [{{
            type: 'category',
            data: categories,
            axisLabel: {{ color: '#94a3b8', interval: 0, rotate: 20 }}
          }}],
          yAxis: [
            {{
              type: 'value',
              name: 'AUM (억원)',
              axisLabel: {{ color: '#94a3b8' }},
              splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.05)' }} }}
            }},
            {{
              type: 'value',
              name: '수익률 (%)',
              axisLabel: {{ color: '#94a3b8', formatter: '{{value}}%' }},
              splitLine: {{ show: false }}
            }}
          ],
          series: [
            {{
              name: 'AUM(억원)',
              type: 'bar',
              data: aumValues,
              itemStyle: {{
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  {{ offset: 0, color: '#3b82f6' }},
                  {{ offset: 1, color: '#1d4ed8' }}
                ]),
                borderRadius: [4, 4, 0, 0]
              }}
            }},
            {{
              name: '1M 평균 수익률(%)',
              type: 'line',
              yAxisIndex: 1,
              data: avgReturns,
              itemStyle: {{ color: '#f59e0b' }},
              lineStyle: {{ width: 3 }},
              symbol: 'circle',
              symbolSize: 6
            }}
          ]
        }};

        chartAssetInstance.setOption(option, true);
      }}

      // Render Chart 3: Return Distribution & Top 10
      function renderReturnChart() {{
        if (!chartReturnInstance) {{
          chartReturnInstance = echarts.init(document.getElementById('chart-return'), 'dark');
        }}

        const key = returnPeriod === '1m' ? 'return_1m' : returnPeriod === '3m' ? 'return_3m' : 'return_6m';
        const validItems = allItems.filter(it => it[key] !== null).sort((a, b) => b[key] - a[key]);

        // Top 10 Items
        const top10 = validItems.slice(0, 10).reverse();
        const names = top10.map(it => it.item_name.length > 12 ? it.item_name.slice(0, 12) + '...' : it.item_name);
        const returns = top10.map(it => it[key]);

        const option = {{
          backgroundColor: 'transparent',
          title: {{
            text: `${{returnPeriod.toUpperCase()}} 수익률 TOP 10 종목`,
            textStyle: {{ color: '#cbd5e1', fontSize: 12, fontWeight: 'normal' }},
            left: 'center'
          }},
          tooltip: {{
            trigger: 'axis',
            axisPointer: {{ type: 'shadow' }},
            formatter: (params) => `${{params[0].name}}<br/>${{returnPeriod.toUpperCase()}} 수익률: <b>${{params[0].value}}%</b>`
          }},
          grid: {{ left: '3%', right: '8%', bottom: '5%', top: '15%', containLabel: true }},
          xAxis: {{
            type: 'value',
            axisLabel: {{ color: '#94a3b8', formatter: '{{value}}%' }},
            splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.05)' }} }}
          }},
          yAxis: {{
            type: 'category',
            data: names,
            axisLabel: {{ color: '#cbd5e1', fontSize: 11 }}
          }},
          series: [{{
            type: 'bar',
            data: returns,
            itemStyle: {{
              color: function(params) {{
                return params.value >= 0 ? '#10b981' : '#f43f5e';
              }},
              borderRadius: [0, 4, 4, 0]
            }}
          }}]
        }};

        chartReturnInstance.setOption(option, true);
      }}

      // Render Chart 4: Liquidity vs Disparity Scatter Plot
      function renderScatterChart() {{
        if (!chartScatterInstance) {{
          chartScatterInstance = echarts.init(document.getElementById('chart-scatter'), 'dark');
        }}

        // Data: [trading_value_eok (X), disparity_rate (Y), aum_eok (Size), item_name, item_code, current_price, inav]
        const scatterData = allItems
          .filter(it => it.trading_value_eok !== null && it.disparity_rate !== null && it.trading_value_eok > 0)
          .map(it => [
            it.trading_value_eok,
            it.disparity_rate,
            it.aum_eok || 10,
            it.item_name,
            it.item_code,
            it.current_price,
            it.inav
          ]);

        const option = {{
          backgroundColor: 'transparent',
          tooltip: {{
            trigger: 'item',
            formatter: function(params) {{
              const d = params.value;
              return `<b>${{d[3]}}</b> (${{d[4]}})<br/>` +
                     `거래대금: ${{d[0].toLocaleString()}} 억원<br/>` +
                     `괴리율: <b>${{d[1] > 0 ? '+' : ''}}${{d[1]}}%</b><br/>` +
                     `AUM: ${{d[2].toLocaleString()}} 억원<br/>` +
                     `현재가: ${{d[5].toLocaleString()}}원 / iNav: ${{d[6].toLocaleString()}}원`;
            }}
          }},
          grid: {{ left: '5%', right: '5%', bottom: '10%', top: '10%', containLabel: true }},
          xAxis: {{
            type: 'log',
            name: '일일 거래대금(억원, Log)',
            nameLocation: 'middle',
            nameGap: 28,
            axisLabel: {{ color: '#94a3b8' }},
            splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.05)' }} }}
          }},
          yAxis: {{
            type: 'value',
            name: 'iNav 괴리율 (%)',
            nameLocation: 'middle',
            nameGap: 38,
            axisLabel: {{ color: '#94a3b8', formatter: '{{value}}%' }},
            splitLine: {{ lineStyle: {{ color: 'rgba(255, 255, 255, 0.05)' }} }}
          }},
          series: [{{
            type: 'scatter',
            data: scatterData,
            symbolSize: function(data) {{
              const aum = data[2];
              return Math.min(35, Math.max(6, Math.sqrt(aum) * 0.4));
            }},
            itemStyle: {{
              color: function(params) {{
                const disp = params.value[1];
                if (disp > 1.0) return '#f43f5e';
                if (disp < -1.0) return '#3b82f6';
                return 'rgba(6, 182, 212, 0.7)';
              }},
              borderColor: 'rgba(255, 255, 255, 0.2)',
              borderWidth: 1
            }}
          }}]
        }};

        chartScatterInstance.setOption(option, true);
      }}

      // Apply Table Filters & Sorting
      function applyFilters() {{
        const searchVal = document.getElementById('input-search').value.trim().toLowerCase();
        const brandVal = document.getElementById('select-brand').value;
        const assetVal = document.getElementById('select-asset').value;
        const strategyVal = document.getElementById('select-strategy').value;

        filteredItems = allItems.filter(it => {{
          if (searchVal) {{
            const matchName = it.item_name.toLowerCase().includes(searchVal);
            const matchCode = it.item_code.toLowerCase().includes(searchVal);
            if (!matchName && !matchCode) return false;
          }}
          if (brandVal && it.brand !== brandVal) return false;
          if (assetVal && it.asset_class !== assetVal) return false;
          if (strategyVal) {{
            if (strategyVal === 'leverage' && !it.is_leverage) return false;
            if (strategyVal === 'inverse' && !it.is_inverse) return false;
            if (strategyVal === 'covered_call' && !it.is_covered_call) return false;
            if (strategyVal === 'active' && !it.is_active) return false;
            if (strategyVal === 'hedged' && !it.is_hedged) return false;
          }}
          return true;
        }});

        // Sort items
        filteredItems.sort((a, b) => {{
          let valA = a[currentSortKey];
          let valB = b[currentSortKey];
          if (valA === null || valA === undefined) return 1;
          if (valB === null || valB === undefined) return -1;
          if (typeof valA === 'string') {{
            return currentSortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
          }}
          return currentSortOrder === 'asc' ? valA - valB : valB - valA;
        }});

        currentPage = 1;
        renderTable();
      }}

      // Render Table Rows & Pagination
      function renderTable() {{
        const total = filteredItems.length;
        document.getElementById('filtered-count').textContent = `${{total.toLocaleString()}} / ${{allItems.length.toLocaleString()}}`;

        const totalPages = Math.max(1, Math.ceil(total / pageSize));
        if (currentPage > totalPages) currentPage = totalPages;

        document.getElementById('page-indicator').textContent = `${{currentPage}} / ${{totalPages}}`;
        document.getElementById('btn-page-first').disabled = currentPage === 1;
        document.getElementById('btn-page-prev').disabled = currentPage === 1;
        document.getElementById('btn-page-next').disabled = currentPage === totalPages;
        document.getElementById('btn-page-last').disabled = currentPage === totalPages;

        const startIdx = (currentPage - 1) * pageSize;
        const pageItems = filteredItems.slice(startIdx, startIdx + pageSize);

        const tbody = document.getElementById('table-body');
        tbody.innerHTML = '';

        if (pageItems.length === 0) {{
          tbody.innerHTML = `<tr><td colspan="13" class="py-8 text-center text-slate-500">일치하는 ETF 종목이 없습니다.</td></tr>`;
          return;
        }}

        pageItems.forEach(it => {{
          const tr = document.createElement('tr');
          tr.className = 'hover:bg-slate-800/40 transition cursor-pointer';
          tr.onclick = (e) => {{
            if (e.target.closest('a')) return;
            openModal(it);
          }};

          const changeRateClass = (it.change_rate || 0) > 0 ? 'text-rose-400 font-semibold' : (it.change_rate || 0) < 0 ? 'text-blue-400 font-semibold' : 'text-slate-400';
          const return1mClass = (it.return_1m || 0) > 0 ? 'text-rose-400' : (it.return_1m || 0) < 0 ? 'text-blue-400' : 'text-slate-400';
          const return3mClass = (it.return_3m || 0) > 0 ? 'text-rose-400' : (it.return_3m || 0) < 0 ? 'text-blue-400' : 'text-slate-400';
          const return6mClass = (it.return_6m || 0) > 0 ? 'text-rose-400' : (it.return_6m || 0) < 0 ? 'text-blue-400' : 'text-slate-400';
          
          let disparityBadge = '-';
          if (it.disparity_rate !== null) {{
            const isWarn = Math.abs(it.disparity_rate) >= 1.0;
            const badgeColor = isWarn ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'text-slate-300';
            disparityBadge = `<span class="px-1.5 py-0.5 rounded ${{badgeColor}}">${{it.disparity_rate > 0 ? '+' : ''}}${{it.disparity_rate.toFixed(2)}}%</span>`;
          }}

          tr.innerHTML = `
            <td class="py-2.5 px-3 font-mono text-cyan-400 font-medium">${{it.item_code}}</td>
            <td class="py-2.5 px-3 font-medium text-white max-w-xs truncate" title="${{it.item_name}}">${{it.item_name}}</td>
            <td class="py-2.5 px-3 text-slate-400">${{it.brand}}</td>
            <td class="py-2.5 px-3 text-slate-400">${{it.asset_class}}</td>
            <td class="py-2.5 px-3 text-right font-semibold text-slate-200">${{formatNumber(it.current_price)}}</td>
            <td class="py-2.5 px-3 text-right ${{changeRateClass}}">${{formatPercent(it.change_rate)}}</td>
            <td class="py-2.5 px-3 text-right text-slate-300">${{formatCurrencyEok(it.trading_value_krw)}}</td>
            <td class="py-2.5 px-3 text-right text-slate-300">${{formatCurrencyEok(it.aum_krw)}}</td>
            <td class="py-2.5 px-3 text-right ${{return1mClass}}">${{formatPercent(it.return_1m)}}</td>
            <td class="py-2.5 px-3 text-right ${{return3mClass}}">${{formatPercent(it.return_3m)}}</td>
            <td class="py-2.5 px-3 text-right ${{return6mClass}}">${{formatPercent(it.return_6m)}}</td>
            <td class="py-2.5 px-3 text-right">${{disparityBadge}}</td>
            <td class="py-2.5 px-2 text-center">
              <button class="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white" title="상세보기">
                <i data-lucide="info" class="w-4 h-4"></i>
              </button>
            </td>
          `;
          tbody.appendChild(tr);
        }});

        lucide.createIcons();
      }}

      // Modal Open / Close
      function openModal(item) {{
        document.getElementById('modal-item-code').textContent = item.item_code;
        document.getElementById('modal-brand').textContent = item.brand;
        document.getElementById('modal-asset-class').textContent = item.asset_class;
        document.getElementById('modal-item-name').textContent = item.item_name;

        document.getElementById('modal-price').textContent = `${{formatNumber(item.current_price)}} 원`;
        const changeSign = (item.change_rate || 0) > 0 ? '▲' : (item.change_rate || 0) < 0 ? '▼' : '';
        const changeClass = (item.change_rate || 0) > 0 ? 'text-rose-400' : (item.change_rate || 0) < 0 ? 'text-blue-400' : 'text-slate-400';
        document.getElementById('modal-change').innerHTML = `<span class="${{changeClass}}">${{changeSign}} ${{formatNumber(item.change_price)}} (${{formatPercent(item.change_rate)}})</span>`;

        document.getElementById('modal-inav').textContent = `${{formatNumber(item.inav)}} 원`;
        document.getElementById('modal-disparity').textContent = `괴리율: ${{formatPercent(item.disparity_rate)}}`;

        document.getElementById('modal-aum').textContent = `${{(item.aum_eok || 0).toLocaleString()}} 억원`;
        document.getElementById('modal-trading-val').textContent = `${{(item.trading_value_eok || 0).toLocaleString()}} 억원`;

        document.getElementById('modal-return-1m').textContent = formatPercent(item.return_1m);
        document.getElementById('modal-return-3m').textContent = formatPercent(item.return_3m);
        document.getElementById('modal-return-6m').textContent = formatPercent(item.return_6m);

        document.getElementById('modal-naver-link').href = `https://finance.naver.com/item/main.naver?code=${{item.item_code}}`;

        document.getElementById('detail-modal').classList.remove('hidden');
      }}

      function closeModal() {{
        document.getElementById('detail-modal').classList.add('hidden');
      }}

      // CSV Export Function (UTF-8 with BOM to prevent Excel encoding issues)
      function exportToCSV() {{
        const headers = ['코드', '종목명', '운용사', '자산군', '현재가', '전일대비', '등락률(%)', '거래량', '거래대금(원)', '순자산(원)', '1M수익률(%)', '3M수익률(%)', '6M수익률(%)', 'iNav', '괴리율(%)'];
        
        let csvContent = '\uFEFF' + headers.join(',') + '\\n';

        filteredItems.forEach(it => {{
          const row = [
            `"${{it.item_code}}"`,
            `"${{it.item_name.replace(/"/g, '""')}}"`,
            `"${{it.brand}}"`,
            `"${{it.asset_class}}"`,
            it.current_price || '',
            it.change_price || '',
            it.change_rate || '',
            it.trading_volume || '',
            it.trading_value_krw || '',
            it.aum_krw || '',
            it.return_1m || '',
            it.return_3m || '',
            it.return_6m || '',
            it.inav || '',
            it.disparity_rate || ''
          ];
          csvContent += row.join(',') + '\\n';
        }});

        const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `etf_eda_export_${{new Date().toISOString().slice(0, 10)}}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }}

      // JSON Export Function
      function exportToJSON() {{
        const blob = new Blob([JSON.stringify(dataset, null, 2)], {{ type: 'application/json' }});
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `etf_eda_dataset_${{new Date().toISOString().slice(0, 10)}}.json`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }}

      // Event Listeners
      window.addEventListener('resize', () => {{
        chartBrandInstance && chartBrandInstance.resize();
        chartAssetInstance && chartAssetInstance.resize();
        chartReturnInstance && chartReturnInstance.resize();
        chartScatterInstance && chartScatterInstance.resize();
      }});

      document.getElementById('input-search').addEventListener('input', applyFilters);
      document.getElementById('select-brand').addEventListener('change', applyFilters);
      document.getElementById('select-asset').addEventListener('change', applyFilters);
      document.getElementById('select-strategy').addEventListener('change', applyFilters);

      document.getElementById('btn-reset-filters').addEventListener('click', () => {{
        document.getElementById('input-search').value = '';
        document.getElementById('select-brand').value = '';
        document.getElementById('select-asset').value = '';
        document.getElementById('select-strategy').value = '';
        applyFilters();
      }});

      // Sorting handler
      document.querySelectorAll('#etf-table thead th[data-sort]').forEach(th => {{
        th.addEventListener('click', () => {{
          const sortKey = th.getAttribute('data-sort');
          if (currentSortKey === sortKey) {{
            currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
          }} else {{
            currentSortKey = sortKey;
            currentSortOrder = 'desc';
          }}
          applyFilters();
        }});
      }});

      // Pagination Events
      document.getElementById('select-page-size').addEventListener('change', (e) => {{
        pageSize = parseInt(e.target.value, 10);
        currentPage = 1;
        renderTable();
      }});
      document.getElementById('btn-page-first').addEventListener('click', () => {{ currentPage = 1; renderTable(); }});
      document.getElementById('btn-page-prev').addEventListener('click', () => {{ if (currentPage > 1) {{ currentPage--; renderTable(); }} }});
      document.getElementById('btn-page-next').addEventListener('click', () => {{
        const totalPages = Math.ceil(filteredItems.length / pageSize);
        if (currentPage < totalPages) {{ currentPage++; renderTable(); }}
      }});
      document.getElementById('btn-page-last').addEventListener('click', () => {{
        currentPage = Math.ceil(filteredItems.length / pageSize);
        renderTable();
      }});

      // Chart Toggles
      document.getElementById('btn-chart-treemap').addEventListener('click', () => {{
        brandChartMode = 'treemap';
        document.getElementById('btn-chart-treemap').className = 'px-2.5 py-1 rounded-md bg-cyan-500 text-white font-medium transition';
        document.getElementById('btn-chart-donut').className = 'px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition';
        renderBrandChart();
      }});

      document.getElementById('btn-chart-donut').addEventListener('click', () => {{
        brandChartMode = 'donut';
        document.getElementById('btn-chart-donut').className = 'px-2.5 py-1 rounded-md bg-cyan-500 text-white font-medium transition';
        document.getElementById('btn-chart-treemap').className = 'px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition';
        renderBrandChart();
      }});

      document.querySelectorAll('.btn-return-period').forEach(btn => {{
        btn.addEventListener('click', () => {{
          document.querySelectorAll('.btn-return-period').forEach(b => {{
            b.className = 'btn-return-period px-2.5 py-1 rounded-md text-slate-400 hover:text-white transition';
          }});
          btn.className = 'btn-return-period px-2.5 py-1 rounded-md bg-purple-500 text-white font-medium transition';
          returnPeriod = btn.getAttribute('data-period');
          renderReturnChart();
        }});
      }});

      // Export Buttons
      document.getElementById('btn-export-csv').addEventListener('click', exportToCSV);
      document.getElementById('btn-export-json').addEventListener('click', exportToJSON);

      // Modal Events
      document.getElementById('btn-close-modal').addEventListener('click', closeModal);
      document.getElementById('detail-modal').addEventListener('click', (e) => {{
        if (e.target.id === 'detail-modal') closeModal();
      }});

      // Theme Toggle (Dark / Light)
      document.getElementById('btn-theme-toggle').addEventListener('click', () => {{
        const isDark = document.documentElement.classList.toggle('dark');
        document.documentElement.classList.toggle('light', !isDark);
      }});

      // Initial Bootstrap
      renderKPIs();
      initFilters();
      renderBrandChart();
      renderAssetChart();
      renderReturnChart();
      renderScatterChart();
      applyFilters();

    }})();
  </script>
</body>
</html>"""
    return html_template


def build_dashboard_file() -> Path:
    """가공된 JSON 데이터셋을 읽어들여 `reports/etf_dashboard.html` 정적 대시보드 파일을 생성합니다.

    Returns:
        Path: 생성된 정적 대시보드 HTML 파일 경로.

    Raises:
        FileNotFoundError: `data/processed/etf_processed.json`이 존재하지 않을 때 발생.
    """
    json_path = resolve_relative_path("data/processed/etf_processed.json")
    if not json_path.exists():
        raise FileNotFoundError(f"가공된 데이터셋 파일을 찾을 수 없습니다: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_content = render_html_dashboard(data)

    output_path = resolve_relative_path("reports/etf_dashboard.html")
    ensure_directory(output_path.parent)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 정적 웹 호스팅(GitHub Pages /docs 등)을 위해 docs/index.html로도 복제 저장
    docs_index_path = resolve_relative_path("docs/index.html")
    ensure_directory(docs_index_path.parent)
    with open(docs_index_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("정적 대시보드 HTML 파일 생성 완료: %s (크기: %d bytes)", output_path, len(html_content.encode("utf-8")))
    logger.info("정적 호스팅 배포용 복제 완료: %s", docs_index_path)

    return output_path


if __name__ == "__main__":
    build_dashboard_file()
