import streamlit as st
import requests
from datetime import datetime

# Настройка на страницата
st.set_page_config(page_title="AI Футбол Консенсус", page_icon="⚽", layout="centered")

st.title("🛠️ AI Футбол Консенсус")

# Конфигурация на API Ключ
API_KEY = st.text_input("Вашият API Ключ:", value="5e7733082a7ccd5b3960167e82c94007", type="password")
HOST = "v3.football.api-sports.io"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST
}

# Бутон за зареждане
if st.button("📅 ЗАРЕДИ МАЧОВЕТЕ ЗА ДНЕС", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://{HOST}/fixtures?date={today}"
    
    with st.spinner("🔄 Зареждане на мачовете..."):
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            # Обновяване на лимитите (ако API връща хедъри)
            limit = response.headers.get('x-ratelimit-requests-limit', 100)
            remaining = response.headers.get('x-ratelimit-requests-remaining', 100)
            st.info(f"Заявки днес: {int(limit) - int(remaining)} | Оставащи: {remaining}")

            if not data.get("response"):
                st.error("❌ Няма мачове за днес или грешен API ключ.")
            else:
                st.subheader("🏟️ Изберете мач за анализ")
                
                # Показване на мачовете под формата на бутони/селектор
                fixtures = {f"{item['teams']['home']['name']} - {item['teams']['away']['name']} ({item['league']['name']})": item['fixture']['id'] for item in data["response"]}
                selected_match = st.selectbox("Изберете двубой:", options=list(fixtures.keys()))
                
                if selected_match:
                    fixture_id = fixtures[selected_match]
                    
                    # Бутон за стартиране на анализа за избрания мач
                    if st.button("🏆 АНАЛИЗИРАЙ ИЗБРАНИЯ МАЧ", use_container_width=True):
                        pred_url = f"https://{HOST}/predictions?fixture={fixture_id}"
                        pred_response = requests.get(pred_url, headers=headers)
                        pred_data = pred_response.json()
                        
                        if not pred_data.get("response"):
                            st.warning("⚠️ Няма налични детайлни прогнози за този мач.")
                        else:
                            match_info = pred_data["response"][0]
                            home_team = match_info["teams"]["home"]["name"]
                            away_team = match_info["teams"]["away"]["name"]
                            
                            win_home = int(match_info["predictions"]["percent"]["home"].replace("%", ""))
                            win_away = int(match_info["predictions"]["percent"]["away"].replace("%", ""))
                            advice = match_info["predictions"]["advice"]
                            
                            st.success(f"### 📊 {home_team} - {away_team}")
                            
                            if win_home > 60:
                                st.markdown(f"⚽ **Краен знак:** Победа за {home_team} ({win_home}% сигурност)")
                            elif win_away > 60:
                                st.markdown(f"⚽ **Краен знак:** Победа за {away_team} ({win_away}% сигурност)")
                                
                            if advice:
                                st.markdown(f"🎯 **Голове & Комбинация:** {advice}")
                                
                            st.markdown("📐 **Очаквани Корнери:** Линия около 8.5/9.5 корнера общо.")
                            st.markdown("⚠️ **Очаквани Картони:** Тенденция за линия под 5.5 картона.")
        except Exception as e:
            st.error(f"Грешка при връзката: {e}")
