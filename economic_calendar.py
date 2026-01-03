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
                            'event': row['Event'],
                            'impact': 'Medium',
                            'description': f"Actual: {row.get('Actual','-')} | Est: {row.get('Market Expectation','-')}"
                        })
        except: pass
        
        # Add Manual Major Events (Example)
        events.append({
            'date': '2025-12-10', 'event': 'FOMC Interest Rate Decision', 
            'impact': 'High', 'description': 'Fed rate decision.'
        })
        return events
    
    def enrich_ai(self, events):
        key = os.getenv('GOOGLE_API_KEY')
        if not key: return events
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        
        for ev in events:
            if ev['impact'] == 'High':
                try:
                    payload = {"contents": [{"parts": [{"text": f"Explain market impact of: {ev['event']} in 2 sentences."}]}]}
                    resp = requests.post(f"{url}?key={key}", json=payload)
                    if resp.status_code == 200:
                        ev['description'] += "\n\n🤖 AI: " + resp.json()['candidates'][0]['content']['parts'][0]['text']
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
