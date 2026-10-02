import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Футбол Трейдър - Реален", page_icon="⚽", layout="wide")

st.markdown("<h2 style='text-align: center; color: #06b6d4;'>⚽ Реален AI Анализатор & Автоматичен Топ Фиш</h2>", unsafe_allow_html=True)
st.write("💥 **Икономичен Про Режим:** Използва реални данни за залози от API-Sports с автоматичен фиш за елитните лиги.")

API_KEY = "ca61b57dd810980c1604d630c470309e"
API_HOST = "v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY, "x-rapidapi-host": API_HOST}

# Списък с IDs или Имена на Топ Лигите за филтриране с цел пестене на заявки
TOP_LEAGUES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]

# 1. ЗАЯВКА: Кешира се за 24 часа. Взема графика на мачовете.
@st.cache_data(ttl=86400)
def fetch_daily_fixtures(date_str):
    url = f"https://{API_HOST}/fixtures?date={date_str}"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get("response", [])
        return []
    except:
        return []

# 2. ЗАЯВКА: Сканира избрани мачове за фиша и детайлния преглед. Кешира се за 1 час.
@st.cache_data(ttl=3600)
def fetch_real_ai_prediction(fixture_id):
    url = f"https://{API_HOST}/predictions?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json().get("response", [])
            if data:
                return data[0] if isinstance(data, list) else data
        return None
    except:
        return None

# Българско време форматиране
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
fixtures_list = fetch_daily_fixtures(today_str)

