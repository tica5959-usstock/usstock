#!/usr/bin/env python3
import os, json, logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class FinalReportGenerator:
    def __init__(self, data_dir='.'):
        self.data_dir = data_dir
        
    def run(self, top_n=10):
        # Load Quant Data
        stats_path = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if not os.path.exists(stats_path): return
        df = pd.read_csv(stats_path)
        
        # Load AI Data
        ai_path = os.path.join(self.data_dir, 'ai_summaries.json')
        ai_data = {}
        if os.path.exists(ai_path):
            with open(ai_path) as f: ai_data = json.load(f)
            
        results = []
        for _, row in df.iterrows():
            ticker = row['ticker']
            if ticker not in ai_data: continue
            
            summary = ai_data[ticker].get('summary', '')
            
            # AI Bonus Score
            ai_score = 0
            rec = "Hold"
            if "매수" in summary or "Buy" in summary: 
                ai_score = 10
                rec = "Buy"
            if "적극" in summary or "Strong" in summary:
                ai_score = 20
                rec = "Strong Buy"
                
            final_score = row['composite_score'] * 0.8 + ai_score
            
            results.append({
                'ticker': ticker,
                'name': row.get('name', ticker),
                'final_score': round(final_score, 1),
                'quant_score': row['composite_score'],
                'ai_recommendation': rec,
                'current_price': row['current_price'],
                'price_at_analysis': row['current_price'],  # 분석 시점 가격 저장
                'target_upside': row.get('target_upside', 0),  # 목표 Upside
                'ai_summary': summary,
                'sector': row.get('sector', 'N/A'),
                'grade': row.get('grade', 'N/A')
            })
            
        # Sort and Rank
        results.sort(key=lambda x: x['final_score'], reverse=True)
        top_picks = results[:top_n]
        for i, p in enumerate(top_picks, 1): p['rank'] = i
        
        # Save Report
        with open(os.path.join(self.data_dir, 'final_top10_report.json'), 'w', encoding='utf-8') as f:
            json.dump({'top_picks': top_picks}, f, indent=2, ensure_ascii=False)
            
        # Save for Dashboard with timestamp
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        
        dashboard_data = {
            'analysis_date': date_str,
            'analysis_timestamp': now.isoformat(),
            'picks': top_picks
        }
        
        with open(os.path.join(self.data_dir, 'smart_money_current.json'), 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        # Save to history directory for date picker
        history_dir = os.path.join(self.data_dir, 'history')
        os.makedirs(history_dir, exist_ok=True)
        
        history_file = os.path.join(history_dir, f'picks_{date_str}.json')
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            
        print(f"Generated Final Report for {len(top_picks)} stocks")

if __name__ == "__main__":
    FinalReportGenerator().run()
