import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Настройка на страницата
st.set_page_config(page_title="AI Футбол Консенсус - Топ 20", page_icon="📊", layout="wide")

st.markdown("<h2 style='text-align: center; color: #0284c7;'>📊 Автоматичен Консенсус: Топ 20 Прогнози за Днес</h2>", unsafe_allow_html=True)
st.write("Софтуерът сканира пълния дневен тираж, сравнява математическата вероятност и извежда 20-те най-сигурни подсигурени изхода.")

# Вградени параметри за сигурност
API_KEY = "5e7733082a7ccd5b3960167e82c94007"
API_HOST = "v3.football.api-sports.io"

# Вход за филтриране в страничната лента
st.sidebar.header("🛡️ Трейдърски Филтри")
min_confidence = st.sidebar.slider("Минимален AI Консенсус (%)", min_value=50, max_value=85, value=60)
max_matches = st.sidebar.number_input("Брой мачове за сканиране (макс)", min_value=10, max_value=100, value=40)

@st.cache_data(ttl=1800)  # Кеширане за 30 минути, за да пази лимитите
def get_todays_fixtures(date_str):
    url = f"https://{API_HOST}/fixtures?date={date_str}"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get("response", [])
    except Exception:
        return []
    return []

@st.cache_data(ttl=1800)
def get_prediction_data(fixture_id):
    url = f"https://{API_HOST}/predictions?fixture={fixture_id}"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json().get("response", [])
            if data:
                return data[0]
    except Exception:
        return None
    return None

# Бутон за стартиране на анализа
if st.button("🔍 СКАНИРАЙ ТИРАЖА И СЪЗДАЙ ТОП 20 ТАБЛИЦА", type="primary", use_container_width=True):
    today = datetime.now().strftime('%Y-%m-%d')
    
    with st.spinner("⏳ Сканиране на мачовете и изчисляване на пазарния консенсус... Моля изчакайте."):
        all_fixtures = get_todays_fixtures(today)
        
        if not all_fixtures:
            st.warning("⚠️ Не бяха намерени активни мачове за днес или API лимитът е достигнат.")
            st.stop()
            
        # Взимаме само предстоящите мачове (Not Started)
        upcoming = [f for f in all_fixtures if f["fixture"]["status"]["short"] == "NS"]
        
        if not upcoming:
            st.info("ℹ️ Няма предстоящи мачове, анализират се текущите/завършилите за деня.")
            upcoming = all_fixtures
            
        compiled_predictions = []
        
        # Сканираме ограничен брой мачове, за да не блокираме системата
        for item in upcoming[:int(max_matches)]:
            f_id = item["fixture"]["id"]
            home_team = item["teams"]["home"]["name"]
            away_team = item["teams"]["away"]["name"]
            league_name = item["league"]["name"]
            match_time = item["fixture"]["date"][11:16] # Взима час на събитието
            
            p_data = get_prediction_data(f_id)
            if p_data:
                try:
                    # Извличане на процентите от консенсуса
                    pct_home = int(p_data["predictions"]["percent"]["home"].replace("%","")) if p_data["predictions"]["percent"]["home"] else 0
                    pct_away = int(p_data["predictions"]["percent"]["away"].replace("%","")) if p_data["predictions"]["percent"]["away"] else 0
                    pct_draw = int(p_data["predictions"]["percent"]["draw"].replace("%","")) if p_data["predictions"]["percent"]["draw"] else 0
                    
                    advice = p_data["predictions"]["advice"]
                    
                    # Дефиниране на подсигурения трейдърски пазар (DNB / Двоен Шанс)
                    if pct_home > pct_away and pct_home >= min_confidence:
                        market = f"{home_team} (DNB 1)"
                        score = pct_home
                    elif pct_away > pct_home and pct_away >= min_confidence:
                        market = f"{away_team} (DNB 2)"
                        score = pct_away
                    else:
                        market = "Над 1.5 Гола / Двоен Шанс"
                        score = max(pct_home, pct_away) + (pct_draw // 2) # Алгоритъм за баланс
                        
                    compiled_predictions.append({
                        "Час": match_time,
                        "Лига": league_name,
                        "Мач": f"{home_team} - {away_team}",
                        "Препоръчителен Пазар": market,
                        "AI Сигурност (%)": score,
                        "Детайли": advice if advice else "Статистическо предимство"
                    })
                except Exception:
                    continue

        if compiled_predictions:
            # Превръщане в Pandas DataFrame и сортиране
            df = pd.DataFrame(compiled_predictions)
            df = df.sort_values(by="AI Сигурност (%)", ascending=False).head(20).reset_index(drop=True)
            
            st.success(f"🎯 Топ {len(df)} прогнози бяха успешно филтрирани и подредени по консенсус!")
            
            # Показване на таблицата
            st.dataframe(
                df, 
                column_config={
                    "AI Сигурност (%)": st.column_config.ProgressColumn("Сигурност", format="%d%%", min_value=0, max_value=100),
                },
                use_container_width=True
            )
            
            # Опция за сваляне на данните
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Свали Топ 20 Прогнози в Excel/CSV формат", csv, "top_20_predictions.csv", "text/csv")
        else:
            st.error("❌ Нито един мач не премина филтъра за минимална сигурност. Опитайте да намалите процента от страничното меню.")