st.sidebar.header("📊 Управление на Лимита")
if st.sidebar.button("🔄 ИЗЧИСТИ КЕШ ПАМЕТТА", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if not fixtures_list:
    st.error("⚠️ Няма достъпни мачове за днес или API лимитът е изчерпан.")
else:
    base_data = []
    top_league_fixtures = []
    mapping = {}
    
    for item in fixtures_list:
        fid = item.get("fixture", {}).get("id")
        time_str = get_clean_bg_time(item.get("fixture", {}).get("date", ""))
        home = item.get("teams", {}).get("home", {}).get("name", "Home")
        away = item.get("teams", {}).get("away", {}).get("name", "Away")
        league = item.get("league", {}).get("name", "League")
        country = item.get("league", {}).get("country", "World")
        
        display_name = f"[{time_str}] {home} - {away} ({league}, {country})"
        match_info = {
            "id": fid, "Час": time_str, "Мач": f"{home} - {away}", 
            "Лига": league, "Държава": country, "Пълен Текст": display_name
        }
        base_data.append(match_info)
        mapping[display_name] = fid
        
        # Заделяме мачовете от Топ лигите за автоматичния фиш
        if league in TOP_LEAGUES:
            top_league_fixtures.append(match_info)

    df = pd.DataFrame(base_data).sort_values(by="Час")

    col1, col2 = st.columns(2)
    with col1: st.metric("🗺️ Налични мачове в тиража", len(df))
    with col2: st.metric("🛡️ Икономичен статус", f"АКТИВЕН ({len(top_league_fixtures)} елитни мача за фиш)")

    # ================= 1. АВТОМАТИЧЕН AI КОМБИНИРАН ФИШ =================
    st.markdown("---")
    show_combo = st.checkbox("🟢 ПОКАЖИ АВТОМАТИЧЕН AI КОМБИНИРАН ФИШ ЗА ДЕНЯ", value=True)
    
    if show_combo:
        st.markdown("<div style='background-color: #0f172a; padding: 20px; border-radius: 10px; border: 2px solid #10b981; margin-bottom: 15px;'>", unsafe_allow_html=True)
        st.subheader("💸 Реален AI Комбиниран Фиш (Елитни Мачове)")
        
        if not top_league_fixtures:
            st.info("ℹ️ Днес няма планирани мачове в Топ 5 европейски първенства. Фишът е празен.")
        else:
            pool_for_combo = []
            # Ограничаваме сканирането до първите 8 топ мача, за да пестим супер много заявки
            with st.spinner(f"⚡ Интелигентно сканиране на елитните мачове за деня (0/{min(8, len(top_league_fixtures))})..."):
                for idx, f_item in enumerate(top_league_fixtures[:8]):
                    pred_res = fetch_real_ai_prediction(f_item["id"])
                    if pred_res and "predictions" in pred_res:
                        preds = pred_res["predictions"]
                        percent = preds.get("percent", {})
                        
                        # Вземаме чистите проценти за Домакин (home) и Гост (away) като стрингове и ги чистим
                        try:
                            p_home = float(str(percent.get("home", "0")).replace("%", ""))
                            p_away = float(str(percent.get("away", "0")).replace("%", ""))
                        except:
                            p_home, p_away = 0.0, 0.0
                            
                        # Избираме по-сигурния знак (1 или 2) и пресмятаме ориентировъчен пазарен коефициент
                        if p_home >= p_away and p_home > 0:
                            best_sign = "1"
                            safety = p_home
                            est_odd = round(95 / p_home, 2) if p_home > 0 else 1.50
                        elif p_away > p_home and p_away > 0:
                            best_sign = "2"
                            safety = p_away
                            est_odd = round(95 / p_away, 2) if p_away > 0 else 1.50
                        else:
                            continue
                        
                        pool_for_combo.append({
                            "Мач": f_item["Мач"],
                            "Лига": f_item["Лига"],
                            "Прогноза": best_sign,
                            "Сигурност": safety,
                            "Коефициент": max(1.20, min(est_odd, 3.50))
                        })
            
            if pool_for_combo:
                combo_df = pd.DataFrame(pool_for_combo)
                # Избираме Топ 3 мача с най-голяма сигурност
                top_picks = combo_df.sort_values(by="Сигурност", ascending=False).head(3)
                
                total_odd = 1.0
                for _, row in top_picks.iterrows():
                    total_odd *= row["Коефициент"]
                    st.write(f"🔹 **{row['Мач']}** ({row['Лига']}) | Прогноза: **{row['Прогноза']}** | Вероятност на алгоритъма: `{int(row['Сигурност'])}%` | Ориент. Коеф: `{row['Коефициент']}`")
                
                total_odd = round(total_odd, 2)
                st.success(f"🟩 **Общ сборен коефициент на фиша: ~ {total_odd}**")
                
                bet_amount = st.number_input("💵 Въведи залог (лв):", min_value=1, value=10, step=5, key="bet_combo")
                st.info(f"💰 Потенциална чиста печалба: **{round((bet_amount * total_odd) - bet_amount, 2)} лв.**")
            else:
                st.warning("Няма достатъчно данни от API-то за съставяне на сигурен фиш в момента.")
                
        st.markdown("</div>", unsafe_allow_html=True)

    # ================= 2. РЪЧНА ТЪРСАЧКА И ДЕТАЙЛЕН АНАЛИЗ =================
    st.markdown("---")
    st.subheader("🔍 Избор и Ръчен Про AI Анализ на Мач")
    st.write("Изберете който и да е мач от днешния световен тираж, за да отключите пълната статистика в реално време.")
    
    search_input = st.text_input("✍️ Пишете име на отбор за бързо филтриране на списъка:", "").strip().lower()
    
    filtered_options = df["Пълен Текст"].tolist()
    if search_input:
        filtered_options = [opt for opt in filtered_options if search_input in opt.lower()]
        
    if not filtered_options:
        st.warning("Няма намерени мачове с това име.")
    else:
        selected_match = st.selectbox("🎯 Изберете мач за анализ:", options=filtered_options)

        if selected_match:
            chosen_id = mapping[selected_match]
            
            with st.spinner("🔄 Зареждане на официални AI данни и H2H показатели..."):
                pred_data = fetch_real_ai_prediction(chosen_id)
                
            if not pred_data or "predictions" not in pred_data:
                st.error("❌ Не бяха открити готови анализи за този мач. Възможно е да е по-нискоразредна лига.")
            else:
                predictions = pred_data.get("predictions", {})
                winner = predictions.get("winner", {}).get("name", "Няма данни")
                advice = predictions.get("advice", "Няма препоръка")
                percent = predictions.get("percent", {})
                comparison = pred_data.get("comparison", {})
                
                st.markdown(f"### 📊 Анализ: {selected_match}")
                
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("🎯 AI Фаворит", winner)
                with c2: st.metric("💡 AI Препоръка за пазар", advice)
                with c3: st.metric("⚖️ Форма (Домакин/Гост)", f"{comparison.get('form', {}).get('home', '0%')} / {comparison.get('form', {}).get('away', '0%')}")
                
                st.markdown("#### 📈 Вероятностно разпределение:")
                p_df = pd.DataFrame([{
                    "Домакин (1)": percent.get("home", "0%"),
                    "Равен (X)": percent.get("draw", "0%"),
                    "Гост (2)": percent.get("away", "0%")
                }])
                st.dataframe(p_df, use_container_width=True, hide_index=True)
                
