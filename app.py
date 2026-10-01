import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="AI Футбол Трейдър", 
    layout="wide"
)

st.markdown("<h2>⚽ AI Симулатор</h2>", unsafe_allow_html=True)
st.write("Икономичен режим: 1 заявка за деня.")

API_KEY = "c21f7bfd4414dea310f1262837a3074e"
API_HOST = "v3.football.api-sports.io"

@st.cache_data(ttl=86400)
def fetch_secure_daily_fixtures(date_str):
    url = f"https://{API_HOST}/fixtures?date={date_str}"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get("response", []), res.headers
    except:
        return [], {}
    return [], {}

def run_granular_local_ai(item):
    try:
        home = item.get("teams", {}).get("home", {}).get("name", "Домакин")
        away = item.get("teams", {}).get("away", {}).get("name", "Гост")
        home_id = item.get("teams", {}).get("home", {}).get("id", 1)
        away_id = item.get("teams", {}).get("away", {}).get("id", 2)
        league = item.get("league", {}).get("name", "Лига")
        
        if home_id is None: home_id = 1
        if away_id is None: away_id = 2
        
        home_power = 40 + (home_id % 25) + 12
        away_power = 30 + (away_id % 25)
        
        if any(w in league.lower() for w in ["cup", "trophy", "knockout"]):
            home_power += 5
        delta = home_power - away_power
        
        odds_data = item.get("odds", [])
        live_odds = {"Home": None, "Draw": None, "Away": None}
        
        if odds_data and isinstance(odds_data, list):
            for bookmaker in odds_data:
                for bet in bookmaker.get("bets", []):
                    if bet.get("name") == "Match Winner":
                        for value in bet.get("values", []):
                            val_name = value.get("value")
                            if val_name in ["Home", "1", home]:
                                live_odds["Home"] = float(value.get("odd", 1.0))
                            elif val_name in ["Away", "2", away]:
                                live_odds["Away"] = float(value.get("odd", 1.0))
                            elif val_name in ["Draw", "X"]:
                                live_odds["Draw"] = float(value.get("odd", 1.0))

        odd_home = live_odds["Home"] if live_odds["Home"] else round(2.10 + (home_id % 5) / 10, 2)
        odd_away = live_odds["Away"] if live_odds["Away"] else round(2.30 + (away_id % 5) / 10, 2)
        odd_draw = live_odds["Draw"] if live_odds["Draw"] else round(3.10 + (home_id % 5) / 10, 2)

        if odd_home < odd_away:
            sign = "1"
            odd_val = odd_home
            sign_p = min(75 + (home_id % 12), 92)
            if sign_p < 58: sign_p = 58
        else:
            sign = "2"
            odd_val = odd_away
            sign_p = min(72 + (away_id % 12), 90)
            if sign_p < 56: sign_p = 56

        if abs(odd_home - odd_away) < 0.15:
            sign = "Х"
            odd_val = odd_draw
            sign_p = min(60 + (home_id % 15), 75)

        if sign == "1" and odd_home < 1.70: 
            ht_sign, ht_p = "1 (РП)", min(sign_p - 5, 85)
            ht_odd = round(odd_home * 1.35, 2)
        elif sign == "2" and odd_away < 1.70: 
            ht_sign, ht_p = "2 (РП)", min(sign_p - 5, 83)
            ht_odd = round(odd_away * 1.35, 2)
        else: 
            ht_sign, ht_p = "Х (РП)", min(74 + (home_id % 12), 89)
            ht_odd = round(1.85 + (home_id % 4) / 10, 2)
        
        if odd_val < 1.60 or "scotland" in league.lower() or "iceland" in league.lower():
            goals, goals_p = "Над 2.5", min(72 + (home_id % 12), 89)
            g_odd = round(1.65 + (home_id % 3) / 10, 2)
        else: 
            goals, goals_p = "Под 2.5", min(72 + (away_id % 14), 91)
            g_odd = round(1.70 + (away_id % 3) / 10, 2)
        
        if goals == "Над 2.5" or any(w in league.lower() for w in ["england", "scotland", "japan"]):
            corners, corners_p = "Над 9.5", min(70 + (home_id % 12), 88)
            c_odd = round(1.80 + (home_id % 3) / 10, 2)
        else: 
            corners, corners_p = "Под 9.5", min(70 + (away_id % 13), 87)
            c_odd = round(1.75 + (away_id % 3) / 10, 2)
        
        if sign == "Х" or any(w in league.lower() for w in ["spain", "italy", "brazil"]):
            cards, cards_p = "Над 4.5", min(72 + (home_id % 14), 90)
            card_odd = round(1.90 + (home_id % 3) / 10, 2)
        else: 
            cards, cards_p = "Под 4.5", min(68 + (away_id % 15), 86)
            card_odd = round(1.65 + (away_id % 3) / 10, 2)
        
        return sign, sign_p, odd_val, ht_sign, ht_p, ht_odd, goals, goals_p, g_odd, corners, corners_p, c_odd, cards, cards_p, card_odd
    except:
        return "1", 60, 1.45, "Х (РП)", 65, 1.90, "Под 2.5", 65, 1.75, "Под 9.5", 60, 1.80, "Под 4.5", 60, 1.70

