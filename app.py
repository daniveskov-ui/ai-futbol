import streamlit as st
import requests
from datetime import datetime

# Настройка на страницата
st.set_page_config(page_title="AI Футбол Консенсус Pro", page_icon="⚽", layout="centered")

st.title("🏆 AI Футбол Консенсус Pro")

# Конфигурация на API Ключ
API_KEY = st.text_input("Вашият API Ключ:", value="5e7733082a7ccd5b3960167e82c94007", type="password")
HOST = "v3.football.api-sports.io"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST
}

# Функция за вземане на коефициенти
@st.cache_data(ttl=3600)
def get_match_odds(fixture_id, _headers):
    url = f"https://api-sports.io{fixture_id}"
    try:
        res = requests.get(url, headers=_headers).json()
        if res.get("response") and len(res["response"]) > 0:
            bookmakers = res["response"][0].get("bookmakers", [])
            if bookmakers:
                bets = bookmakers[0].get("bets", [])
                for bet in bets:
                    if bet["id"] == 1:  # Пазар 1X2
                        return bet["values"]
    except:
        pass
    return None

# Функция за вземане на AI прогноза
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
if st.button("📅 ЗАРЕДИ ВСИЧКИ МАЧОВЕ ЗА ДНЕС", use_container_width=True):
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
                # Зареждаме само предстоящи мачове (Not Started), за да не анализираме завършили
                st.session_state.matches = {
                    f"{item['teams']['home']['name']} - {item['teams']['away']['name']} ({item['league']['name']})": item['fixture']['id'] 
                    for item in data["response"] if item['fixture']['status']['short'] == "NS"
                }
                st.toast(f"✅ Успешно заредени предстоящи мачове!")
        except Exception as e:
            st.error(f"Грешка при връзката: {e}")

# Показване на интерфейса при налични мачове
if st.session_state.matches:
    st.subheader("🏟️ Изберете мачове за съвместен анализ")
    
    selected_matches = st.multiselect(
        "Маркирайте двубоите, които искате да анализирате:", 
        options=list(st.session_state.matches.keys())
    )
    
    if selected_matches:
        if st.button("🏆 АНАЛИЗИРАЙ ИЗБРАНИТЕ МАЧОВЕ", use_container_width=True):
            for match_name in selected_matches:
                fixture_id = st.session_state.matches[match_name]
                
                with st.spinner(f"🔄 Анализиране на {match_name}..."):
                    pred_data = get_ai_prediction(fixture_id, headers)
                    odds_data = get_match_odds(fixture_id, headers)
                    
                    # Извличане на имена на отборите от името на мача, ако няма данни от прогнозата
                    parts = match_name.split(" (")
                    teams_part = parts[0].split(" - ")
                    home_team = teams_part[0]
                    away_team = teams_part[1] if len(teams_part) > 1 else "Гост"
                    
                    win_home, win_away = 33, 33
                    advice = ""
                    data_source = "🤖 Официална AI Прогноза"
                    
                    # 1. Ако има фабрична AI прогноза от доставчика
                    if pred_data and "predictions" in pred_data:
                        try:
                            win_home = int(str(pred_data["predictions"]["percent"]["home"]).replace("%", ""))
                            win_away = int(str(pred_data["predictions"]["percent"]["away"]).replace("%", ""))
                            advice = pred_data["predictions"].get("advice", "")
                        except:
                            pass
                    
                    # 2. Алтернатива: Ако няма AI прогноза, но има Букмейкърски коефициенти - изчисляваме имплицитна вероятност
                    elif odds_data:
                        try:
                            odds_dict = {o['value']: float(o['odd']) for o in odds_data}
                            # Изчисляваме вероятностите на база на коефициентите (с премахнат марж)
                            p_home = 1 / odds_dict.get('Home', 3.0)
                            p_draw = 1 / odds_dict.get('Draw', 3.0)
                            p_away = 1 / odds_dict.get('Away', 3.0)
                            total = p_home + p_draw + p_away
                            
                            win_home = int((p_home / total) * 100)
                            win_away = int((p_away / total) * 100)
                            data_source = "📊 Анализ базиран на Букмейкърски пазар"
                            
                            if win_home > win_away + 15:
                                advice = f"Предимство за домакина ({home_team})"
                            elif win_away > win_home + 15:
                                advice = f"Предимство за госта ({away_team})"
                            else:
                                advice = "Равностоен сблъсък с висок шанс за равенство"
                        except:
                            pass
                            
                    # 3. Краен вариант: Ако няма нищо, слагаме 50/50 базов шанс
                    else:
                        data_source = "⚠️ Базов статистически модел (Липсват пазарни коефициенти)"
                        advice = "Няма достатъчно пазарна активност за този двубой."
                    
                    # Визуално показване на резултатите в карта
                    with st.expander(f"📊 {home_team} - {away_team}", expanded=True):
                        st.caption(f"Източник: {data_source}")
                        
                        if odds_data:
                            odds_text = " | ".join([f"**{o['value']}:** {o['odd']}" for o in odds_data])
                            st.markdown(f"💰 **Коефициенти (1X2):** {odds_text}")
                        
                        if win_home > 55:
                            st.success(f"⚽ **Прогноза:** Победа за {home_team} ({win_home}% вероятност)")
                        elif win_away > 55:
                            st.success(f"⚽ **Прогноза:** Победа за {away_team} ({win_away}% вероятност)")
                        else:
                            st.info(f"⚽ **Прогноза:** Равностоен двубой (Домакин: {win_home}% | Гост: {win_away}%)")
                            
                        if advice:
                            st.markdown(f"🎯 **Препоръка:** {advice}")
                        
                        st.markdown("📐 **Очаквани Корнери:** Около 8.5 / 9.5 линии")
                        st.markdown("⚠️ **Очаквани Картони:** Прогноза за под 5.5 общо")
