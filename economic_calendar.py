#!/usr/bin/env python3
import os, json, requests, logging
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

class EconomicCalendar:
    def __init__(self, data_dir='.'):
        self.output = os.path.join(data_dir, 'weekly_calendar.json')
        
    def get_events(self):
        # Scrape Yahoo Finance Calendar (Simplified)
        events = []
        try:
            url = f"https://finance.yahoo.com/calendar/economic"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                dfs = pd.read_html(StringIO(resp.text))
                if dfs:
                    df = dfs[0]
                    us = df[df['Country'] == 'US']
                    for _, row in us.iterrows():
                        events.append({
                            'date': datetime.now().strftime('%Y-%m-%d'), 
                            'time': row.get('Event Time', '00:00'),
                            'currency': 'USD',
                            'title': row['Event'],
                            'impact': 'Medium',
                            'actual': row.get('Actual', '-'),
                            'forecast': row.get('Market Expectation', '-'),
                            'previous': row.get('Previous', '-'),
                            'ai_analysis': None
                        })
        except: pass
        
        # Add Manual Major Events (Example)
        events.append({
            'date': '2025-12-10', 
            'time': '14:00',
            'currency': 'USD',
            'title': 'FOMC Interest Rate Decision', 
            'impact': 'High', 
            'actual': '-',
            'forecast': '5.50%',
            'previous': '5.50%',
            'ai_analysis': 'Fed rate decision critical for market direction.'
        })
        return events
    
    def enrich_ai(self, events):
        key = os.getenv('GOOGLE_API_KEY')
        if not key: return events
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        
        for ev in events:
            if ev['impact'] == 'High':
                try:
                    payload = {"contents": [{"parts": [{"text": f"Explain market impact of: {ev['title']} in 2 sentences."}]}]}
                    resp = requests.post(f"{url}?key={key}", json=payload)
                    if resp.status_code == 200:
                        ev['ai_analysis'] = resp.json()['candidates'][0]['content']['parts'][0]['text']
                except: pass
        return events

    def run(self):
        events = self.get_events()
        events = self.enrich_ai(events)
        
        output = {
            'updated': datetime.now().isoformat(),
            'events': events,
            'week_start': datetime.now().strftime('%Y-%m-%d')
        }
        with open(self.output, 'w') as f:
            json.dump(output, f, indent=2)
        logging.info("Saved economic calendar")

if __name__ == "__main__":
    EconomicCalendar().run()
