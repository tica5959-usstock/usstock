#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US ETF Flows Analysis
Tracks capital flows in major sector and market ETFs
"""

import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from tqdm import tqdm
import requests
from dotenv import load_dotenv

load_dotenv()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETFFlowsAnalyzer:
    """Analyze ETF capital flows to detect sector rotation"""
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_csv = os.path.join(data_dir, 'us_etf_flows.csv')
        self.output_json = os.path.join(data_dir, 'etf_flow_analysis.json')
        
        # Major ETFs to track (24 total)
        self.etfs = {
            # Market Cap
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ 100',
            'IWM': 'Russell 2000',
            'DIA': 'Dow Jones',
            
            # Sector ETFs
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLV': 'Healthcare',
            'XLE': 'Energy',
            'XLY': 'Consumer Discretionary',
            'XLP': 'Consumer Staples',
            'XLI': 'Industrials',
            'XLB': 'Materials',
            'XLU': 'Utilities',
            'XLRE': 'Real Estate',
            'XLC': 'Communication Services',
            
            # Thematic
            'VTI': 'Total Market',
            'VOO': 'S&P 500 (Vanguard)',
            'GLD': 'Gold',
            'SLV': 'Silver',
            'USO': 'Oil',
            'TLT': 'Long-Term Treasury',
            'IEF': 'Mid-Term Treasury',
            'HYG': 'High Yield Bonds',
            'LQD': 'Investment Grade Bonds'
        }

        self.etf_categories = {
            'SPY': 'Broad Market', 'QQQ': 'Broad Market', 'IWM': 'Broad Market', 'DIA': 'Broad Market', 'VTI': 'Broad Market', 'VOO': 'Broad Market',
            'XLK': 'Sector', 'XLF': 'Sector', 'XLV': 'Sector', 'XLE': 'Sector', 'XLY': 'Sector', 'XLP': 'Sector',
            'XLI': 'Sector', 'XLB': 'Sector', 'XLU': 'Sector', 'XLRE': 'Sector', 'XLC': 'Sector',
            'GLD': 'Thematic', 'SLV': 'Thematic', 'USO': 'Thematic', 
            'TLT': 'Thematic', 'IEF': 'Thematic', 'HYG': 'Thematic', 'LQD': 'Thematic'
        }
    
    def download_etf_data(self, ticker: str, period: str = '3mo') -> pd.DataFrame:
        """Download ETF price and volume data"""
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period=period)
            return hist
        except Exception as e:
            logger.debug(f"Failed to download {ticker}: {e}")
            return pd.DataFrame()
    
    def calculate_obv(self, df: pd.DataFrame) -> float:
        """Calculate On-Balance Volume trend"""
        if len(df) < 20:
            return 0
        
        obv = [0]
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.append(obv[-1] + df['Volume'].iloc[i])
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.append(obv[-1] - df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        obv_series = pd.Series(obv)
        if len(obv_series) >= 20:
            obv_change = (obv_series.iloc[-1] - obv_series.iloc[-20]) / abs(obv_series.iloc[-20]) * 100 if obv_series.iloc[-20] != 0 else 0
            return obv_change
        return 0
    
    def calculate_flow_proxy(self, df: pd.DataFrame) -> Dict:
        """Calculate flow proxy score based on volume and price action"""
        if len(df) < 30:
            return None
        
        # Volume analysis
        vol_5d = df['Volume'].tail(5).mean()
        vol_20d = df['Volume'].tail(20).mean()
        vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1
        
        # Price momentum
        price_5d = (df['Close'].iloc[-1] / df['Close'].iloc[-6] - 1) * 100 if len(df) >= 6 else 0
        price_20d = (df['Close'].iloc[-1] / df['Close'].iloc[-21] - 1) * 100 if len(df) >= 21 else 0
        
        # OBV trend
        obv_trend = self.calculate_obv(df)
        
        # Flow Score (0-100)
        flow_score = 50
        
        # Volume contribution
        if vol_ratio > 1.5:
            flow_score += 20
        elif vol_ratio > 1.2:
            flow_score += 10
        elif vol_ratio < 0.8:
            flow_score -= 10
        
        # Price momentum contribution
        if price_5d > 3:
            flow_score += 15
        elif price_5d > 1:
            flow_score += 8
        elif price_5d < -3:
            flow_score -= 15
        elif price_5d < -1:
            flow_score -= 8
        
        # OBV contribution
        if obv_trend > 10:
            flow_score += 15
        elif obv_trend > 0:
            flow_score += 5
        elif obv_trend < -10:
            flow_score -= 15
        
        flow_score = max(0, min(100, flow_score))
        
        # Flow direction
        if flow_score >= 65:
            direction = "Strong Inflow"
        elif flow_score >= 55:
            direction = "Inflow"
        elif flow_score >= 45:
            direction = "Neutral"
        elif flow_score >= 35:
            direction = "Outflow"
        else:
            direction = "Strong Outflow"
        
        return {
            'vol_ratio': round(vol_ratio, 2),
            'price_5d': round(price_5d, 2),
            'price_20d': round(price_20d, 2),
            'obv_trend': round(obv_trend, 2),
            'flow_score': round(flow_score, 1),
            'flow_direction': direction
        }
    
    def analyze_all_etfs(self) -> pd.DataFrame:
        """Analyze all ETFs"""
        logger.info("🚀 Starting ETF Flows Analysis...")
        
        results = []
        
        for ticker, name in tqdm(self.etfs.items(), desc="Analyzing ETFs"):
            hist = self.download_etf_data(ticker, '3mo')
            
            if hist.empty:
                continue
            
            flow_data = self.calculate_flow_proxy(hist)
            
            if flow_data:
                current_price = hist['Close'].iloc[-1]
                
                result = {
                    'ticker': ticker,
                    'name': name,
                    'category': self.etf_categories.get(ticker, 'Other'),
                    'current_price': round(current_price, 2),
                    **flow_data
                }
                results.append(result)
        
        return pd.DataFrame(results)
    
    def generate_ai_analysis(self, results_df: pd.DataFrame) -> None:
        """Generate AI analysis of capital flows using Gemini"""
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            logger.warning("⚠️ Gemini API key not found. Skipping AI analysis.")
            return
        
        # Prepare data summary
        inflows = results_df[results_df['flow_direction'].str.contains('Inflow')]['name'].tolist()
        outflows = results_df[results_df['flow_direction'].str.contains('Outflow')]['name'].tolist()
        
        top_inflows = results_df.nlargest(5, 'flow_score')[['name', 'flow_score']].to_dict('records')
        top_outflows = results_df.nsmallest(5, 'flow_score')[['name', 'flow_score']].to_dict('records')
        
        prompt = f"""분석해주세요: ETF 자금 흐름

