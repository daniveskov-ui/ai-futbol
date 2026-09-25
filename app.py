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

# Кеширана функция за вземане на коефициенти
@st.cache_data(ttl=3600)
def get_match_odds(fixture_id, _headers):
    url = f"https://api-sports.io{fixture_id}"
    try:
        res = requests.get(url, headers=_headers).json()
        if res.get("response") and len(res["response"]) > 0:
            bookmakers = res["response"].get("bookmakers", [])
            if bookmakers:
                bets = bookmakers.get("bets", [])
                for bet in bets:
                    if bet["id"] == 1: # Пазар 1X2
                        return bet["values"]
    except:
        pass
    return None

# Кеширана функция за вземане на AI прогноза
@st.cache_data(ttl=43200)
def get_ai_prediction(fixture_id, _headers):
    url = f"https://api-sports.io{fixture_id}"
    try:
        res = requests.get(url, headers=_headers).json()
        if res.get("response") and len(res["response"]) > 0:
            return res["response"]
    except:
        pass
    return None

# Функция: Взема последните 10 мача като хронология
@st.cache_data(ttl=43200)
def get_team_last_10_fixtures(team_id, _headers):
    url = f"https://api-sports.io{team_id}&last=10"
    try:
        res = requests.get(url, headers=_headers).json()
        if res.get("response") and len(res["response"]) > 0:
            results = []
            total_goals = 0
            btts_count = 0
            for match in res["response"]:
                home_id = match["teams"]["home"]["id"]
                goals_home = match["goals"]["home"]
                goals_away = match["goals"]["away"]
                
                if goals_home is None or goals_away is None:
                    continue
                
                total_goals += (goals_home + goals_away)
                if goals_home > 0 and goals_away > 0:
                    btts_count += 1
                
                if home_id == team_id:
                    if goals_home > goals_away: results.append("✅")
                    elif goals_home == goals_away: results.append("🤝")
                    else: results.append("❌")
                else:
                    if goals_away > goals_home: results.append("✅")
                    elif goals_home == goals_away: results.append("🤝")
                    else: results.append("❌")
            
            avg_goals = total_goals / len(results) if results else 0
            btts_rate = (btts_count / len(results)) * 100 if results else 0
            return {"form": results[:5], "win_rate": results.count("✅") * 10, "avg_goals": avg_goals, "btts_rate": btts_rate}
    except:
        pass
    return {"form": ["Няма данни"], "win_rate": 0, "avg_goals": 0, "btts_rate": 0}

if "matches" not in st.session_state:
    st.session_state.matches = None
if "filter_mode" not in st.session_state:
    st.session_state.filter_mode = "Всички"

# ДВА БУТОНА ЗА ЗАРЕЖДАНЕ
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("📅 ЗАРЕДИ ДНЕШНИЯ ТИРАЖ", use_container_width=True):
        st.session_state.filter_mode = "Всички"
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://{HOST}/fixtures?date={today}"
        
        with st.spinner("🔄 Зареждане на тиража..."):
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                if data.get("response"):
                    sorted_fixtures = sorted(data["response"], key=lambda x: x['fixture']['date'])
                    filtered = {}
                    for item in sorted_fixtures:
                        if item['fixture']['status']['short'] == "NS":
                            raw_date = item['fixture']['date']
                            match_time = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%H:%M")
                            key = f"[{match_time}] {item['league']['country']} - {item['league']['name']} | {item['teams']['home']['name']} - {item['teams']['away']['name']}"
                            filtered[key] = {"id": item['fixture']['id'], "home_id": item['teams']['home']['id'], "away_id": item['teams']['away']['id']}
                    st.session_state.matches = filtered
                    st.toast("✅ Всички предстоящи мачове са заредени!")
            except:
                st.error("Грешка при връзката.")

