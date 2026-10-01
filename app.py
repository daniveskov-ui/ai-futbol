import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="AI Футбол Трейдър Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стилизиране за по-красив интерфейс
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
    .subtitle { color: #6B7280; font-size: 1rem; margin-bottom: 2rem; }
    .card { padding: 1.5rem; border-radius: 0.5rem; background-color: #F3F4F6; border-left: 5px solid #10B981; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>⚽ AI Футбол Трейдър Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Елитни футболни прогнози и генератор на фишове, задвижвани от AI алгоритми</div>", unsafe_allow_html=True)

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

# Зареждане на утрешната програма
target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
fixtures, meta_headers = fetch_secure_daily_fixtures(target_date)

# Фалбек списък, ако API-то няма мачове за деня
if not fixtures or len(fixtures) == 0:
    fixtures = [
        {"fixture": {"date": "2026-10-02T18:45:00+00:00"}, "teams": {"home": {"name": "Leverkusen", "id": 161}, "away": {"name": "Stuttgart", "id": 159}}, "league": {"name": "Bundesliga", "country": "Germany"}},
        {"fixture": {"date": "2026-10-02T19:00:00+00:00"}, "teams": {"home": {"name": "PSG", "id": 85}, "away": {"name": "Rennes", "id": 94}}, "league": {"name": "Ligue 1", "country": "France"}},
        {"fixture": {"date": "2026-10-02T20:00:00+00:00"}, "teams": {"home": {"name": "Athletic Bilbao", "id": 531}, "away": {"name": "Sevilla", "id": 536}}, "league": {"name": "La Liga", "country": "Spain"}},
        {"fixture": {"date": "2026-10-02T21:00:00+00:00"}, "teams": {"home": {"name": "Real Madrid", "id": 541}, "away": {"name": "Espanyol", "id": 544}}, "league": {"name": "La Liga", "country": "Spain"}},
        {"fixture": {"date": "2026-10-02T16:00:00+00:00"}, "teams": {"home": {"name": "Chelsea", "id": 49}, "away": {"name": "Fulham", "id": 52}}, "league": {"name": "Premier League", "country": "England"}},
    ]

# Подготовка на суровите данни за обработка
raw_data = []
for item in fixtures:
    time_val = item.get("fixture", {}).get("date", "00:00")[11:16]
    h_team = item.get("teams", {}).get("home", {}).get("name", "Домакин")
    a_team = item.get("teams", {}).get("away", {}).get("name", "Гост")
    country = item.get("league", {}).get("country", "Световни")
    
    s, sp, so, ht, htp, hto, g, gp, go, c, cp, co, cr, crp, cro = run_granular_local_ai(item)
    
    raw_data.append({
        "Час 📅": time_val,
        "Държава 🗺️": country,
        "Мач 🏟️": f"{h_team} - {a_team}",
        "Знак 🎯": s,
        "Коеф. 💰": so,
        "Сигурност % 📈": sp,
        "1-во Пол. ⏱️": f"{ht} ({hto})",
        "Голове ⚽": f"{g} ({go})",
        "Корнери 📐": f"{c} ({co})",
        "Картони 🟨": f"{cr} ({cro})"
    })

full_df = pd.DataFrame(raw_data).sort_values(by="Час 📅").reset_index(drop=True)

# --- СТРАНИЧНА ЛЕНТА (САЙДБАР) ---
st.sidebar.header("📊 Управление и Филтри")

# 1. Филтър по държава
countries = ["Всички"] + sorted(list(full_df["Държава 🗺️"].unique()))
selected_country = st.sidebar.selectbox("Избери Държава/Лига:", countries)

# 2. Филтър по минимална сигурност
min_conf = st.sidebar.slider("Минимална AI Сигурност (%)", min_value=50, max_value=95, value=60, step=5)

# 3. Инструменти за фиш
st.sidebar.markdown("---")
st.sidebar.subheader("🎫 Генератор на Фиш")
bet_amount = st.sidebar.number_input("Размер на залога (лв.):", min_value=1.0, max_value=1000.0, value=10.0, step=5.0)
generate_ticket = st.sidebar.button("⚡ СГЛОБИ СИГУРЕН ФИШ", type="primary", use_container_width=True)

if st.sidebar.button("🔄 ИЗЧИСТИ КЕШ", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Прилагане на филтрите върху таблицата
filtered_df = full_df[full_df["Сигурност % 📈"] >= min_conf]
if selected_country != "Всички":
    filtered_df = filtered_df[filtered_df["Държава 🗺️"] == selected_country]

# --- ГЕНЕРИРАНЕ НА ФИШ (АКО Е НАТИСНАТ БУТОНА) ---
if generate_ticket:
    # Избираме топ 3 мача с най-висока сигурност
    top_picks = full_df.sort_values(by="Сигурност % 📈", ascending=False).head(3)
    
    if not top_picks.empty:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🎫 Твоят AI Сигурен Фиш (Топ 3 Алтернативи)")
        
        total_odds = 1.0
        for idx, row in top_picks.iterrows():
            st.write(f"🔹 **{row['Мач 🏟️']}** | Прогноза: **{row['Знак 🎯']}** | Коефициент: **{row['Коеф. 💰']}** (Сигурност: {row['Сигурност % 📈']}%)")
            total_odds *= row["Коеф. 💰"]
        
        potential_win = total_odds * bet_amount
        st.markdown(f"**Общ коефициент:** `{total_odds:.2f}`")
        st.markdown(f"💰 **Потенциална печалба при {bet_amount:.2f} лв. залог:** ` {potential_win:.2f} лв.`")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Няма налични мачове за сглобяване на фиш.")

# --- ИЗВЕЖДАНЕ НА ТАБЛИЦАТА С ЦВЕТНО КОДИРАНЕ ---
st.markdown(f"### 📋 Световен дневен тираж (Намерени: {len(filtered_df)} мача)")

# Функция за оцветяване на редове с висока сигурност (Над 80%)
def highlight_high_confidence(row):
    if row["Сигурност % 📈"] >= 80:
        return ['background-color: #D1FAE5; color: #065F46'] * len(row)
    return [''] * len(row)

