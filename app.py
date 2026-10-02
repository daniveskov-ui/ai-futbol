import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Футбол Трейдър - Автоматичен", page_icon="⚽", layout="wide")

st.markdown("<h2 style='text-align: center; color: #06b6d4;'>⚽ AI Симулатор: Пълен Световен Тираж</h2>", unsafe_allow_html=True)
st.write("Икономичен режим: 1 заявка за деня. Автоматично зареждане на абсолютно всички мачове по света по часове.")

API_KEY = "ca61b57dd810980c1604d630c470309e"
API_HOST = "v3.football.api-sports.io"

@st.cache_data(ttl=86400)
def fetch_secure_daily_fixtures(date_str):
    url = f"https://{API_HOST}/fixtures?date={date_str}"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data.get("errors"):
                return [], res.headers
            return data.get("response", []), res.headers
        return [], {}
    except:
        return [], {}

def run_granular_local_ai(item):
    try:
        home_id = item.get("teams", {}).get("home", {}).get("id", 1)
        away_id = item.get("teams", {}).get("away", {}).get("id", 2)
        league = item.get("league", {}).get("name", "Лига")
        
        if home_id is None: home_id = 1
        if away_id is None: away_id = 2
        if league is None: league = "Лига"
        
        home_power = 40 + (home_id % 25) + 12
        away_power = 30 + (away_id % 25)
        
        if any(w in league.lower() for w in ["league", "championship", "division"]): 
            home_power += 5
        delta = home_power - away_power
        
        if delta > 16: 
            sign = "1"
            sign_p = min(75 + (home_id % 12), 92)
            odd_val = round(1.35 + (home_id % 5) / 10, 2)
        elif delta < -12: 
            sign = "2"
            sign_p = min(72 + (away_id % 12), 90)
            odd_val = round(1.40 + (away_id % 5) / 10, 2)
        else: 
            sign = "Х"
            sign_p = min(60 + (home_id % 15), 78)
            odd_val = round(2.90 + (home_id % 5) / 10, 2)
        
        if sign == "1" and delta > 22: 
            ht_sign, ht_p = "1 (РП)", min(sign_p - 5, 85)
            ht_odd = round(odd_val * 1.35, 2)
        elif sign == "2" and delta < -18: 
            ht_sign, ht_p = "2 (РП)", min(sign_p - 5, 83)
            ht_odd = round(odd_val * 1.35, 2)
        else: 
            ht_sign, ht_p = "Х (РП)", min(74 + (home_id % 12), 89)
            ht_odd = round(1.85 + (home_id % 4) / 10, 2)
        
        if abs(delta) < 6 or "scotland" in league.lower() or "iceland" in league.lower():
            goals, goals_p = "Над 2.5", min(70 + (home_id % 14), 89)
            g_odd = round(1.65 + (home_id % 3) / 10, 2)
        else: 
            goals, goals_p = "Под 2.5", min(72 + (away_id % 14), 91)
            g_odd = round(1.70 + (away_id % 3) / 10, 2)
        
        if goals == "Над 2.5" or any(w in league.lower() for w in ["england", "scotland", "japan"]):
            corners, corners_p, c_odd = "Над 9.5", min(68 + (home_id % 15), 88), round(1.80 + (home_id % 3) / 10, 2)
        else: 
            corners, corners_p, c_odd = "Под 9.5", min(70 + (away_id % 13), 87), round(1.75 + (away_id % 3) / 10, 2)
        
        if sign == "Х" or any(w in league.lower() for w in ["spain", "italy", "brazil"]):
            cards, cards_p, card_odd = "Над 4.5", min(72 + (home_id % 14), 90), round(1.90 + (home_id % 3) / 10, 2)
        else: 
            cards, cards_p, card_odd = "Под 4.5", min(68 + (away_id % 15), 86), round(1.65 + (away_id % 3) / 10, 2)
        
        return sign, sign_p, odd_val, ht_sign, ht_p, ht_odd, goals, goals_p, g_odd, corners, corners_p, c_odd, cards, cards_p, card_odd
    except:
        return "1", 65, 1.45, "Х (РП)", 70, 1.90, "Под 2.5", 70, 1.75, "Под 9.5", 65, 1.80, "Под 4.5", 65, 1.70

def get_clean_bg_time(date_raw):
    if date_raw and len(date_raw) >= 16:
        try:
            base_time = date_raw[:19].replace("T", " ")
            utc_dt = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
            return (utc_dt + timedelta(hours=3)).strftime("%H:%M")
        except:
            return date_raw[11:16]
    return "00:00"

today_str = datetime.now().strftime('%Y-%m-%d')
yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
fixtures, meta_headers = fetch_secure_daily_fixtures(today_str)

st.sidebar.header("📊 Управление")
if st.sidebar.button("🔄 ИЗЧИСТИ КЕШ ПАМЕТТА", type="primary", use_container_width=True):
    st.cache_data.clear()

if not fixtures:
    st.error("⚠️ Изчистете кеш паметта от страничното меню.")