유입 섹터: {', '.join(inflows[:5])}
유출 섹터: {', '.join(outflows[:5])}

상위 유입:
{chr(10).join([f"- {item['name']}: {item['flow_score']}" for item in top_inflows])}

상위 유출:
{chr(10).join([f"- {item['name']}: {item['flow_score']}" for item in top_outflows])}

요청: 
1. 현재 자금 흐름 패턴 요약
2. 투자 기회 (유입 섹터)
3. 리스크 (유출 섹터)
4. 구체적 전략 제안

한국어로 4-5문장."""
        
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}
            }
            
            response = requests.post(f"{url}?key={api_key}", json=payload, timeout=30)
            
            if response.status_code == 200:
                ai_analysis = response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_analysis = "AI 분석 생성 실패"
                
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            ai_analysis = "AI 분석 생성 실패"
        
        # Save to JSON
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_etfs': len(results_df),
                'inflows': len(inflows),
                'outflows': len(outflows)
            },
            'top_inflows': top_inflows,
            'top_outflows': top_outflows,
            'ai_analysis': ai_analysis
        }
        
        with open(self.output_json, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ AI analysis saved to {self.output_json}")
    
    def run(self) -> pd.DataFrame:
        """Main execution"""
        # Analyze ETFs
        results_df = self.analyze_all_etfs()
        
        # Save CSV
        if not results_df.empty:
            results_df.to_csv(self.output_csv, index=False)
            logger.info(f"✅ Saved ETF flows to {self.output_csv}")
            
            # Generate AI analysis
            self.generate_ai_analysis(results_df)
            
            # Print summary
            logger.info("\n📊 ETF Flows Summary:")
            for direction in ['Strong Inflow', 'Inflow', 'Neutral', 'Outflow', 'Strong Outflow']:
                count = len(results_df[results_df['flow_direction'] == direction])
                if count > 0:
                    logger.info(f"   {direction}: {count} ETFs")
        else:
            logger.warning("No ETF data collected")
        
        return results_df


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='US ETF Flows Analysis')
    parser.add_argument('--dir', default='.', help='Data directory')
    args = parser.parse_args()
    
    analyzer = ETFFlowsAnalyzer(data_dir=args.dir)
    results = analyzer.run()
    
    if not results.empty:
        print("\n💰 Top 5 Capital Inflows:")
        top_5 = results.nlargest(5, 'flow_score')
        for _, row in top_5.iterrows():
            print(f"   {row['ticker']} ({row['name']}): Score {row['flow_score']} | {row['flow_direction']}")
        
        print("\n📉 Top 5 Capital Outflows:")
        bottom_5 = results.nsmallest(5, 'flow_score')
        for _, row in bottom_5.iterrows():
            print(f"   {row['ticker']} ({row['name']}): Score {row['flow_score']} | {row['flow_direction']}")


if __name__ == "__main__":
    main()
