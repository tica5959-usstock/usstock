import os
import json
import threading
import pandas as pd
import numpy as np
import yfinance as yf
import subprocess
from flask import Flask, render_template, jsonify, request
import traceback
from datetime import datetime

app = Flask(__name__)

# Data Directory Configuration
DATA_DIR = os.getenv('DATA_DIR', '.')

# Sector mapping for major US stocks (S&P 500 + popular stocks)
SECTOR_MAP = {
    # Technology
    'AAPL': 'Tech', 'MSFT': 'Tech', 'NVDA': 'Tech', 'AVGO': 'Tech', 'ORCL': 'Tech',
    'CRM': 'Tech', 'AMD': 'Tech', 'ADBE': 'Tech', 'CSCO': 'Tech', 'INTC': 'Tech',
    'IBM': 'Tech', 'MU': 'Tech', 'QCOM': 'Tech', 'TXN': 'Tech', 'NOW': 'Tech',
    'AMAT': 'Tech', 'LRCX': 'Tech', 'KLAC': 'Tech', 'SNPS': 'Tech', 'CDNS': 'Tech',
    'ADI': 'Tech', 'MRVL': 'Tech', 'FTNT': 'Tech', 'PANW': 'Tech', 'CRWD': 'Tech',
    'SNOW': 'Tech', 'DDOG': 'Tech', 'ZS': 'Tech', 'NET': 'Tech', 'PLTR': 'Tech',
    'DELL': 'Tech', 'HPQ': 'Tech', 'HPE': 'Tech', 'KEYS': 'Tech', 'SWKS': 'Tech',
    # Financials
    'BRK-B': 'Fin', 'JPM': 'Fin', 'V': 'Fin', 'MA': 'Fin', 'BAC': 'Fin',
    'WFC': 'Fin', 'GS': 'Fin', 'MS': 'Fin', 'SPGI': 'Fin', 'AXP': 'Fin',
    'C': 'Fin', 'BLK': 'Fin', 'SCHW': 'Fin', 'CME': 'Fin', 'CB': 'Fin',
    'PGR': 'Fin', 'MMC': 'Fin', 'AON': 'Fin', 'ICE': 'Fin', 'MCO': 'Fin',
    'USB': 'Fin', 'PNC': 'Fin', 'TFC': 'Fin', 'AIG': 'Fin', 'MET': 'Fin',
    'PRU': 'Fin', 'ALL': 'Fin', 'TRV': 'Fin', 'COIN': 'Fin', 'HOOD': 'Fin',
    # Healthcare
    'LLY': 'Health', 'UNH': 'Health', 'JNJ': 'Health', 'ABBV': 'Health', 'MRK': 'Health',
    'PFE': 'Health', 'TMO': 'Health', 'ABT': 'Health', 'DHR': 'Health', 'BMY': 'Health',
    'AMGN': 'Health', 'GILD': 'Health', 'VRTX': 'Health', 'ISRG': 'Health', 'MDT': 'Health',
    'SYK': 'Health', 'BSX': 'Health', 'REGN': 'Health', 'ZTS': 'Health', 'ELV': 'Health',
    'CI': 'Health', 'HUM': 'Health', 'CVS': 'Health', 'MCK': 'Health', 'CAH': 'Health',
    'GEHC': 'Health', 'DXCM': 'Health', 'IQV': 'Health', 'BIIB': 'Health', 'MRNA': 'Health',
    # Energy
    'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy', 'EOG': 'Energy',
    'MPC': 'Energy', 'PSX': 'Energy', 'VLO': 'Energy', 'OXY': 'Energy', 'WMB': 'Energy',
    'DVN': 'Energy', 'HES': 'Energy', 'HAL': 'Energy', 'BKR': 'Energy', 'KMI': 'Energy',
    'FANG': 'Energy', 'PXD': 'Energy', 'TRGP': 'Energy', 'OKE': 'Energy', 'ET': 'Energy',
    # Consumer Discretionary
    'AMZN': 'Cons', 'TSLA': 'Cons', 'HD': 'Cons', 'MCD': 'Cons', 'NKE': 'Cons',
    'LOW': 'Cons', 'SBUX': 'Cons', 'TJX': 'Cons', 'BKNG': 'Cons', 'CMG': 'Cons',
    'ORLY': 'Cons', 'AZO': 'Cons', 'ROST': 'Cons', 'DHI': 'Cons', 'LEN': 'Cons',
    'GM': 'Cons', 'F': 'Cons', 'MAR': 'Cons', 'HLT': 'Cons', 'YUM': 'Cons',
    'DG': 'Cons', 'DLTR': 'Cons', 'BBY': 'Cons', 'ULTA': 'Cons', 'POOL': 'Cons',
    'LULU': 'Cons',  # lululemon athletica
    # Consumer Staples
    'WMT': 'Staple', 'PG': 'Staple', 'COST': 'Staple', 'KO': 'Staple', 'PEP': 'Staple',
    'PM': 'Staple', 'MDLZ': 'Staple', 'MO': 'Staple', 'CL': 'Staple', 'KMB': 'Staple',
    'GIS': 'Staple', 'K': 'Staple', 'HSY': 'Staple', 'SYY': 'Staple', 'STZ': 'Staple',
    'KHC': 'Staple', 'KR': 'Staple', 'EL': 'Staple', 'CHD': 'Staple', 'CLX': 'Staple',
    'KDP': 'Staple', 'TAP': 'Staple', 'ADM': 'Staple', 'BG': 'Staple', 'MNST': 'Staple',
    # Industrials
    'CAT': 'Indust', 'GE': 'Indust', 'RTX': 'Indust', 'HON': 'Indust', 'UNP': 'Indust',
    'BA': 'Indust', 'DE': 'Indust', 'LMT': 'Indust', 'UPS': 'Indust', 'MMM': 'Indust',
    'GD': 'Indust', 'NOC': 'Indust', 'CSX': 'Indust', 'NSC': 'Indust', 'WM': 'Indust',
    'EMR': 'Indust', 'ETN': 'Indust', 'ITW': 'Indust', 'PH': 'Indust', 'ROK': 'Indust',
    'FDX': 'Indust', 'CARR': 'Indust', 'TT': 'Indust', 'PCAR': 'Indust', 'FAST': 'Indust',
    # Materials
    'LIN': 'Mater', 'APD': 'Mater', 'SHW': 'Mater', 'FCX': 'Mater', 'ECL': 'Mater',
    'NEM': 'Mater', 'NUE': 'Mater', 'DOW': 'Mater', 'DD': 'Mater', 'VMC': 'Mater',
    'CTVA': 'Mater', 'PPG': 'Mater', 'MLM': 'Mater', 'IP': 'Mater', 'PKG': 'Mater',
    'ALB': 'Mater', 'GOLD': 'Mater', 'FMC': 'Mater', 'CF': 'Mater', 'MOS': 'Mater',
    # Utilities
    'NEE': 'Util', 'SO': 'Util', 'DUK': 'Util', 'CEG': 'Util', 'SRE': 'Util',
    'AEP': 'Util', 'D': 'Util', 'PCG': 'Util', 'EXC': 'Util', 'XEL': 'Util',
    'ED': 'Util', 'WEC': 'Util', 'ES': 'Util', 'AWK': 'Util', 'DTE': 'Util',
    # Real Estate
    'PLD': 'REIT', 'AMT': 'REIT', 'EQIX': 'REIT', 'SPG': 'REIT', 'PSA': 'REIT',
    'O': 'REIT', 'WELL': 'REIT', 'DLR': 'REIT', 'CCI': 'REIT', 'AVB': 'REIT',
    'CBRE': 'REIT', 'SBAC': 'REIT', 'WY': 'REIT', 'EQR': 'REIT', 'VTR': 'REIT',
    # Communication Services
    'META': 'Comm', 'GOOGL': 'Comm', 'GOOG': 'Comm', 'NFLX': 'Comm', 'DIS': 'Comm',
    'T': 'Comm', 'VZ': 'Comm', 'CMCSA': 'Comm', 'TMUS': 'Comm', 'CHTR': 'Comm',
    'EA': 'Comm', 'TTWO': 'Comm', 'RBLX': 'Comm', 'PARA': 'Comm', 'WBD': 'Comm',
    'MTCH': 'Comm', 'LYV': 'Comm', 'OMC': 'Comm', 'IPG': 'Comm', 'FOXA': 'Comm',
    # IT Services & Software
    'EPAM': 'Tech', 'ALGN': 'Health',
}

