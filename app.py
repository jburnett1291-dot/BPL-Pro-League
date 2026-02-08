import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from pathlib import Path

# 1. UI & NO-SCROLL CSS
st.set_page_config(page_title="BPL Pro", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;} [data-testid="stStatusWidget"] {display: none;}
    .block-container { padding: 0rem !important; margin: 0rem !important; }
    .stApp { background: radial-gradient(circle, #001529 0%, #000000 100%); color: white; }
    .splash-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 92vh; width: 100%; text-align: center; overflow: hidden; }
    [data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05) !important; border-left: 6px solid #0056b3 !important; border-radius: 12px !important; padding: 22px !important; }
    .header-banner { padding: 15px; text-align: center; background: #0056b3; border-bottom: 5px solid white; color: white; font-family: 'Arial Black'; font-size: 24px; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #000a12; color: #00a2ff; padding: 10px 0; font-family: 'Arial Black'; border-bottom: 2px solid #0056b3; }
    .ticker-content { display: inline-block; white-space: nowrap; animation: ticker 60s linear infinite; }
    .ticker-item { display: inline-block; margin-right: 80px; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE (SECURE CONNECTION)
@st.cache_data(ttl=60)
def load_data():
    try:
        # Connect using the Service Account email credentials stored in Secrets
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(
            spreadsheet="https://docs.google.com/spreadsheets/d/1Q5Q7_bk2RyNqJMbrYY5_VzDaPYhlEbQxqXA3BnYFBJU/edit#gid=0",
            ttl="1m"
        )
        
        df.columns = df.columns.str.strip()
        
        # Numeric processing
        core_cols = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FGA', 'Game_ID', 'Win']
        for c in core_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            else:
                df[c] = 0
        
        df['PIE'] = (df['PTS'] + df['REB'] + df['AST'] + df['STL'] + df['BLK']) - (df.get('FGA', 0) * 0.5)
        
        df_p = df[df['Type'].str.lower() == 'player'].copy()
        df_t = df[df['Type'].str.lower() == 'team'].copy()
        
        # Player Avg logic
        gp = df_p.groupby('Player/Team')['Game_ID'].nunique().reset_index(name='GP')
        p_avg = pd.merge(df_p.groupby(['Player/Team', 'Team Name']).sum(numeric_only=True).reset_index(), gp, on='Player/Team')
        for s in ['PTS', 'REB', 'AST', 'STL', 'BLK']:
            p_avg[f'{s}/G'] = (p_avg[s] / p_avg['GP']).round(1)
            
        # Team Standings logic
        t_stats = df_t.groupby('Team Name').agg({'Win': 'sum', 'Game_ID': 'count', 'PTS': 'sum', 'REB': 'sum', 'AST': 'sum'}).reset_index()
        t_stats['Loss'] = (t_stats['Game_ID'] - t_stats['Win']).astype(int)
        t_stats['Record'] = t_stats['Win'].astype(int).astype(str) + "-" + t_stats['Loss'].astype(str)
        
        return p_avg, df_p, t_stats
    except Exception as e:
        st.error(f"Authentication Failed: {e}")
        return None, None, None

p_avg, df_raw, t_stats = load_data()

# 3. SPLASH SCREEN
if 'entered' not in st.session_state: st.session_state.entered = False

if not st.session_state.entered:
    st.markdown('<div class="splash-container">', unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 60px; margin-bottom: 5px;'>BPL PRO</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #00a2ff; letter-spacing: 5px; margin-bottom: 25px;'>SECURE TERMINAL</h3>", unsafe_allow_html=True)
    if st.button("ENTER BPL HUB", use_container_width=True):
        st.session_state.entered = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 4. MAIN INTERFACE (TICKER & TABS)
if p_avg is not None:
    leads = []
    for cat in ['PTS', 'AST', 'REB']:
        if not p_avg.empty:
            l = p_avg.nlargest(1, f'{cat}/G').iloc[0]
            leads.append(f"🔷 {cat}: {l['Player/Team']} ({l[cat+'/G']})")
    st.markdown(f'<div class="ticker-wrap"><div class="ticker-content"><span class="ticker-item">{"  •  ".join(leads)}</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="header-banner">🏀 BPL PRO | SEASON 1</div>', unsafe_allow_html=True)

    tabs = st.tabs(["👤 PLAYERS", "🏘️ STANDINGS", "🔝 LEADERS", "⚔️ VERSUS"])

    with tabs[0]:
        st.dataframe(p_avg[['Player/Team', 'Team Name', 'GP', 'PTS/G', 'REB/G', 'AST/G', 'PIE']], use_container_width=True, hide_index=True)

    with tabs[1]:
        st.dataframe(t_stats[['Team Name', 'Record', 'PTS', 'REB', 'AST']], use_container_width=True, hide_index=True)

    with tabs[2]:
        cat_sel = st.selectbox("Category", ["PTS/G", "REB/G", "AST/G", "PIE"])
        t10 = p_avg[['Player/Team', 'Team Name', cat_sel]].nlargest(10, cat_sel)
        st.plotly_chart(


