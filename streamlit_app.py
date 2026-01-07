#!/usr/bin/env python3
"""
US Stock Smart Money Dashboard - Streamlit Version
Flask 원본 대시보드와 완벽히 동일한 레이아웃
"""
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Page Config
st.set_page_config(
    page_title="🇺🇸 US Market - AI Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Koyfin-Style Dark Theme CSS
st.markdown("""
<style>
    /* Reset & Global */
    .stApp { background-color: #121212 !important; }
    .main .block-container { 
        padding: 1rem 1rem 2rem 1rem; 
        max-width: 100%; 
    }
    
    /* Hide Streamlit defaults */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    
    /* Header Bar */
    .top-header {
        background: #121212;
        border-bottom: 1px solid #2a2a2a;
        padding: 12px 16px;
        margin: -1rem -1rem 1rem -1rem;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .top-header h1 {
        font-size: 18px;
        font-weight: bold;
        color: white;
        margin: 0;
    }
    
    /* Tab Navigation */
    .tab-nav {
        background: #121212;
        border-bottom: 1px solid #2a2a2a;
        padding: 0 16px;
        margin: 0 -1rem 1rem -1rem;
        display: flex;
        gap: 4px;
    }
    .tab-item {
        padding: 8px 16px;
        font-size: 12px;
        color: #9ca3af;
        cursor: pointer;
        border-bottom: 2px solid transparent;
    }
    .tab-item.active {
        color: white;
        border-bottom-color: #3b82f6;
    }
    
    /* Section Header */
    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .section-title {
        font-size: 13px;
        font-weight: bold;
        color: #d1d5db;
    }
    .section-badge {
        font-size: 11px;
        color: #6b7280;
    }
    
    /* Market Index Card */
    .index-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    @media (max-width: 1200px) {
        .index-grid { grid-template-columns: repeat(3, 1fr); }
    }
    .index-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 12px;
        text-align: center;
        transition: background 0.2s;
    }
    .index-card:hover { background: #252525; }
    .index-card .name { font-size: 11px; color: #9ca3af; margin-bottom: 4px; }
    .index-card .price { font-size: 16px; font-weight: bold; color: white; margin-bottom: 2px; }
    .index-card .change { font-size: 11px; font-weight: 500; }
    .green { color: #22c55e; }
    .red { color: #ef4444; }
    .gray { color: #6b7280; }
    
    /* Chart Section */
    .chart-container {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 16px;
    }
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .chart-ticker { font-size: 18px; font-weight: bold; color: white; }
    .chart-info { font-size: 11px; color: #9ca3af; }
    
    /* Period Buttons */
    .period-btns { display: flex; gap: 4px; }
    .period-btn {
        padding: 4px 8px;
        font-size: 11px;
        border-radius: 4px;
        background: #374151;
        color: #d1d5db;
        border: none;
        cursor: pointer;
    }
    .period-btn.active { background: #3b82f6; color: white; }
    
    /* AI Card */
    .ai-card {
        background: linear-gradient(135deg, rgba(88, 28, 135, 0.3), rgba(30, 58, 138, 0.3));
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 6px;
        padding: 16px;
        margin-top: 16px;
    }
    .ai-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .ai-label { font-size: 13px; font-weight: bold; color: #a78bfa; }
    .ai-content { font-size: 13px; color: #d1d5db; line-height: 1.6; white-space: pre-wrap; }
    
    /* Smart Money Table */
    .table-container {
        overflow-x: auto;
        background: #1a1a1a;
        border-radius: 6px;
    }
    .sm-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    .sm-table th {
        background: #1a1a1a;
        color: #9ca3af;
        font-size: 11px;
        font-weight: normal;
        text-align: left;
        padding: 10px 12px;
        border-bottom: 1px solid #2a2a2a;
    }
    .sm-table th.center { text-align: center; }
    .sm-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #2a2a2a;
        color: #e5e7eb;
    }
    .sm-table td.center { text-align: center; }
    .sm-table tr:hover { background: #252525; }
    .ticker-cell { font-weight: bold; color: #60a5fa !important; }
    .ticker-name { font-size: 10px; color: #6b7280; }
    .score { color: #facc15; font-weight: bold; }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        background: rgba(79, 70, 229, 0.3);
        color: #a5b4fc;
        border: 1px solid rgba(79, 70, 229, 0.5);
    }
    
    /* ETF Flow Cards */
    .flow-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
    .flow-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 16px;
    }
    .flow-title { font-size: 12px; font-weight: bold; margin-bottom: 12px; }
    .flow-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        font-size: 12px;
        border-bottom: 1px solid #2a2a2a;
    }
    .flow-ticker { font-weight: bold; color: #d1d5db; width: 50px; }
    .flow-name { color: #6b7280; flex: 1; margin-left: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .flow-score { font-family: monospace; width: 60px; text-align: right; }
    
    /* Options Grid */
    .options-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
    }
    .option-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
    }
    .option-card.bullish { background: rgba(34, 197, 94, 0.1); border-color: rgba(34, 197, 94, 0.3); }
    .option-card.bearish { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); }
    .option-ticker { font-weight: bold; color: #e5e7eb; font-size: 12px; }
    .option-pc { font-size: 10px; color: #6b7280; margin-top: 4px; }
    .option-sentiment { font-size: 10px; margin-top: 2px; }
    
    /* Macro Indicators */
    .macro-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 8px;
        margin-bottom: 16px;
    }
    @media (max-width: 1200px) {
        .macro-grid { grid-template-columns: repeat(5, 1fr); }
    }
    .macro-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        padding: 8px;
        text-align: center;
    }
    .macro-label { font-size: 10px; color: #6b7280; }
    .macro-value { font-size: 12px; font-weight: bold; color: white; }
    .macro-change { font-size: 10px; }
</style>
""", unsafe_allow_html=True)

# ============ Data Loading ============
@st.cache_data(ttl=300)
def load_smart_money_picks():
    try:
        with open('smart_money_current.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'picks': [], 'analysis_date': '', 'analysis_timestamp': ''}

@st.cache_data(ttl=300)
def load_macro_analysis():
    try:
        with open('macro_analysis.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            indicators = {}
            for key, val in data.get('macro_indicators', {}).items():
                if isinstance(val, dict):
                    indicators[key] = {
                        'current': val.get('current', val.get('value', 0)),
                        'change_1d': val.get('change_1d', 0)
                    }
            return {'macro_indicators': indicators, 'ai_analysis': data.get('ai_analysis', '')}
    except:
        return {'macro_indicators': {}, 'ai_analysis': 'No analysis available'}

@st.cache_data(ttl=300)
def load_sector_heatmap():
    try:
        with open('sector_heatmap.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'series': []}

@st.cache_data(ttl=300)
def load_etf_flows():
    try:
        return pd.read_csv('us_etf_flows.csv')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_options_flow():
    try:
        with open('options_flow.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'options_flow': []}

@st.cache_data(ttl=300)
def load_history_dates():
    history_dir = 'history'
    if not os.path.exists(history_dir):
        return []
    dates = [f[6:-5] for f in os.listdir(history_dir) if f.startswith('picks_') and f.endswith('.json')]
    return sorted(dates, reverse=True)

# ============ Main App ============
def main():
    # Load Data
    smart_money = load_smart_money_picks()
    macro_data = load_macro_analysis()
    indicators = macro_data.get('macro_indicators', {})
    
    # ===== Header =====
    st.markdown("""
    <div class="top-header">
        <h1>🇺🇸 US Market</h1>
    </div>
    <div class="tab-nav">
        <div class="tab-item active">🇺🇸 US Market</div>
        <div class="tab-item">Economic Calendar</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== Section 1: Market Indices =====
    st.markdown("""
    <div class="section-header">
        <span class="section-title">🇺🇸 US Market Indices</span>
        <span class="section-badge">Real-time Data</span>
    </div>
    """, unsafe_allow_html=True)
    
    index_order = ['VIX', '10Y_Yield', '2Y_Yield', 'BTC', 'DXY', 'FearGreed', 'GOLD', 'OIL', 'QQQ', 'SPY', 'YieldSpread']
    cards_html = '<div class="index-grid">'
    for key in index_order:
        if key in indicators:
            val = indicators[key]
            current = val.get('current', 0)
            change = val.get('change_1d', 0)
            color_class = 'green' if change >= 0 else 'red'
            sign = '+' if change >= 0 else ''
            cards_html += f'''
            <div class="index-card">
                <div class="name">{key}</div>
                <div class="price">{current:,.2f}</div>
                <div class="change {color_class}">{sign}{change:.2f}%</div>
            </div>'''
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    
    # ===== Section 2: Chart + Heatmap (2:1) =====
    col1, col2 = st.columns([2, 1])
    
    with col1:
        picks = smart_money.get('picks', [])
        ticker_list = [p['ticker'] for p in picks] if picks else ['SPY']
        selected = st.selectbox("Select Stock", ticker_list, key="ticker_select", label_visibility="collapsed")
        
        st.markdown(f"""
        <div class="chart-container">
            <div class="chart-header">
                <div>
                    <div class="chart-ticker">{selected}</div>
                    <div class="chart-info">Click table row for details</div>
                </div>
                <div class="period-btns">
                    <span class="period-btn">1M</span>
                    <span class="period-btn">3M</span>
                    <span class="period-btn">6M</span>
                    <span class="period-btn active">1Y</span>
                    <span class="period-btn">ALL</span>
                </div>
            </div>
            <div style="height: 280px; display: flex; align-items: center; justify-content: center; color: #6b7280;">
                📈 Interactive chart available in Flask version
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-title" style="margin-bottom: 8px;">🗺️ Market Map</div>', unsafe_allow_html=True)
        heatmap_data = load_sector_heatmap()
        if heatmap_data.get('series'):
            data_for_plot = []
            for series in heatmap_data['series']:
                for item in series.get('data', []):
                    data_for_plot.append({
                        'name': item.get('x', ''),
                        'value': abs(item.get('y', 1)),
                        'change': item.get('change', 0),
                        'sector': series.get('name', 'Other')
                    })
            if data_for_plot:
                df_hm = pd.DataFrame(data_for_plot)
                fig = px.treemap(df_hm, path=['sector', 'name'], values='value',
                    color='change', color_continuous_scale=['#ef4444', '#333333', '#22c55e'],
                    color_continuous_midpoint=0)
                fig.update_layout(paper_bgcolor='#1a1a1a', plot_bgcolor='#1a1a1a',
                    font_color='white', height=300, margin=dict(t=0, b=0, l=0, r=0))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)
    
    # ===== Section 3: AI Summary =====
    st.markdown("""
    <div class="ai-card">
        <div class="ai-header">
            <span>🤖</span>
            <span class="ai-label">AI 투자 분석</span>
        </div>
        <div class="ai-content">종목을 선택하면 AI 분석이 표시됩니다. (Flask 버전에서 상세 분석 가능)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== Section 4: Smart Money Picks =====
    st.markdown("""
    <div class="section-header" style="margin-top: 24px;">
        <span class="section-title">📊 Final Top 10 - Smart Money Picks</span>
    </div>
    """, unsafe_allow_html=True)
    
    picks = smart_money.get('picks', [])
    if picks:
        table_html = '''
        <div class="table-container">
        <table class="sm-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Ticker</th>
                    <th class="center">Sector</th>
                    <th class="center">Score</th>
                    <th class="center">AI 추천</th>
                    <th class="center">추천가</th>
                    <th class="center">현재가</th>
                    <th class="center">변동</th>
                    <th class="center">목표 Upside</th>
                </tr>
            </thead>
            <tbody>'''
        
        for p in picks:
            change = p.get('target_upside', 0)
            change_color = 'green' if change >= 0 else 'red'
            table_html += f'''
                <tr>
                    <td>{p.get('rank', '')}</td>
                    <td>
                        <span class="ticker-cell">{p.get('ticker', '')}</span>
                        <div class="ticker-name">{p.get('name', '')[:25]}</div>
                    </td>
                    <td class="center">{p.get('sector', 'N/A')}</td>
                    <td class="center score">{p.get('final_score', 0):.1f}</td>
                    <td class="center"><span class="badge">{p.get('ai_recommendation', 'Hold')}</span></td>
                    <td class="center">${p.get('price_at_analysis', p.get('current_price', 0)):,.2f}</td>
                    <td class="center" style="color: white; font-family: monospace;">${p.get('current_price', 0):,.2f}</td>
                    <td class="center {change_color}">0%</td>
                    <td class="center {change_color}">{change:+.1f}%</td>
                </tr>'''
        
        table_html += '</tbody></table></div>'
        st.markdown(table_html, unsafe_allow_html=True)
    
    # ===== Section 5: ETF Flows =====
    st.markdown("""
    <div class="section-header" style="margin-top: 24px;">
        <span class="section-title">💰 ETF Fund Flows - 자금 흐름</span>
    </div>
    """, unsafe_allow_html=True)
    
    etf_df = load_etf_flows()
    if not etf_df.empty:
        top_in = etf_df.nlargest(5, 'flow_score')
        top_out = etf_df.nsmallest(5, 'flow_score')
        
        flow_html = '<div class="flow-container">'
        
        # Inflows
        flow_html += '<div class="flow-card"><div class="flow-title green">📈 Top Inflows</div>'
        for _, row in top_in.iterrows():
            flow_html += f'''
            <div class="flow-item">
                <span class="flow-ticker">{row['ticker']}</span>
                <span class="flow-name">{row.get('name', '')}</span>
                <span class="flow-score green">{row['flow_score']:.1f}</span>
            </div>'''
        flow_html += '</div>'
        
        # Outflows
        flow_html += '<div class="flow-card"><div class="flow-title red">📉 Top Outflows</div>'
        for _, row in top_out.iterrows():
            flow_html += f'''
            <div class="flow-item">
                <span class="flow-ticker">{row['ticker']}</span>
                <span class="flow-name">{row.get('name', '')}</span>
                <span class="flow-score red">{row['flow_score']:.1f}</span>
            </div>'''
        flow_html += '</div></div>'
        
        st.markdown(flow_html, unsafe_allow_html=True)
    
    # ===== Section 6: Options Flow =====
    st.markdown("""
    <div class="section-header" style="margin-top: 24px;">
        <span class="section-title">📊 Options Flow - 기관 포지션</span>
    </div>
    """, unsafe_allow_html=True)
    
    options_data = load_options_flow()
    flows = options_data.get('options_flow', [])[:10]
    
    if flows:
        options_html = '<div class="options-grid">'
        for flow in flows:
            ticker = flow.get('ticker', '')
            metrics = flow.get('metrics', {})
            pc = metrics.get('pc_ratio', 0)
            sentiment = 'Bullish' if pc < 0.6 else ('Bearish' if pc > 1.0 else 'Neutral')
            card_class = 'bullish' if sentiment == 'Bullish' else ('bearish' if sentiment == 'Bearish' else '')
            sent_color = 'green' if sentiment == 'Bullish' else ('red' if sentiment == 'Bearish' else 'gray')
            
            options_html += f'''
            <div class="option-card {card_class}">
                <div class="option-ticker">{ticker}</div>
                <div class="option-pc">P/C: {pc:.2f}</div>
                <div class="option-sentiment {sent_color}">{sentiment}</div>
            </div>'''
        options_html += '</div>'
        st.markdown(options_html, unsafe_allow_html=True)
    
    # ===== Section 7: Macro Analysis =====
    st.markdown("""
    <div class="section-header" style="margin-top: 24px;">
        <span class="section-title">🌍 Macro Analysis - AI 예측</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Macro Grid
    macro_html = '<div class="macro-grid">'
    for key, val in list(indicators.items())[:10]:
        current = val.get('current', 0)
        change = val.get('change_1d', 0)
        change_color = 'green' if change >= 0 else 'red'
        sign = '+' if change >= 0 else ''
        macro_html += f'''
        <div class="macro-card">
            <div class="macro-label">{key}</div>
            <div class="macro-value">{current:,.2f}</div>
            <div class="macro-change {change_color}">{sign}{change:.2f}%</div>
        </div>'''
    macro_html += '</div>'
    st.markdown(macro_html, unsafe_allow_html=True)
    
    # AI Macro Card
    ai_text = macro_data.get('ai_analysis', '분석 로딩 중...')
    st.markdown(f"""
    <div class="ai-card">
        <div class="ai-header">
            <span>🤖</span>
            <span class="ai-label">Gemini 3.0 매크로 분석</span>
        </div>
        <div class="ai-content">{ai_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div style="text-align: center; padding: 24px 0; color: #6b7280; font-size: 11px;">
        Analysis Date: {smart_money.get('analysis_date', 'N/A')} | 
        Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
