# US Stock Market Dashboard - Backend System

미국 주식 스마트 머니 분석 대시보드의 백엔드 시스템입니다.

## 📋 시스템 개요

이 시스템은 3개의 주요 파트로 구성되어 있습니다:

1. **Part 1: 데이터 수집** - S&P 500 가격 데이터, 거래량 분석, 13F 보유량, ETF 자금흐름
2. **Part 2: 분석 및 스크리닝** - 6팩터 스마트 머니 스크리너, 섹터 히트맵, 옵션 플로우
3. **Part 3: AI 분석** - Gemini AI 기반 거시경제 분석, 종목별 투자 요약, 최종 리포트

## 🚀 설치 방법

### 1. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 `.env`로 복사하고 API 키를 입력하세요:

```bash
cp .env.example .env
```

필수 API 키:
- `GOOGLE_API_KEY`: Gemini AI API 키 ([발급받기](https://makersuite.google.com/app/apikey))

선택 API 키:
- `OPENAI_API_KEY`: OpenAI API 키
- `FRED_API_KEY`: FRED 경제 데이터 API 키

## 📂 데이터 흐름

```
┌─────────────────────┐
│  Part 1: 데이터 수집  │
├─────────────────────┤
│ create_us_daily_prices.py → us_daily_prices.csv
│ analyze_volume.py         → us_volume_analysis.csv
│ analyze_13f.py            → us_13f_holdings.csv
│ analyze_etf_flows.py      → us_etf_flows.csv
└─────────────────────┘
          ↓
┌─────────────────────┐
│ Part 2: 분석/스크리닝 │
├─────────────────────┤
│ smart_money_screener_v2.py → smart_money_picks_v2.csv
│ sector_heatmap.py          → sector_heatmap.json
│ options_flow.py            → options_flow.json
│ insider_tracker.py         → insider_moves.json
│ portfolio_risk.py          → portfolio_risk.json
└─────────────────────┘
          ↓
┌─────────────────────┐
│  Part 3: AI 분석     │
├─────────────────────┤
│ macro_analyzer.py          → macro_analysis.json
│ ai_summary_generator.py    → ai_summaries.json
│ final_report_generator.py  → final_top10_report.json
│ economic_calendar.py       → weekly_calendar.json
└─────────────────────┘
```

## 🎯 사용법

### 개별 스크립트 실행

#### Part 1: 데이터 수집

```bash
# S&P 500 가격 데이터 수집 (증분 업데이트)
python create_us_daily_prices.py

# 전체 새로고침
python create_us_daily_prices.py --full

# 거래량 분석
python analyze_volume.py

# 13F 기관 보유량 분석
python analyze_13f.py

# ETF 자금 흐름 분석
python analyze_etf_flows.py
```

#### Part 2: 분석 및 스크리닝

```bash
# 스마트 머니 스크리너 (Top 20)
python smart_money_screener_v2.py --top 20

# 섹터 히트맵
python sector_heatmap.py

# 옵션 플로우
python options_flow.py

# 인사이더 매매 추적
python insider_tracker.py

# 포트폴리오 리스크 분석
python portfolio_risk.py
```

#### Part 3: AI 분석

```bash
# 거시경제 AI 분석
python macro_analyzer.py

# 개별 종목 AI 요약 (Top 20)
python ai_summary_generator.py

# 최종 Top 10 리포트
python final_report_generator.py

# 경제 캘린더
python economic_calendar.py
```

### 전체 파이프라인 실행

```bash
# 전체 실행 (AI 포함)
python update_all.py

# 빠른 실행 (AI 제외)
python update_all.py --quick
```

## 📊 출력 파일 설명

### CSV 파일

- `us_daily_prices.csv`: S&P 500 일일 가격 데이터
- `us_stocks_list.csv`: S&P 500 종목 리스트
- `us_volume_analysis.csv`: 거래량 분석 결과 (OBV, A/D, MFI, Score)
- `us_13f_holdings.csv`: 기관 보유량 분석 결과
- `us_etf_flows.csv`: ETF 자금 흐름 데이터
- `smart_money_picks_v2.csv`: 스마트 머니 종합 스크리닝 결과

### 🇺🇸 US Stock AI Dashboard

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tica5959-usstock/usstock/blob/main/Stock_Dashboard_Colab.ipynb)

Advanced US Stock Market Analysis Dashboard powered by Flask, Gemini 3.0, and GPT-4.
Features real-time data tracking, AI-driven insights, and institutional flow analysis.

### JSON 파일

- `etf_flow_analysis.json`: ETF 자금 흐름 분석
- `sector_heatmap.json`: 섹터 히트맵 데이터 (Treemap용)
- `options_flow.json`: 옵션 플로우 데이터
- `insider_moves.json`: 인사이더 매매 데이터
- `portfolio_risk.json`: 포트폴리오 리스크 분석
- `macro_analysis.json`: 거시경제 AI 분석 (한국어)
- `macro_analysis_en.json`: 거시경제 AI 분석 (영어)
- `ai_summaries.json`: 개별 종목 AI 투자 요약
- `final_top10_report.json`: 최종 Top 10 투자 추천
- `smart_money_current.json`: 대시보드용 현재 추천 종목
- `weekly_calendar.json`: 주간 경제 캘린더 + AI 전망

## 🔧 문제 해결

### API 키 오류

```
Error: API Key Missing
```

→ `.env` 파일에 `GOOGLE_API_KEY`가 올바르게 설정되어 있는지 확인하세요.

### yfinance 다운로드 실패

```
Failed to download ticker
```

→ 일부 종목은 데이터가 없을 수 있습니다. 정상적인 현상이며, 시스템은 계속 진행됩니다.

### Rate Limit 오류

```
429 Too Many Requests
```

→ API 호출 제한에 걸렸습니다. 잠시 후 다시 시도하세요. `ai_summary_generator.py`에는 자동 딜레이가 포함되어 있습니다.

### 데이터 파일 없음

```
FileNotFoundError: us_daily_prices.csv
```

→ Part 1의 데이터 수집 스크립트를 먼저 실행해야 합니다.

## 📝 실행 순서 권장사항

처음 실행 시 다음 순서를 권장합니다:

1. `create_us_daily_prices.py` (약 10분 소요)
2. `analyze_volume.py`, `analyze_13f.py`, `analyze_etf_flows.py` (병렬 가능)
3. `smart_money_screener_v2.py` (약 10분 소요)
4. `sector_heatmap.py`, `options_flow.py`, `insider_tracker.py`, `portfolio_risk.py` (병렬 가능)
5. `macro_analyzer.py`
6. `ai_summary_generator.py` (약 15분 소요)
7. `final_report_generator.py`
8. `economic_calendar.py`

또는 간단하게:
```bash
python update_all.py
```

## 📈 업데이트 주기 권장

- **일일 업데이트**: `create_us_daily_prices.py`, `update_all.py`
- **주간 업데이트**: `ai_summary_generator.py`, `macro_analyzer.py`
- **월간 업데이트**: `analyze_13f.py` (13F는 분기별 공시)

## 🤝 기여

이슈 및 개선 제안은 환영합니다.

## 📄 라이선스

MIT License
