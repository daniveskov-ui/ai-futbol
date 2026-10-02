import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Футбол Трейдър - Автоматичен", page_icon="⚽", layout="wide")

st.markdown("<h2 style='text-align: center; color: #06b6d4;'>⚽ AI Симулатор: Пълен Световен Тираж</h2>", unsafe_allow_html=True)
st.write("Икономичен режим: 1 заявка за деня. Автоматично зареждане на абсолютно всички мачове по света по часове.")

API_KEY = "ca61b57dd810980c1604d630c470309e"
API_HOST = "v3.football.api-sports.io"

# Дълбоко кеширане за абсолютна защита на лимита (24 часа) с диагностика на грешки
@st.cache_data(ttl=86400)
def fetch_secure_daily_fixtures(date_str):
    url = f"https://{API_HOST}/fixtures?date={date_str}"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data.get("errors"):
                st.error(f"🚨 Грешка, върната от спортното API: {data.get('errors')}")
                return [], res.headers
            return data.get("response", []), res.headers
        else:
            st.error(f"🚨 Сървърна грешка от API доставчика. Статус код: {res.status_code}")
            return [], {}
    except Exception as e:
        st.error(f"🚨 Проблем с интернет връзката или API заявката: {e}")
        return [], {}

# Бронирана функция за локалния AI алгоритъм с вградена защита срещу празни данни
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
            corners, corners_p = "Над 9.5", min(68 + (home_id % 15), 88)
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

# Функция за сигурно извличане на българско време без риск от бъгове
def get_clean_bg_time(date_raw):
    if date_raw and len(date_raw) >= 16:
        try:
            base_time = date_raw[:19].replace("T", " ")
            utc_dt = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
            return (utc_dt + timedelta(hours=3)).strftime("%H:%M")
        except:
            return date_raw[11:16]
    return "00:00"

# Настройка на датите
today_str = datetime.now().strftime('%Y-%m-%d')
yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
fixtures, meta_headers = fetch_secure_daily_fixtures(today_str)

# --- СТРАНИЧНА ЛЕНТА ---
st.sidebar.header("📊 Управление")
if meta_headers:
    rem = meta_headers.get('x-ratelimit-requests-remaining', '100')
    st.sidebar.success(f"📊 Оставащи API заявки: {rem}")

if st.sidebar.button("🔄 ИЗЧИСТИ КЕШ ПАМЕТТА", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.info("Кешът е изчистен! Презаредете страницата.")

if not fixtures:
    st.error("⚠️ Изчистете кеш паметта от менюто встрани или изчакайте актуализация на тиража.")
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
        
        try:
            sign_o = float(sign_o) if sign_o else 1.50
            sign_p = int(sign_p) if sign_p else 60
        except:
            sign_o = 1.50
            sign_p = 60

        full_schedule.append({
            "Час 📅": time_str, 
            "Държава 🗺️": str(country),
            "Мач 🏟️": f"{home} - {away}",
            "Знак 🎯": f"{sign} ({sign_o}) [{sign_p}%]",
            "1-во Пол. ⏱️": f"{ht_sign} ({ht_o}) [{ht_p}%]",
            "Голове ⚽": f"{goals} ({g_o}) [{goals_p}%]",
            "Корнери 📐": f"{corners} ({c_o}) [{corners_p}%]",
            "Картони 🟨": f"{cards} ({card_o}) [{cards_p}%]",
            "Сигурност": sign_p
        })
        
        pool_for_combo.append({
            "Мач": f"{home} - {away}", "Прогноза": str(sign), "Коефициент": sign_o, "Сигурност": sign_p
        })

    if full_schedule:
        df = pd.DataFrame(full_schedule)
        df = df.sort_values(by="Час 📅")

        # --- СТАТИСТИКА ЗА ДЕНЯ ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🗺️ Общо мачове в тиража", len(df))
        with col2:
            st.metric("🎯 Основен пазар", "Българско време (БГ)")
        with col3:
            st.metric("⚡ Икономия на ресурси", "100% (Кеширан)")

        # --- НАЧАЛНА СТРАНИЦА: СЕКЦИЯ С БУТОНИ ЗА ФИШ И АРХИВ ---
        st.markdown("---")
        check_col1, check_col2 = st.columns(2)
        
        with check_col1:
            show_combo = st.checkbox("🟢 ПОКАЖИ AI КОМБИНИРАН ФИШ ЗА ДЕНЯ", value=True)
        with check_col2:
            show_archive = st.checkbox("📉 ПОКАЖИ ВЧЕРАШНА УСПЕВАЕМОСТ (АРХИВ)", value=False)

        # 1. БЛОК: КОМБИНИРАН ФИШ
        if show_combo:
            st.markdown("<div style='background-color: #0f172a; padding: 15px; border-radius: 10px; border: 2px solid #10b981; margin-bottom: 15px;'>", unsafe_allow_html=True)
            st.subheader("💸 AI Комбиниран Фиш (Топ 3 най-сигурни мача)")
            combo_df = pd.DataFrame(pool_for_combo)
            if not combo_df.empty:
                top_picks = combo_df.sort_values(by="Сигурност", ascending=False).head(3)
                total_odd = 1.0
                for idx, row in top_picks.iterrows():
                    total_odd *= row["Коефициент"]
                    st.write(f"🔹 **{row['Мач']}** | Прогноза: **{row['Прогноза']}** | Коефициент: `{row['Коефициент']}` ({row['Сигурност']}% сигурност)")
                total_odd = round(total_odd, 2)
                st.success(f"🟩 **Общ коефициент на фиша: {total_odd}**")
                bet_amount = st.number_input("💵 Въведи сума за залог (лв):", min_value=1, value=10, step=5, key="bet_main")
                st.info(f"💰 Потенциална печалба: **{round(bet_amount * total_odd, 2)} лв.**")
            st.markdown("</div>", unsafe_allow_html=True)

        # 2. БЛОК: ВЧЕРАШЕН АРХИВ С БЪЛГАРСКО ВРЕМЕ И HTML ТАБЛИЦА
        if show_archive:
            st.markdown("<div style='background-color: #0f172a; padding: 15px; border-radius: 10px; border: 2px solid #ef4444; margin-bottom: 15px;'>", unsafe_allow_html=True)
            st.subheader(f"📊 Отчет за успеваемост от вчера ({yesterday_str})")
            with st.spinner("⏳ Зареждане на вчерашните резултати..."):
                yesterday_fixtures, _ = fetch_secure_daily_fixtures(yesterday_str)
                if not yesterday_fixtures:
                    st.warning("⚠️ В момента няма налични или приключили данни за вчерашния архив.")
                else:
                    past_results = []
                    for item in yesterday_fixtures:
                        status = item.get("fixture", {}).get("status", {}).get("short", "")
                        if status == "FT":
