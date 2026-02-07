import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# 1. UI & NO-SCROLL CSS
st.set_page_config(page_title="BPL Pro", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;} [data-testid="stStatusWidget"] {display: none;}
    
    .block-container { padding: 0rem !important; margin: 0rem !important; }
    .stApp { background: radial-gradient(circle, #001529 0%, #000000 100%); color: white; }
    
    .splash-container {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        height: 92vh; width: 100%; text-align: center; overflow: hidden;
    }
    
    [data-testid="stMetric"] { 
        background: rgba(255, 255, 255, 0.05) !important; 
        border-left: 6px solid #0056b3 !important; 
        border-radius: 12px !important; 
        padding: 22px !important; 
    }
    
    .header-banner { 
        padding: 15px; text-align: center; 
        background: #0056b3; border-bottom: 5px solid white; 
        color: white; font-family: 'Arial Black'; font-size: 24px; 
    }
    
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #000a12; color: #00a2ff; padding: 10px 0; font-family: 'Arial Black'; border-bottom: 2px solid #0056b3; }
    .ticker-content { display: inline-block; white-space: nowrap; animation: ticker 60s linear infinite; }
    .ticker-item { display: inline-block; margin-right: 80px; font-size: 18px; }
    
    /* Custom button styling */
    .stButton>button {
        background-color: #0056b3;
        color: white;
        border-radius: 8px;
        border: 1px solid white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #00a2ff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE
# Updated for the new BPL Sheet ID
SHEET_ID = "1Q5Q7_bk2RyNqJMbrYY5_VzDaPYhlEbQxqXA3BnYFBJU"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = df.columns.str.strip()
        
        # Force core columns to exist as numeric
        core_cols = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FGA', 'Game_ID', 'Win']
        for c in core_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            else:
                df[c] = 0
        
        df['PIE'] = (df['PTS'] + df['REB'] + df['AST'] + df['STL'] + df['BLK']) - (df.get('FGA', 0) * 0.5)
        
        df_p = df[df['Type'].str.lower() == 'player'].copy()
        df_t = df[df['Type'].str.lower() == 'team'].copy()
        
        # Player Stats
        gp = df_p.groupby('Player/Team')['Game_ID'].nunique().reset_index(name='GP')
        p_avg = pd.merge(df_p.groupby(['Player/Team', 'Team Name']).sum(numeric_only=True).reset_index(), gp, on='Player/Team')
        for s in ['PTS', 'REB', 'AST', 'STL', 'BLK']:
            p_avg[f'{s}/G'] = (p_avg[s] / p_avg['GP']).round(1)
            
        # Team Standings
        t_stats = df_t.groupby('Team Name').agg({
            'Win': 'sum', 
            'Game_ID': 'count', 
            'PTS': 'sum', 
            'REB': 'sum', 
            'AST': 'sum', 
            'STL': 'sum', 
            'BLK': 'sum'
        }).reset_index()
        
        t_stats['Loss'] = (t_stats['Game_ID'] - t_stats['Win']).astype(int)
        t_stats['Record'] = t_stats['Win'].astype(int).astype(str) + "-" + t_stats['Loss'].astype(str)
        
        # Team Averages
        for s in ['PTS', 'REB', 'AST', 'STL', 'BLK']:
            t_stats[f'{s}_Avg'] = (t_stats[s] / t_stats['Game_ID']).round(1)
            
        return p_avg, df_p, t_stats
    except Exception as e:
        return None, None, None

p_avg, df_raw, t_stats = load_data()

# 3. SPLASH SCREEN
if 'entered' not in st.session_state: st.session_state.entered = False

if not st.session_state.entered:
    st.markdown('<div class="splash-container">', unsafe_allow_html=True)
    logo_file = Path(__file__).parent / "logo.png"
    if logo_file.exists():
        st.image(str(logo_file), width=320)
    st.markdown("<h1 style='font-size: 60px; margin-bottom: 5px; color: white;'>BPL PRO</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #00a2ff; letter-spacing: 5px; margin-bottom: 25px;'>ELITE BASKETBALL DATA</h3>", unsafe_allow_html=True)
    if st.button("ACCESS BPL HUB", use_container_width=True):
        st.session_state.entered = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 4. MAIN INTERFACE
if p_avg is not None:
    # TICKER (Blue Themed)
    leads = []
    for cat in ['PTS', 'AST', 'REB', 'STL', 'BLK']:
        if not p_avg.empty:
            l = p_avg.nlargest(1, f'{cat}/G').iloc[0]
            leads.append(f"🔷 {cat}: {l['Player/Team']} ({l[cat+'/G']})")
    st.markdown(f'<div class="ticker-wrap"><div class="ticker-content"><span class="ticker-item">{"  •  ".join(leads)}</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="header-banner">🏀 BPL PRO | SEASON 1</div>', unsafe_allow_html=True)

    tabs = st.tabs(["👤 PLAYERS", "🏘️ STANDINGS", "🔝 LEADERS", "⚔️ VERSUS", "📖 RECORDS"])

    with tabs[0]: # PLAYERS
        table = p_avg[['Player/Team', 'Team Name', 'GP', 'PTS/G', 'REB/G', 'AST/G', 'PIE']].sort_values('PIE', ascending=False)
        sel = st.dataframe(table, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
        if len(sel.selection.rows) > 0:
            name = table.iloc[sel.selection.rows[0]]['Player/Team']
            hist = df_raw[df_raw['Player/Team'] == name].sort_values('Game_ID', ascending=False)
            st.header(f"🔍 {name} Performance Profile")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("PTS HIGH", int(hist['PTS'].max()))
                st.metric("REB HIGH", int(hist['REB'].max()))
                st.metric("AST HIGH", int(hist['AST'].max()))
            with c2:
                # Plotly for better color control
                fig = px.line(hist, x='Game_ID', y='PTS', template="plotly_dark", color_discrete_sequence=['#00a2ff'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            st.table(hist[['Game_ID', 'PTS', 'REB', 'AST', 'PIE']].head(5))

    with tabs[1]: # STANDINGS
        if t_stats is not None and not t_stats.empty:
            standings_df = t_stats[['Team Name', 'Record', 'PTS', 'REB', 'AST', 'Win']].sort_values('Win', ascending=False)
            st.dataframe(standings_df.drop(columns=['Win']), use_container_width=True, hide_index=True)

    with tabs[2]: # LEADERS
        cat_sel = st.selectbox("Category", ["PTS/G", "REB/G", "AST/G", "STL/G", "BLK/G", "PIE"])
        t10 = p_avg[['Player/Team', 'Team Name', cat_sel]].nlargest(10, cat_sel).reset_index(drop=True)
        t10.index += 1
        st.table(t10)
        st.plotly_chart(px.bar(t10, x=cat_sel, y='Player/Team', orientation='h', template="plotly_dark", color_discrete_sequence=['#0056b3']), use_container_width=True)

    with tabs[3]: # VERSUS
        v_mode = st.radio("Matchup Type", ["Player vs Player", "Team vs Team"], horizontal=True)
        v1, v2 = st.columns(2)
        if v_mode == "Player vs Player":
            p1 = v1.selectbox("P1", p_avg['Player/Team'].unique(), index=0)
            p2 = v2.selectbox("P2", p_avg['Player/Team'].unique(), index=1)
            d1, d2 = p_avg[p_avg['Player/Team']==p1].iloc[0], p_avg[p_avg['Player/Team']==p2].iloc[0]
            for s in ['PTS/G', 'REB/G', 'AST/G', 'PIE']:
                sc1, sc2 = st.columns(2)
                sc1.metric(f"{p1} {s}", d1[s], delta=round(d1[s]-d2[s], 1)); sc2.metric(f"{p2} {s}", d2[s], delta=round(d2[s]-d1[s], 1))
        else:
            t1 = v1.selectbox("Team 1", t_stats['Team Name'].unique(), index=0)
            t2 = v2.selectbox("Team 2", t_stats['Team Name'].unique(), index=1)
            td1, td2 = t_stats[t_stats['Team Name']==t1].iloc[0], t_stats[t_stats['Team Name']==t2].iloc[0]
            for s in ['PTS_Avg', 'REB_Avg', 'AST_Avg']:
                sc1, sc2 = st.columns(2)
                sc1.metric(f"{t1} {s.split('_')[0]}", td1[s], delta=round(td1[s]-td2[s], 1)); sc2.metric(f"{t2} {s.split('_')[0]}", td2[s], delta=round(td2[s]-td1[s], 1))

    with tabs[4]: # RECORDS
        c1, c2 = st.columns(2)
        r_pts = df_raw.loc[df_raw['PTS'].idxmax()]; r_reb = df_raw.loc[df_raw['REB'].idxmax()]
        r_stl = df_raw.loc[df_raw['STL'].idxmax()]; r_blk = df_raw.loc[df_raw['BLK'].idxmax()]
        c1.metric("Points Record", int(r_pts['PTS']), r_pts['Player/Team'])
        c1.metric("Steals Record", int(r_stl['STL']), r_stl['Player/Team'])
        c2.metric("Rebounds Record", int(r_reb['REB']), r_reb['Player/Team'])
        c2.metric("Blocks Record", int(r_blk['BLK']), r_blk['Player/Team'])

    st.markdown('<div style="text-align: center; color: #555; padding: 20px;">© 2026 BPL PRO DATA HUB</div>', unsafe_allow_html=True)
else:
    st.error("Connection failed. Please check the Google Sheet sharing permissions.")

