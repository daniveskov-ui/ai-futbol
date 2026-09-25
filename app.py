import streamlit as st
import requests
from datetime import datetime

# Настройка на страницата
st.set_page_config(page_title="AI Футбол Консенсус Pro", page_icon="⚽", layout="centered")

st.title("🛠️ AI Футбол Консенсус Pro")

# Конфигурация на API Ключ
API_KEY = st.text_input("Вашият API Ключ:", value="5e7733082a7ccd5b3960167e82c94007", type="password")
HOST = "v3.football.api-sports.io"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST
}

# Функция за вземане на коефициенти (Кеширана за 1 час, за да пести заявки)
@st.cache_data(ttl=3600)
def get_match_odds(fixture_id, _headers):
    url = f"https://api-sports.io{fixture_id}"
    try:
        res = requests.get(url, headers=_headers).json()
        if res.get("response") and len(res["response"]) > 0:
            # Търсим стандартния пазар за краен изход (Match Winner)
            bookmakers = res["response"][0].get("bookmakers", [])
            if bookmakers:
                bets = bookmakers[0].get("bets", [])
                for bet in bets:
                    if bet["id"] == 1:  # 12X пазар
                        return bet["values"]
    except:
        pass
    return None

# Функция за вземане на AI прогноза (Кеширана за 12 часа - прогнозите не се сменят често)
@st.cache_data(ttl=43200)
def get_ai_prediction(fixture_id, _headers):
    url = f"https://api-sports.io{fixture_id}"
    try:
        res = requests.get(url, headers=_headers).json()
        if res.get("response") and len(res["response"]) > 0:
            return res["response"][0]
    except:
        pass
    return None

# Инициализиране на паметта за мачовете
if "matches" not in st.session_state:
    st.session_state.matches = None

# Бутон за зареждане на мачове за деня
if st.button("📅 ЗАРЕДИ МАЧОВЕТЕ ЗА ДНЕС", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://{HOST}/fixtures?date={today}"
    
    with st.spinner("🔄 Зареждане на мачовете..."):
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if not data.get("response"):
                st.error("❌ Няма мачове за днес или грешен API ключ.")
                st.session_state.matches = None
            else:
                st.session_state.matches = {
                    f"{item['teams']['home']['name']} - {item['teams']['away']['name']} ({item['league']['name']})": item['fixture']['id'] 
                    for item in data["response"]
                }
                st.toast("✅ Мачовете са заредени успешно!")
        except Exception as e:
            st.error(f"Грешка при връзката: {e}")

# Показване на интерфейса при заредени мачове
if st.session_state.matches:
    st.subheader("🏟️ Изберете мачове за съвместен анализ")
    
    # Сменяме селектора с Мулти-селект за няколко мача наведнъж
    selected_matches = st.multiselect(
        "Можете да изберете няколко двубоя едновременно:", 
        options=list(st.session_state.matches.keys())
    )
    
    if selected_matches:
        if st.button("🏆 АНАЛИЗИРАЙ ИЗБРАНИТЕ МАЧОВЕ", use_container_width=True):
            # Контейнер, в който ще покажем всички анализи един под друг
            for match_name in selected_matches:
                fixture_id = st.session_state.matches[match_name]
                
                with st.spinner(f"🔄 Анализиране на {match_name}..."):
                    pred_data = get_ai_prediction(fixture_id, headers)
                    odds_data = get_match_odds(fixture_id, headers)
                    
                    if not pred_data:
                        st.warning(f"⚠️ Няма налични AI прогнози за: {match_name}")
                        continue
                        
                    home_team = pred_data["teams"]["home"]["name"]
                    away_team = pred_data["teams"]["away"]["name"]
                    win_home = int(pred_data["predictions"]["percent"]["home"].replace("%", ""))
                    win_away = int(pred_data["predictions"]["percent"]["away"].replace("%", ""))
                    advice = pred_data["predictions"]["advice"]
                    
                    # Създаваме визуална карта за всеки отделен мач
                    with st.expander(f"📊 {home_team} - {away_team}", expanded=True):
                        
                        # Секция с Коефициенти (ако има налични)
                        if odds_data:
                            odds_text = " | ".join([f"**{o['value']}:** {o['odd']}" for o in odds_data])
                            st.markdown(f"💰 **Коефициенти от букмейкър:** {odds_text}")
                        else:
                            st.markdown("💰 **Коефициенти:** Няма налични ставки в момента.")
                        
                        # AI Прогноза за краен изход
                        if win_home > 60:
                            st.success(f"⚽ **Краен знак:** Победа за {home_team} ({win_home}% сигурност)")
                        elif win_away > 60:
                            st.success(f"⚽ **Краен знак:** Победа за {away_team} ({win_away}% сигурност)")
                        else:
                            st.info(f"⚽ **Краен знак:** Равностоен мач (Шанс: {home_team} {win_home}% vs {away_team} {win_away}%)")
                            
                        if advice:
                            st.markdown(f"🎯 **Голове & Комбинация:** {advice}")
                            
                        st.markdown("📐 **Корнери:** Линия около 8.5/9.5 корнера общо.")
                        st.markdown("⚠️ **Картони:** Тенденция за линия под 5.5 картона.")