# Persistent sector cache file
SECTOR_CACHE_FILE = os.path.join(DATA_DIR, 'sector_cache.json')

def _load_sector_cache() -> dict:
    """Load sector cache from file"""
    try:
        if os.path.exists(SECTOR_CACHE_FILE):
            with open(SECTOR_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def _save_sector_cache(cache: dict):
    """Save sector cache to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(SECTOR_CACHE_FILE) or '.', exist_ok=True)
        with open(SECTOR_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving sector cache: {e}")

# Load cache at startup
_sector_cache = _load_sector_cache()

def get_sector(ticker: str) -> str:
    """Get sector for a ticker, auto-fetch from yfinance if not in SECTOR_MAP"""
    global _sector_cache
    
    # Check static map first
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]
    
    # Check persistent cache
    if ticker in _sector_cache:
        return _sector_cache[ticker]
    
    # Fetch from yfinance and save to file
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', '')
        
        # Map sector to short code
        sector_short_map = {
            'Technology': 'Tech',
            'Information Technology': 'Tech',
            'Healthcare': 'Health',
            'Health Care': 'Health',
            'Financials': 'Fin',
            'Financial Services': 'Fin',
            'Consumer Discretionary': 'Cons',
            'Consumer Cyclical': 'Cons',
            'Consumer Staples': 'Staple',
            'Consumer Defensive': 'Staple',
            'Energy': 'Energy',
            'Industrials': 'Indust',
            'Materials': 'Mater',
            'Basic Materials': 'Mater',
            'Utilities': 'Util',
            'Real Estate': 'REIT',
            'Communication Services': 'Comm',
        }
        
        short_sector = sector_short_map.get(sector, sector[:5] if sector else '-')
        
        # Save to cache and persist to file
        _sector_cache[ticker] = short_sector
        _save_sector_cache(_sector_cache)
        print(f"✅ Cached sector for {ticker}: {short_sector}")
        
        return short_sector
    except Exception as e:
        print(f"Error fetching sector for {ticker}: {e}")
        _sector_cache[ticker] = '-'
        _save_sector_cache(_sector_cache)
        return '-'


def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@app.route('/')
def index():
    return render_template('index.html')


# Load Stock List and Ticker Map
# (Used for KR market compatibility if needed)
try:
    map_df = pd.read_csv('ticker_to_yahoo_map.csv', dtype=str)
    TICKER_TO_YAHOO_MAP = dict(zip(map_df['ticker'], map_df['yahoo_ticker']))
except Exception:
    TICKER_TO_YAHOO_MAP = {}

# --- US Market Keys ---

@app.route('/api/us/portfolio')
def get_us_portfolio_data():
    """US Market Portfolio Data - Market Indices"""
    try:
        market_indices = []
        
        # US Market Indices
        indices_map = {
            '^DJI': 'Dow Jones',
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ',
            '^RUT': 'Russell 2000',
            '^VIX': 'VIX',
            'GC=F': 'Gold',
            'CL=F': 'Crude Oil',
            'BTC-USD': 'Bitcoin',
            '^TNX': '10Y Treasury',
            'DX-Y.NYB': 'Dollar Index',
            'KRW=X': 'USD/KRW'
        }
        
        # Fetch each ticker individually with error handling
        for ticker, name in indices_map.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='5d')
                
                if not hist.empty and len(hist) >= 2:
                    current_val = float(hist['Close'].iloc[-1])
                    prev_val = float(hist['Close'].iloc[-2])
                    change = current_val - prev_val
                    change_pct = (change / prev_val) * 100
                    
                    market_indices.append({
                        'name': name,
                        'price': f"{current_val:,.2f}",
                        'change': f"{change:+,.2f}",
                        'change_pct': round(change_pct, 2),
                        'color': 'green' if change >= 0 else 'red'
                    })
                elif not hist.empty:
                    current_val = float(hist['Close'].iloc[-1])
                    market_indices.append({
                        'name': name,
                        'price': f"{current_val:,.2f}",
                        'change': "0.00",
                        'change_pct': 0,
                        'color': 'gray'
                    })
            except Exception as e:
                print(f"Error fetching {ticker} ({name}): {e}")

        return jsonify({
            'market_indices': market_indices,
            'top_holdings': [],
            'style_box': {}
        })
        
    except Exception as e:
        print(f"Error getting US portfolio data: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/smart-money')
def get_us_smart_money():
    """Get Smart Money Picks with performance tracking"""
    try:
        # Try to load tracked picks with performance
        current_file = os.path.join(DATA_DIR, 'smart_money_current.json')
        
        if os.path.exists(current_file):
            with open(current_file, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
            
            # Get current prices for performance calculation
            tickers = [p['ticker'] for p in snapshot['picks']]
            current_prices = {}
            
            # Fetch prices individually for better reliability
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='5d')
                    if not hist.empty:
                        current_prices[ticker] = round(float(hist['Close'].dropna().iloc[-1]), 2)
                except Exception as e:
                    print(f"Error fetching price for {ticker}: {e}")
            
            # Add performance data to picks
            picks_with_perf = []
            for pick in snapshot['picks']:
                ticker = pick['ticker']
                price_at_rec = pick.get('price_at_analysis', 0) or 0
                current_price = current_prices.get(ticker, price_at_rec) or price_at_rec or 0
                
                # Handle NaN values
                try:
                    if pd.isna(price_at_rec): price_at_rec = 0
                    if pd.isna(current_price): current_price = price_at_rec
                except:
                    pass

                if price_at_rec > 0:
                    change_pct = ((current_price / price_at_rec) - 1) * 100
                else:
                    change_pct = 0
                
                picks_with_perf.append({
                    **pick,
                    'sector': get_sector(ticker),
                    'current_price': round(float(current_price), 2),
                    'price_at_rec': round(float(price_at_rec), 2),
                    'change_since_rec': round(float(change_pct), 2)
                })
            
            return jsonify({
                'analysis_date': snapshot.get('analysis_date', ''),
                'analysis_timestamp': snapshot.get('analysis_timestamp', ''),
                'top_picks': picks_with_perf,
                'summary': {
                    'total_analyzed': len(picks_with_perf),
                    'avg_score': round(sum(p['final_score'] for p in picks_with_perf) / len(picks_with_perf), 1) if picks_with_perf else 0
                }
            })
        
        # Fallback to CSV if no tracked data
        csv_path = os.path.join(DATA_DIR, 'smart_money_picks_v2.csv')
        if not os.path.exists(csv_path):
            csv_path = os.path.join(DATA_DIR, 'smart_money_picks.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({'error': 'Smart money picks not found. Run screener first.'}), 404
        
        df = pd.read_csv(csv_path)
        
        # Fetch real-time prices for CSV data
        tickers = df['ticker'].head(20).tolist()
        current_prices = {}
        
        try:
            import math
            price_data = yf.download(tickers, period='1d', progress=False)
            if not price_data.empty:
                closes = price_data['Close']
                for ticker in tickers:
                    try:
                        if isinstance(closes, pd.DataFrame) and ticker in closes.columns:
                            val = closes[ticker].iloc[-1]
                        elif isinstance(closes, pd.Series):
                            val = closes.iloc[-1]
                        else:
                            val = 0
                        current_prices[ticker] = round(float(val), 2) if not pd.isna(val) else 0
                    except:
                        current_prices[ticker] = 0
        except Exception as e:
            print(f"Error fetching US real-time prices: {e}")
        
        top_picks = []
        for _, row in df.head(20).iterrows():
            ticker = row['ticker']
            rec_price = row.get('current_price', 0) or 0
            cur_price = current_prices.get(ticker, rec_price) or rec_price
            
            if rec_price > 0:
                change_pct = ((cur_price / rec_price) - 1) * 100
            else:
                change_pct = 0
            
            top_picks.append({
                'ticker': ticker,
                'name': row.get('name', ticker),
                'sector': get_sector(ticker),
                'final_score': row.get('smart_money_score', row.get('composite_score', 0)),
                'current_price': round(float(cur_price), 2),
                'price_at_rec': round(float(rec_price), 2),
                'change_since_rec': round(float(change_pct), 2),
                'category': row.get('category', 'N/A'),
                'volume_stage': row.get('volume_stage', 'N/A'),
                'insider_score': row.get('insider_score', 0),
                'avg_surprise': row.get('avg_surprise', 0)
            })
        
        return jsonify({
            'top_picks': top_picks,
            'summary': {
                'total_analyzed': len(df),
                'avg_score': round(df['smart_money_score'].mean() if 'smart_money_score' in df.columns else 0, 1)
            }
        })
        
    except Exception as e:
        print(f"Error getting smart money picks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/etf-flows')
def get_us_etf_flows():
    """Get ETF Fund Flow Analysis"""
    try:
        csv_path = os.path.join(DATA_DIR, 'us_etf_flows.csv')
        
        if not os.path.exists(csv_path):
            return jsonify({'error': 'ETF flows not found. Run analyze_etf_flows.py first.'}), 404
        
        df = pd.read_csv(csv_path)
        
        # Calculate market sentiment
        broad_market = df[df['category'] == 'Broad Market']
        broad_score = round(broad_market['flow_score'].mean(), 1) if not broad_market.empty else 50
        
        # Sector summary
        sector_flows = df[df['category'] == 'Sector'].to_dict(orient='records')
        
        # Top inflows and outflows
        top_inflows = df.nlargest(5, 'flow_score').to_dict(orient='records')
        top_outflows = df.nsmallest(5, 'flow_score').to_dict(orient='records')
        
        # Load AI analysis
        ai_analysis_text = ""
        ai_path = os.path.join(DATA_DIR, 'etf_flow_analysis.json')
        if os.path.exists(ai_path):
            try:
                with open(ai_path, 'r', encoding='utf-8') as f:
                    ai_data = json.load(f)
                    ai_analysis_text = ai_data.get('ai_analysis', '')
            except Exception as e:
                print(f"Error loading ETF AI analysis: {e}")

        return jsonify({
            'market_sentiment_score': broad_score,
            'sector_flows': sector_flows,
            'top_inflows': top_inflows,
            'top_outflows': top_outflows,
            'all_etfs': df.to_dict(orient='records'),
            'ai_analysis': ai_analysis_text
        })
        
    except Exception as e:
        print(f"Error getting ETF flows: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/stock-chart/<ticker>')
def get_us_stock_chart(ticker):
    """Get US stock chart data (OHLC) for candlestick chart"""
    try:
        # Get period from query params (default: 1y)
        period = request.args.get('period', '1y')
        valid_periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
        if period not in valid_periods:
            period = '1y'
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return jsonify({'error': f'No data found for {ticker}'}), 404
        
        # Format for Lightweight Charts
        candles = []
        for date, row in hist.iterrows():
            candles.append({
                'time': int(date.timestamp()),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2)
            })
        
        return jsonify({
            'ticker': ticker,
            'period': period,
            'candles': candles
        })
        
    except Exception as e:
        print(f"Error getting US stock chart for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/history-dates')
def get_us_history_dates():
    """Get list of available historical analysis dates"""
    try:
        history_dir = os.path.join(DATA_DIR, 'history')
        
        if not os.path.exists(history_dir):
            return jsonify({'dates': []})
        
        dates = []
        for f in os.listdir(history_dir):
            if f.startswith('picks_') and f.endswith('.json'):
                date_str = f[6:-5]  # Extract date from filename
                dates.append(date_str)
        
        dates.sort(reverse=True)  # Most recent first
        
        return jsonify({
            'dates': dates,
            'count': len(dates)
        })
        
    except Exception as e:
        print(f"Error getting history dates: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/history/<date>')
def get_us_history_by_date(date):
    """Get picks from a specific historical date with current performance"""
    try:
        history_file = os.path.join(DATA_DIR, 'history', f'picks_{date}.json')
        
        if not os.path.exists(history_file):
            return jsonify({'error': f'No analysis found for {date}'}), 404
        
        with open(history_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # Get current prices individually
        tickers = [p['ticker'] for p in snapshot['picks']]
        current_prices = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='5d')
                if not hist.empty:
                    current_prices[ticker] = round(float(hist['Close'].dropna().iloc[-1]), 2)
            except Exception as e:
                print(f"Error fetching price for {ticker}: {e}")
        
        # Add performance data
        picks_with_perf = []
        for pick in snapshot['picks']:
            ticker = pick['ticker']
            price_at_rec = pick.get('price_at_analysis', 0) or 0
            current_price = current_prices.get(ticker, price_at_rec) or price_at_rec
            
            try:
                if pd.isna(price_at_rec): price_at_rec = 0
            except: pass

            if price_at_rec > 0:
                change_pct = ((current_price / price_at_rec) - 1) * 100
            else:
                change_pct = 0
            
            picks_with_perf.append({
                **pick,
                'sector': get_sector(ticker),
                'current_price': round(float(current_price), 2),
                'price_at_rec': round(float(price_at_rec), 2),
                'change_since_rec': round(float(change_pct), 2)
            })
        
        # Calculate average performance
        changes = [p['change_since_rec'] for p in picks_with_perf if p['price_at_rec'] > 0]
        avg_perf = round(sum(changes) / len(changes), 2) if changes else 0
        
        return jsonify({
            'analysis_date': snapshot.get('analysis_date', date),
            'analysis_timestamp': snapshot.get('analysis_timestamp', ''),
            'top_picks': picks_with_perf,
            'summary': {
                'total': len(picks_with_perf),
                'avg_performance': avg_perf
            }
        })
        
    except Exception as e:
        print(f"Error getting history for {date}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/macro-analysis')
def get_us_macro_analysis():
    """Get macro market analysis with live indicators + cached AI predictions"""
    try:
        # Get language and model preference
        lang = request.args.get('lang', 'ko')
        model = request.args.get('model', 'gemini')  # 'gemini' or 'gpt'
        
        # === LIVE MACRO INDICATORS ===
        macro_indicators = {}
        
        # Determine which file to load
        if model == 'gpt':
             analysis_path = os.path.join(DATA_DIR, 'macro_analysis_gpt.json') if lang != 'en' else os.path.join(DATA_DIR, 'macro_analysis_gpt_en.json')
             # Fallback
             if not os.path.exists(analysis_path):
                 analysis_path = os.path.join(DATA_DIR, 'macro_analysis.json') if lang != 'en' else os.path.join(DATA_DIR, 'macro_analysis_en.json')
        else: # gemini
            analysis_path = os.path.join(DATA_DIR, 'macro_analysis.json') if lang != 'en' else os.path.join(DATA_DIR, 'macro_analysis_en.json')
        
        if not os.path.exists(analysis_path):
            analysis_path = os.path.join(DATA_DIR, 'macro_analysis.json')
        
        ai_analysis = "AI 분석을 로드할 수 없습니다. macro_analyzer.py를 실행하세요."
        
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                ai_analysis = cached.get('ai_analysis', ai_analysis)
                raw_indicators = cached.get('macro_indicators', {})
                
                # Convert 'value' to 'current' for consistency with frontend
                for key, val in raw_indicators.items():
                    if isinstance(val, dict):
                        macro_indicators[key] = {
                            'current': val.get('current', val.get('value', 0)),
                            'change_1d': val.get('change_1d', 0)
                        }
        
        # === UPDATE KEY INDICATORS WITH LIVE DATA ===
        live_tickers = {
            'VIX': '^VIX', 'SPY': 'SPY', 'QQQ': 'QQQ',
            'BTC': 'BTC-USD', 'GOLD': 'GC=F', 'USD/KRW': 'KRW=X'
        }
        
        try:
            import time as t
            for name, ticker in live_tickers.items():
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='5d')
                    
                    if not hist.empty and len(hist) >= 2:
                        current = float(hist['Close'].iloc[-1])
                        prev = float(hist['Close'].iloc[-2])
                        change = current - prev
                        change_pct = (change / prev) * 100 if prev != 0 else 0
                        
                        macro_indicators[name] = {
                            'current': round(current, 2),
                            'change_1d': round(change_pct, 2)
                        }
                    t.sleep(0.3)
                except Exception as e:
                    print(f"Error fetching live {name}: {e}")
        except Exception as e:
            print(f"Error in live data loop: {e}")
        
        return jsonify({
            'macro_indicators': macro_indicators,
            'ai_analysis': ai_analysis,
            'model': model,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error getting macro analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/sector-heatmap')
def get_us_sector_heatmap():
    """Get sector performance data for heatmap visualization"""
    try:
        heatmap_path = os.path.join(DATA_DIR, 'sector_heatmap.json')
        
        if not os.path.exists(heatmap_path):
            return jsonify({'series': []})
        
        with open(heatmap_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        print(f"Error getting sector heatmap: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/options-flow')
def get_us_options_flow():
    """Get options flow data"""
    try:
        flow_path = os.path.join(DATA_DIR, 'options_flow.json')
        
        if not os.path.exists(flow_path):
            return jsonify({'error': 'Options flow data not found.'}), 404
        
        with open(flow_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        print(f"Error getting options flow: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/ai-summary/<ticker>')
def get_us_ai_summary(ticker):
    """Get AI-generated summary for a US stock"""
    try:
        lang = request.args.get('lang', 'ko')
        summary_path = os.path.join(DATA_DIR, 'ai_summaries.json')
        
        if not os.path.exists(summary_path):
             return jsonify({'error': 'AI summaries not found.'}), 404
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        if ticker not in summaries:
            return jsonify({'error': f'Summary not found for {ticker}'}), 404
        
        summary_data = summaries[ticker]
        
        if lang == 'en':
            summary = summary_data.get('summary_en', summary_data.get('summary', ''))
        else:
            summary = summary_data.get('summary_ko', summary_data.get('summary', ''))
        
        return jsonify({
            'ticker': ticker,
            'summary': summary,
            'lang': lang,
            'news_count': summary_data.get('news_count', 0),
            'updated': summary_data.get('updated', '')
        })
        
    except Exception as e:
        print(f"Error getting AI summary for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/realtime-prices', methods=['POST'])
def get_realtime_prices():
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])
        
        if not tickers: return jsonify({})
            
        yf_tickers = []
        ticker_map = {} 
        
        for t in tickers:
            yf_t = t # US stocks usually match
            yf_tickers.append(yf_t)
            ticker_map[yf_t] = t 
            
        print(f"DEBUG: Requesting {len(yf_tickers)} tickers from yfinance...")
        
        df = yf.download(yf_tickers, period='1d', interval='1m', progress=False, threads=True)
        
        prices = {}
        if not df.empty:
            df = df.ffill()
            
            # Helper to extract data from a row
            def extract_ohlc(row, ticker_key=None):
                def safe_float(val):
                    return float(val) if not pd.isna(val) else 0.0
                
                try:
                    if ticker_key: # MultiIndex
                        current = safe_float(row['Close'][ticker_key])
                        open_p = safe_float(row['Open'][ticker_key])
                        high = safe_float(row['High'][ticker_key])
                        low = safe_float(row['Low'][ticker_key])
                        vol = safe_float(row['Volume'][ticker_key])
                    else: # Single Index
                        current = safe_float(row['Close'])
                        open_p = safe_float(row['Open'])
                        high = safe_float(row['High'])
                        low = safe_float(row['Low'])
                        vol = safe_float(row['Volume'])
                    
                    return {
                        'current': current,
                        'open': open_p,
                        'high': high,
                        'low': low,
                        'volume': vol,
                        'date': row.name.strftime('%Y-%m-%d %H:%M') if hasattr(row, 'name') else datetime.now().strftime('%Y-%m-%d')
                    }
                except:
                    return None

            last_row = df.iloc[-1]
            
            if len(yf_tickers) == 1:
                 prices[tickers[0]] = extract_ohlc(last_row)
            else:
                 for yf_t in yf_tickers:
                     original_t = ticker_map.get(yf_t)
                     if original_t:
                         val = extract_ohlc(last_row, yf_t)
                         if val: prices[original_t] = val

        return jsonify(prices)
        
    except Exception as e:
        print(f"Error fetching realtime prices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/calendar')
def get_us_calendar():
    """Get Weekly Economic Calendar"""
    try:
        calendar_path = os.path.join(DATA_DIR, 'weekly_calendar.json')
        if not os.path.exists(calendar_path):
            return jsonify({'events': [], 'message': 'Calendar data not available'}), 404
        with open(calendar_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/technical-indicators/<ticker>')
def get_technical_indicators(ticker):
    """Get technical indicators (RSI, MACD, Bollinger Bands, Support/Resistance)"""
    try:
        from ta.momentum import RSIIndicator
        from ta.trend import MACD
        from ta.volatility import BollingerBands
        
        period = request.args.get('period', '1y')
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return jsonify({'error': f'No data found for {ticker}'}), 404
        
        df = hist.reset_index()
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # RSI (14-period)
        rsi_indicator = RSIIndicator(close=close, window=14)
        df['rsi'] = rsi_indicator.rsi()
        
        # MACD (12, 26, 9)
        macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
        df['macd_line'] = macd.macd()
        df['signal_line'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        
        # Bollinger Bands (20-period, 2 std)
        bb = BollingerBands(close=close, window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        
        # Helper to find S/R
        def find_support_resistance(data_low, data_high, window=20):
            supports = []
            resistances = []
            for i in range(window, len(df) - window):
                low_w = data_low.iloc[i-window:i+window+1]
                high_w = data_high.iloc[i-window:i+window+1]
                if data_low.iloc[i] == low_w.min(): supports.append(float(data_low.iloc[i]))
                if data_high.iloc[i] == high_w.max(): resistances.append(float(data_high.iloc[i]))
            
            # Simple clustering
            def cluster(levels, threshold=0.02):
                if not levels: return []
                levels = sorted(levels)
                clusters = []
                curr = [levels[0]]
                for l in levels[1:]:
                    if (l - curr[0]) / curr[0] < threshold: curr.append(l)
                    else:
                        clusters.append(sum(curr)/len(curr))
                        curr = [l]
                clusters.append(sum(curr)/len(curr))
                return [round(c, 2) for c in clusters[-5:]]

            return cluster(supports), cluster(resistances)
        
        supports, resistances = find_support_resistance(low, high)
        
        # Make serializable series
        def make_series(dates, values):
            res = []
            for d, v in zip(dates, values):
                if not pd.isna(v):
                    res.append({'time': int(d.timestamp()), 'value': round(float(v), 2)})
            return res

        return jsonify({
            'ticker': ticker,
            'rsi': make_series(df['Date'], df['rsi']),
            'macd': {
                'macd_line': make_series(df['Date'], df['macd_line']),
                'signal_line': make_series(df['Date'], df['signal_line']),
                'histogram': make_series(df['Date'], df['macd_histogram'])
            },
            'bollinger': {
                'upper': make_series(df['Date'], df['bb_upper']),
                'middle': make_series(df['Date'], df['bb_middle']),
                'lower': make_series(df['Date'], df['bb_lower'])
            },
            'support_resistance': {
                'support': supports,
                'resistance': resistances
            }
        })
        
    except Exception as e:
        print(f"Error getting technical indicators for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('🚀 Flask Server Starting on port 5001...')
    app.run(port=5001, debug=True, use_reloader=False)
