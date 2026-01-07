#!/usr/bin/env python3
"""
US Stock Smart Money Dashboard - Streamlit Version
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
    page_title="🇺🇸 US Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0e0e0e; }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2a2a4a;
    }
    .stock-card {
        background: #1a1a1a;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #2a2a2a;
    }
    h1, h2, h3 { color: #ffffff !important; }
    .positive { color: #00ff88 !important; }
    .negative { color: #ff4444 !important; }
</style>
""", unsafe_allow_html=True)

# Data Loading Functions
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
            # Convert 'value' to 'current' for consistency
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
        df = pd.read_csv('us_etf_flows.csv')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_history_dates():
    history_dir = 'history'
    if not os.path.exists(history_dir):
        return []
    dates = []
    for f in os.listdir(history_dir):
        if f.startswith('picks_') and f.endswith('.json'):
            dates.append(f[6:-5])
    return sorted(dates, reverse=True)

# Main App
def main():
    # Header
    st.markdown("# 🇺🇸 US Stock Smart Money Dashboard")
    
    # Load Data
    smart_money = load_smart_money_picks()
    macro_data = load_macro_analysis()
    
    # Analysis Date
    analysis_date = smart_money.get('analysis_date', 'N/A')
    st.markdown(f"**📅 Analysis Date:** {analysis_date}")
    
    st.divider()
    
    # Macro Indicators
    st.markdown("## 🌍 Macro Indicators")
    
    indicators = macro_data.get('macro_indicators', {})
    cols = st.columns(6)
    
    indicator_order = ['VIX', 'SPY', 'QQQ', 'BTC', 'GOLD', 'OIL']
    for i, key in enumerate(indicator_order):
        if key in indicators:
            val = indicators[key]
            current = val.get('current', 0)
            change = val.get('change_1d', 0)
            color = "🟢" if change >= 0 else "🔴"
            with cols[i % 6]:
                st.metric(
                    label=key,
                    value=f"{current:,.2f}",
                    delta=f"{change:+.2f}%"
                )
    
    st.divider()
    
    # Main Content - Two Columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Smart Money Picks Table
        st.markdown("## 📊 Final Top 10 - Smart Money Picks")
        
        picks = smart_money.get('picks', [])
        
        if picks:
            df = pd.DataFrame(picks)
            
            # Display columns
            display_cols = ['rank', 'ticker', 'name', 'sector', 'final_score', 
                           'current_price', 'target_upside', 'grade']
            available_cols = [c for c in display_cols if c in df.columns]
            
            # Format dataframe
            styled_df = df[available_cols].copy()
            if 'final_score' in styled_df.columns:
                styled_df['final_score'] = styled_df['final_score'].apply(lambda x: f"{x:.1f}")
            if 'current_price' in styled_df.columns:
                styled_df['current_price'] = styled_df['current_price'].apply(lambda x: f"${x:,.2f}")
            if 'target_upside' in styled_df.columns:
                styled_df['target_upside'] = styled_df['target_upside'].apply(lambda x: f"{x:+.1f}%")
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "rank": st.column_config.NumberColumn("Rank", width="small"),
                    "ticker": st.column_config.TextColumn("Ticker", width="small"),
                    "name": st.column_config.TextColumn("Name", width="medium"),
                    "sector": st.column_config.TextColumn("Sector", width="small"),
                    "final_score": st.column_config.TextColumn("Score", width="small"),
                    "current_price": st.column_config.TextColumn("Price", width="small"),
                    "target_upside": st.column_config.TextColumn("Upside", width="small"),
                    "grade": st.column_config.TextColumn("Grade", width="medium"),
                }
            )
        else:
            st.warning("No picks available. Run update_all.py first.")
    
    with col2:
        # AI Analysis
        st.markdown("## 🤖 AI Macro Analysis")
        ai_text = macro_data.get('ai_analysis', 'No analysis')
        st.markdown(f"""
        <div style="background: #1a1a2e; padding: 15px; border-radius: 10px; 
                    border: 1px solid #2a2a4a; max-height: 400px; overflow-y: auto;">
            {ai_text}
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ETF Flows
    st.markdown("## 💰 ETF Fund Flows")
    
    etf_df = load_etf_flows()
    if not etf_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Top Inflows")
            top_inflows = etf_df.nlargest(5, 'flow_score')[['ticker', 'name', 'flow_score']]
            st.dataframe(top_inflows, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("### 📉 Top Outflows")
            top_outflows = etf_df.nsmallest(5, 'flow_score')[['ticker', 'name', 'flow_score']]
            st.dataframe(top_outflows, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Sector Heatmap
    st.markdown("## 🗺️ Sector Heatmap")
    
    heatmap_data = load_sector_heatmap()
    if heatmap_data.get('series'):
        # Create treemap using plotly
        data_for_plot = []
        for series in heatmap_data['series']:
            for item in series.get('data', []):
                data_for_plot.append({
                    'name': item.get('x', ''),
                    'value': item.get('y', 0),
                    'change': item.get('change', 0),
                    'sector': series.get('name', 'Other')
                })
        
        if data_for_plot:
            df_heatmap = pd.DataFrame(data_for_plot)
            
            fig = px.treemap(
                df_heatmap,
                path=['sector', 'name'],
                values='value',
                color='change',
                color_continuous_scale=['#ff4444', '#333333', '#00ff88'],
                color_continuous_midpoint=0
            )
            fig.update_layout(
                paper_bgcolor='#0e0e0e',
                plot_bgcolor='#0e0e0e',
                font_color='white',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.divider()
    st.markdown(
        f"<center><small>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></center>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
