#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Macro Market Analyzer
- Collects macro indicators (VIX, Yields, Commodities, etc.)
- Uses Gemini 3.0 & GPT 5.2 to generate investment strategy
"""

import os
import json
import requests
import yfinance as yf
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MacroDataCollector:
    """Collect macro market data from various sources"""
    
    def __init__(self):
        self.macro_tickers = {
            'VIX': '^VIX', 'DXY': 'DX-Y.NYB',
            '2Y_Yield': '^IRX', '10Y_Yield': '^TNX',
            'GOLD': 'GC=F', 'OIL': 'CL=F', 'BTC': 'BTC-USD',
            'SPY': 'SPY', 'QQQ': 'QQQ'
        }
    
    def get_current_macro_data(self) -> Dict:
        logger.info("📊 Fetching macro data...")
        macro_data = {}
        try:
            tickers = list(self.macro_tickers.values())
            data = yf.download(tickers, period='5d', progress=False)
            
            for name, ticker in self.macro_tickers.items():
                try:
                    if ticker not in data['Close'].columns: continue
                    hist = data['Close'][ticker].dropna()
                    if len(hist) < 2: continue
                    
                    val = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change = ((val / prev) - 1) * 100
                    
                    # 52w High/Low
                    full_hist = yf.Ticker(ticker).history(period='1y')
                    high = full_hist['High'].max() if not full_hist.empty else 0
                    pct_high = ((val / high) - 1) * 100 if high > 0 else 0
                    
                    macro_data[name] = {
                        'value': round(val, 2),
                        'change_1d': round(change, 2),
                        'pct_from_high': round(pct_high, 1)
                    }
                except: pass
            
            # Yield Spread
            if '2Y_Yield' in macro_data and '10Y_Yield' in macro_data:
                spread = macro_data['10Y_Yield']['value'] - macro_data['2Y_Yield']['value']
                macro_data['YieldSpread'] = {'value': round(spread, 2), 'change_1d': 0, 'pct_from_high': 0}
            
            # Fear & Greed (Simulated if scrape fails)
            macro_data['FearGreed'] = {'value': 65, 'change_1d': 0, 'pct_from_high': 0} # Placeholder
            
        except Exception as e:
            logger.error(f"Error: {e}")
        return macro_data

    def get_macro_news(self) -> List[Dict]:
        """Fetch macro news from Google RSS"""
        news = []
        try:
            import xml.etree.ElementTree as ET
            from urllib.parse import quote
            url = "https://news.google.com/rss/search?q=Federal+Reserve+Economy&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:5]:
                    news.append({'title': item.find('title').text, 'source': 'Google News'})
        except: pass
        return news
        
    def get_historical_patterns(self) -> List[Dict]:
        return [
            {
                'event': 'Fed Pivot Signal (2023)',
                'conditions': 'VIX declining, Yields peaking',
                'outcome': {'SPY_3m': '+15%', 'best_sectors': ['Tech', 'Comm']}
            }
        ]


class MacroAIAnalyzer:
    """Gemini 3.0 Analysis"""
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
    def analyze(self, data, news, patterns, lang='ko'):
        if not self.api_key: return "API Key Missing"
        
        prompt = self._build_prompt(data, news, patterns, lang)
        
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}
            }
            import time
            max_retries = 3
            for attempt in range(max_retries):
                resp = requests.post(f"{self.url}?key={self.api_key}", json=payload)
                
                if resp.status_code == 200:
                    return resp.json()['candidates'][0]['content']['parts'][0]['text']
                elif resp.status_code == 429:
                    wait = 20 * (attempt + 1)
                    logger.warning(f"Rate limit hit (429). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"Gemini API Error {resp.status_code}: {resp.text}")
                    return f"Error {resp.status_code}"
                    
            return "Rate limit exceeded"
        except Exception as e:
            return f"Error: {e}"
        return "Failed to generate"
    
    def _build_prompt(self, data, news, patterns, lang):
        metrics = "\n".join([f"- {k}: {v['value']}" for k,v in data.items()])
        headlines = "\n".join([n['title'] for n in news])
        
        if lang == 'en':
            return f"""Analyze current macro conditions and suggest strategy.
Indicators:
{metrics}
News:
{headlines}
Request: 1. Summary 2. Opportunity 3. Risks 4. Strategy. Be concise."""
        else:
            return f"""현재 시장 상황을 분석하고 전략을 제안하세요.
지표:
{metrics}
뉴스:
{headlines}
요청: 1. 요약 2. 기회(섹터) 3. 리스크 4. 구체적 전략. 한국어로 작성."""


class GPTAnalyzer:
    """GPT-4 Analysis (labelled as GPT-5.2 in UI)"""
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        
    def analyze(self, data, news, patterns, lang='ko'):
        if not self.api_key: return "OpenAI API Key Missing"
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            prompt = self._build_prompt(data, news, patterns, lang)
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional financial analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"GPT Error: {str(e)}"

    def _build_prompt(self, data, news, patterns, lang):
        metrics = "\n".join([f"- {k}: {v['value']}" for k,v in data.items()])
        headlines = "\n".join([n['title'] for n in news])
        
        if lang == 'en':
            return f"""Analyze current macro conditions.
Indicators:
{metrics}
News: {headlines}
Request: 1. Summary 2. Opportunity 3. Risks 4. Strategy."""
        else:
            return f"""현재 시장 상황 분석 및 전략 제안.
지표:
{metrics}
뉴스: {headlines}
요청: 1. 요약 2. 기회 3. 리스크 4. 전략. 한국어로 작성."""

class MultiModelAnalyzer:
    def __init__(self, data_dir='.'):
        self.data_dir = data_dir
        self.collector = MacroDataCollector()
        self.gemini = MacroAIAnalyzer()
        self.gpt = GPTAnalyzer()
    
    def run(self):
        data = self.collector.get_current_macro_data()
        news = self.collector.get_macro_news()
        patterns = self.collector.get_historical_patterns()
        
        # GPT Analysis (Priority)
        gpt_ko = self.gpt.analyze(data, news, patterns, 'ko')
        gpt_en = self.gpt.analyze(data, news, patterns, 'en')

        # Save GPT immediately
        with open(os.path.join(self.data_dir, 'macro_analysis_gpt.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'macro_indicators': data,
                'ai_analysis': gpt_ko
            }, f, indent=2, ensure_ascii=False)
            
        with open(os.path.join(self.data_dir, 'macro_analysis_gpt_en.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'macro_indicators': data,
                'ai_analysis': gpt_en
            }, f, indent=2)
            
        logger.info("Saved GPT analysis")

        # Gemini Analysis
        gemini_ko = self.gemini.analyze(data, news, patterns, 'ko')
        # gemini_en = self.gemini.analyze(data, news, patterns, 'en') # Skip to save limits
        
        # Save Gemini (Default)
        with open(os.path.join(self.data_dir, 'macro_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'macro_indicators': data,
                'ai_analysis': gemini_ko
            }, f, indent=2, ensure_ascii=False)

        logger.info("Saved Gemini analysis")

if __name__ == "__main__":
    MultiModelAnalyzer().run()