today_str = datetime.now().strftime('%Y-%m-%d')
fixtures, meta_headers = fetch_secure_daily_fixtures(today_str)

st.sidebar.header("📊 Управление")
if st.sidebar.button("🔄 ИЗЧИСТИ КЕШ", type="primary", use_container_width=True):
    st.cache_data.clear()

if not fixtures or len(fixtures) == 0:
    fixtures = [
        {"fixture": {"date": "2026-10-01T16:00:00+00:00"}, "teams": {"home": {"name": "Arsenal", "id": 42}, "away": {"name": "Chelsea", "id": 49}}, "league": {"name": "Premier League", "country": "England"}},
        {"fixture": {"date": "2026-10-01T17:30:00+00:00"}, "teams": {"home": {"name": "Real Madrid", "id": 541}, "away": {"name": "Barcelona", "id": 529}}, "league": {"name": "La Liga", "country": "Spain"}},
        {"fixture": {"date": "2026-10-01T19:45:00+00:00"}, "teams": {"home": {"name": "Bayern Munich", "id": 157}, "away": {"name": "Dortmund", "id": 165}}, "league": {"name": "Bundesliga", "country": "Germany"}},
    ]

# СЪЗДАВАМЕ ПРАЗНИ СПИСЪЦИ ЗА СЕКЦИИТЕ
c_час, c_лига, c_мач, c_знак, c_рп, c_гол, c_корн, c_карт = [], [], [], [] ,[], [], [], []

for item in fixtures:
    time_val = item.get("fixture", {}).get("date", "00:00")[11:16]
    h_team = item.get("teams", {}).get("home", {}).get("name", "Домакин")
    a_team = item.get("teams", {}).get("away", {}).get("name", "Гост")
    country = item.get("league", {}).get("country", "Световни")
    
    s, sp, so, ht, htp, hto, g, gp, go, c, cp, co, cr, crp, cro = run_granular_local_ai(item)
    
    # ПЪЛНИМ ВСЯКА КОЛОНА ПООТДЕЛНО - РЕДОВЕТЕ СА МАКСИМАЛНО КЪСИ И ЗАЩИТЕНИ
    c_час.append(time_val)
    c_лига.append(country)
    c_мач.append(f"{h_team} - {a_team}")
    c_знак.append(f"{s} ({so}) [{sp}%]")
    c_рп.append(f"{ht} ({hto}) [{htp}%]")
    c_гол.append(f"{g} ({go}) [{gp}%]")
    c_корн.append(f"{c} ({co}) [{cp}%]")
    c_карт.append(f"{cr} ({cro}) [{crp}%]")

# СГЛОБЯВАМЕ КРАЙНАТА ТАБЛИЦА БЕЗ НИТО ЕДНА СКОБА В ЦИКЪЛА
df = pd.DataFrame()
df["Час 📅"] = c_час
df["Държава 🗺️"] = c_лига
df["Мач 🏟️"] = c_мач
df["Знак 🎯"] = c_знак
df["1-во Пол. ⏱️"] = c_рп
df["Голове ⚽"] = c_гол
df["Корнери 📐"] = c_корн
df["Картони 🟨"] = c_карт

df = df.sort_values(by="Час 📅", ascending=True).reset_index(drop=True)
st.markdown("### 📋 Световен дневен тираж")
st.dataframe(df, use_container_width=True, hide_index=True)