with col_btn2:
    if st.button("🔥 ФИЛТРИРАЙ САМО НАД 60% ШАНС", use_container_width=True):
        st.session_state.filter_mode = "Топ"
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://{HOST}/fixtures?date={today}"
        
        with st.spinner("🔍 Сканиране на тиража за мачове с висока сигурност (Прогнози/Голове)..."):
            try:
                response = requests.get(url, headers=headers)
                data = response.json()
                if data.get("response"):
                    sorted_fixtures = sorted(data["response"], key=lambda x: x['fixture']['date'])
                    high_sure_matches = {}
                    
                    for item in sorted_fixtures[:40]:
                        if item['fixture']['status']['short'] == "NS":
                            f_id = item['fixture']['id']
                            pred = get_ai_prediction(f_id, headers)
                            
                            if pred and "predictions" in pred:
                                try:
                                    win_home = int(str(pred["predictions"]["percent"]["home"]).replace("%", ""))
                                    win_away = int(str(pred["predictions"]["percent"]["away"]).replace("%", ""))
                                    
                                    # Проверка на пазара за Гол/Гол вероятност (ако съществува в отговора)
                                    btts_pct = 0
                                    if "btts" in pred["predictions"] and pred["predictions"]["btts"]:
                                        btts_pct = int(str(pred["predictions"]["btts"]).replace("%", ""))
                                    
                                    # Включваме мача, ако има 1X2 сигурност или сигурност за голове/BTTS над 60%
                                    if win_home >= 60 or win_away >= 60 or btts_pct >= 60:
                                        raw_date = item['fixture']['date']
                                        match_time = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%H:%M")
                                        max_pct = max(win_home, win_away, btts_pct)
                                        
                                        type_tag = "⚽ Знак" if max_pct in [win_home, win_away] else "🎯 Голове"
                                        key = f"🔥 [{match_time}] {type_tag}: {max_pct}% | {item['teams']['home']['name']} - {item['teams']['away']['name']}"
                                        high_sure_matches[key] = {"id": f_id, "home_id": item['teams']['home']['id'], "away_id": item['teams']['away']['id']}
                                except:
                                    pass
                    
                    if high_sure_matches:
                        st.session_state.matches = high_sure_matches
                        st.toast(f"✅ Намерени са {len(high_sure_matches)} топ мача!")
                    else:
                        st.warning("⚠️ Няма открити събития над 60% в извадката.")
                        st.session_state.matches = None
            except:
                st.error("Грешка при сканирането.")

# Основен интерфейс
if st.session_state.matches:
    st.subheader("🏟️ Изберете мачове за съвместен анализ" if st.session_state.filter_mode == "Всички" else "🎯 Изберете от филтрираните топ мачове")
    
    selected_matches = st.multiselect(
        "Маркирайте мачовете за преглед:", 
        options=list(st.session_state.matches.keys())
    )
    
    if selected_matches:
        if st.button("🏆 СТАРТИРАЙ МАСОВ АНАЛИЗ", use_container_width=True):
            ticket_items = []
            
            for match_name in selected_matches:
                match_data = st.session_state.matches[match_name]
                fixture_id = match_data["id"]
                
                with st.spinner(f"📊 Анализиране..."):
                    pred_data = get_ai_prediction(fixture_id, headers)
                    odds_data = get_match_odds(fixture_id, headers)
                    home_stats = get_team_last_10_fixtures(match_data["home_id"], headers)
                    away_stats = get_team_last_10_fixtures(match_data["away_id"], headers)
                    
                    clean_name = match_name.split(" | ")[-1] if "|" in match_name else match_name
                    if " - " in clean_name:
                        home_team, away_team = clean_name.split(" - ")
                    else:
                        home_team, away_team = "Домакин", "Гост"
                    
                    win_home, win_away, win_draw = 33, 33, 34
                    btts_chance = 50
                    advice = ""
                    
                    if pred_data and "predictions" in pred_data:
                        try:
                            win_home = int(str(pred_data["predictions"]["percent"]["home"]).replace("%", ""))
                            win_away = int(str(pred_data["predictions"]["percent"]["away"]).replace("%", ""))