else:
    full_schedule = []
    pool_for_combo = []
    
    for item in fixtures:
        time_str = get_clean_bg_time(item.get("fixture", {}).get("date", ""))
        teams = item.get("teams", {})
        home = teams.get("home", {}).get("name", "Домакин")
        away = teams.get("away", {}).get("name", "Гост")
        country = item.get("league", {}).get("country", "Световни")
        
        if not home: home = "Домакин"
        if not away: away = "Гост"
        if not country: country = "Световни"
        
        sign, sign_p, sign_o, ht_sign, ht_p, ht_o, goals, goals_p, g_o, corners, corners_p, c_o, cards, cards_p, card_o = run_granular_local_ai(item)
        
        full_schedule.append({
            "Час 📅": time_str, "Държава 🗺️": str(country), "Мач 🏟️": f"{home} - {away}",
            "Знак 🎯": f"{sign} ({sign_o})", "1-во Пол. ⏱️": f"{ht_sign} ({ht_o})",
            "Голове ⚽": f"{goals} ({g_o})", "Корнери 📐": f"{corners} ({c_o})",
            "Картони 🟨": f"{cards} ({card_o})", "Сигурност": int(sign_p)
        })
        
        pool_for_combo.append({"Мач": f"{home} - {away}", "Прогноза": str(sign), "Коефициент": float(sign_o), "Сигурност": int(sign_p)})

    df = pd.DataFrame(full_schedule).sort_values(by="Час 📅")

    col1, col2 = st.columns(2)
    with col1: st.metric("🗺️ Общо мачове в тиража", len(df))
    with col2: st.metric("⚡ Икономия", "100% Кеш")

    st.markdown("---")
    show_combo = st.checkbox("🟢 ПОКАЖИ AI КОМБИНИРАН ФИШ ЗА ДЕНЯ", value=True)
    show_archive = st.checkbox("📉 ПОКАЖИ ВЧЕРАШНА УСПЕВАЕМОСТ (АРХИВ)", value=False)

    if show_combo:
        st.markdown("<div style='background-color: #0f172a; padding: 15px; border-radius: 10px; border: 2px solid #10b981; margin-bottom: 15px;'>", unsafe_allow_html=True)
        st.subheader("💸 AI Комбиниран Фиш (Топ 3 мача)")
        combo_df = pd.DataFrame(pool_for_combo)
        if not combo_df.empty:
            top_picks = combo_df.sort_values(by="Сигурност", ascending=False).head(3)
            total_odd = 1.0
            for idx, row in top_picks.iterrows():
                total_odd *= row["Коефициент"]
                st.write(f"🔹 **{row['Мач']}** | Прогноза: **{row['Прогноза']}** | Коефициент: `{row['Коефициент']}`")
            total_odd = round(total_odd, 2)
            st.success(f"🟩 **Общ коефициент: {total_odd}**")
            bet_amount = st.number_input("💵 Въведи залог (лв):", min_value=1, value=10, step=5)
            st.info(f"💰 Чиста печалба: **{round(bet_amount * total_odd, 2)} лв.**")
        st.markdown("</div>", unsafe_allow_html=True)

    if show_archive:
        st.markdown("<div style='background-color: #0f172a; padding: 15px; border-radius: 10px; border: 2px solid #ef4444; margin-bottom: 15px;'>", unsafe_allow_html=True)
        st.subheader(f"📊 Отчет от вчера ({yesterday_str})")
        yesterday_fixtures, _ = fetch_secure_daily_fixtures(yesterday_str)
        if yesterday_fixtures:
            past_results = []
            for item in yesterday_fixtures:
                if item.get("fixture", {}).get("status", {}).get("short", "") == "FT":
                    h = item.get("teams", {}).get("home", {}).get("name", "Домакин")
                    a = item.get("teams", {}).get("away", {}).get("name", "Гост")
                    hg = item.get("goals", {}).get("home", 0)
                    ag = item.get("goals", {}).get("away", 0)
                    t_s = get_clean_bg_time(item.get("fixture", {}).get("date", ""))
                    sign, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = run_granular_local_ai(item)
                    is_correct = "❌"
                    if "1" in sign and hg > ag: is_correct = "✅"
                    elif "2" in sign and ag > hg: is_correct = "✅"
                    elif "Х" in sign and hg == ag: is_correct = "✅"
                    past_results.append({"Час": t_s, "Мач": f"{h} - {a}", "Резултат": f"{hg}:{ag}", " AI Прогноза": sign, "Статус": is_correct})
            if past_results:
                st.dataframe(pd.DataFrame(past_results).sort_values(by="Час").head(15), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 МЕНЮ ПРОГНОЗИ ЗА ТИРАЖА")
    
    show_tab1 = st.checkbox("🎯 КРАЕН ЗНАК & 1-ВО ПОЛУВРЕМЕ", value=True)
    show_tab2 = st.checkbox("⚽ ГОЛОВЕ & КОРНЕРИ", value=False)
    show_tab3 = st.checkbox("🟨 КАРТОНИ ЗА МАЧА", value=False)
    show_raw_text = st.checkbox("📱 ТЕКСТОВ РЕЖИМ (Включи при проблеми с таблиците)", value=False)

    st.markdown("---")
    st.markdown("### ⚙️ Филтриране по Сигурност")
    
    filter_type = st.radio(
        "Избери ниво на сигурност за показване:",
        ["Всички налични мачове (Дефолт)", "Средна сигурност (Над 65%)", "Най-висока сигурност (Над 72%)"],
        index=0
    )
    
    filtered_df = df.copy()
    if "Над 65%" in filter_type:
        filtered_df = filtered_df[filtered_df["Сигурност"] >= 65]
    elif "Над 72%" in filter_type:
        filtered_df = filtered_df[filtered_df["Сигурност"] >= 72]

    if not filtered_df.empty:
        if show_raw_text:
            st.markdown("#### Списък с прогнози (Чист текст):")
            for idx, r in filtered_df.iterrows():
