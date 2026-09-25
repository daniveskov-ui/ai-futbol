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

# Списък с ID-та на лигите, за които API-Sports ВИНАГИ има прогнози
# 39=Висша лига, 140=Ла Лига, 135=Серия А, 78=Бундеслига, 61=Лига 1, 2=Шампионска лига, 3=Лига Европа, 848=Конференции, 172=България Ефбет Лига
ALLOWED_LEAGUE_IDS = [39, 140, 135, 78, 61, 2, 3, 848, 172, 94, 144, 40, 179, 203]

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
            return res["response"][0]  # Поправено: Вземаме първия елемент от списъка!
    except:
        pass
    return None

# Инициализиране на паметта за мачовете
if "matches" not in st.session_state:
    st.session_state.matches = None

# Бутон за зареждане на мачове за деня
if st.button("📅 ЗАРЕДИ ТОП МАЧОВЕТЕ ЗА ДНЕС", use_container_width=True):
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
                filtered_matches = {}
                for item in data["response"]:
                    league_id = item['league']['id']
                    league_name = item['league']['name']
                    status = item['fixture']['status']['short']
                    
                    # Филтрираме строго по големи лиги И мачът да не е започнал/завършил
                    if league_id in ALLOWED_LEAGUE_IDS and status == "NS":
                        key = f"{item['teams']['home']['name']} - {item['teams']['away']['name']} ({league_name})"
                        filtered_matches[key] = item['fixture']['id']
                
                if filtered_matches:
                    st.session_state.matches = filtered_matches
                    st.toast(f"✅ Заредени са {len(filtered_matches)} сериозни мача за анализ!")
                else:
                    st.warning("⚠️ В момента няма предстоящи мачове от топ първенствата. Зареждаме всички свободни за деня...")
                    st.session_state.matches = {
                        f"{item['teams']['home']['name']} - {item['teams']['away']['name']} ({item['league']['name']})": item['fixture']['id'] 
                        for item in data["response"] if item['fixture']['status']['short'] == "NS"
                    }
        except Exception as e:
            st.error(f"Грешка при връзката: {e}")

# Показване на интерфейса
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
                    
                    if not pred_data or "predictions" not in pred_data:
                        st.warning(f"⚠️ Липсват детайлни AI данни за този мач от API доставчика.")
                        continue
                        
                    home_team = pred_data["teams"]["home"]["name"]
                    away_team = pred_data["teams"]["away"]["name"]
                    
                    try:
                        win_home = int(str(pred_data["predictions"]["percent"]["home"]).replace("%", ""))
                        win_away = int(str(pred_data["predictions"]["percent"]["away"]).replace("%", ""))
                    except:
                        win_home, win_away = 33, 33
                        
                    advice = pred_data["predictions"].get("advice", "")
                    
                    # Визуална карта за резултата
                    with st.expander(f"📊 {home_team} - {away_team}", expanded=True):
                        if odds_data:
                            odds_text = " | ".join([f"**{o['value']}:** {o['odd']}" for o in odds_data])
                            st.markdown(f"💰 **Коефициенти (1X2):** {odds_text}")
                        else:
                            st.markdown("💰 **Коефициенти (1X2):** Не са налични в момента.")
                        
                        if win_home > 60:
                            st.success(f"⚽ **AI Прогноза:** Победа за {home_team} ({win_home}% сигурност)")
                        elif win_away > 60:
                            st.success(f"⚽ **AI Прогноза:** Победа за {away_team} ({win_away}% сигурност)")
                        else:
                            st.info(f"⚽ **AI Прогноза:** Равностоен мач (Домакин: {win_home}% | Гост: {win_away}%)")
                            
                        if advice:
                            st.markdown(f"🎯 **Препоръка:** {advice}")
