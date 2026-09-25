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
def get_match_odds(fixture_id, _headers):
    url = f"https://api-sports.io{fixture_id}"
    res = requests.get(url, headers=_headers).json()
    response_data = res.get("response", [])
    if response_data and len(response_data) > 0:
        bookmakers = response_data[0].get("bookmakers", [])
        if bookmakers and len(bookmakers) > 0:
            bets = bookmakers[0].get("bets", [])
            for bet in bets:
                if bet.get("id") == 1:
                    return bet.get("values", [])
    return []

# Функция за вземане на AI прогноза
def get_ai_prediction(fixture_id, _headers):
    url = f"https://api-sports.io{fixture_id}"
    res = requests.get(url, headers=_headers).json()
    response_data = res.get("response", [])
    if response_data and len(response_data) > 0:
        return response_data[0]
    return {}

# Функция: Взема последните 10 мача като хронология
def get_team_last_10_fixtures(team_id, _headers):
    url = f"https://api-sports.io{team_id}&last=10"
    res = requests.get(url, headers=_headers).json()
    response_data = res.get("response", [])
    
    results = []
    total_goals = 0
    btts_count = 0
    
    if response_data:
        for match in response_data:
            goals = match.get("goals", {})
            goals_home = goals.get("home")
            goals_away = goals.get("away")
            
            if goals_home is not None and goals_away is not None:
                total_goals += (goals_home + goals_away)
                if goals_home > 0 and goals_away > 0:
                    btts_count += 1
                
                home_id = match.get("teams", {}).get("home", {}).get("id")
                if home_id == team_id:
                    if goals_home > goals_away: results.append("✅")
                    elif goals_home == goals_away: results.append("🤝")
                    else: results.append("❌")
                else:
                    if goals_away > goals_home: results.append("✅")
                    elif goals_home == goals_away: results.append("🤝")
                    else: results.append("❌")
                    
    avg_goals = total_goals / len(results) if len(results) > 0 else 0
    btts_rate = (btts_count / len(results)) * 100 if len(results) > 0 else 0
    return {"form": results[:5], "win_rate": results.count("✅") * 10, "avg_goals": avg_goals, "btts_rate": btts_rate}

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
        
        response = requests.get(url, headers=headers)
        data = response.json()
        response_data = data.get("response", [])
        if response_data:
            sorted_fixtures = sorted(response_data, key=lambda x: x.get('fixture', {}).get('date', ''))
            filtered = {}
            for item in sorted_fixtures:
                fixture_info = item.get('fixture', {})
                status = fixture_info.get('status', {}).get('short', '')
                if status == "NS":
                    raw_date = fixture_info.get('date', '')
                    match_time = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%H:%M")
                    league_info = item.get('league', {})
                    teams_info = item.get('teams', {})
                    key = f"[{match_time}] {league_info.get('country')} - {league_info.get('name')} | {teams_info.get('home', {}).get('name')} - {teams_info.get('away', {}).get('name')}"
                    filtered[key] = {"id": fixture_info.get('id'), "home_id": teams_info.get('home', {}).get('id'), "away_id": teams_info.get('away', {}).get('id')}
            st.session_state.matches = filtered
            st.toast("✅ Всички мачове са заредени!")

with col_btn2:
    if st.button("🔥 ФИЛТРИРАЙ САМО НАД 60% ШАНС", use_container_width=True):
        st.session_state.filter_mode = "Топ"
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://{HOST}/fixtures?date={today}"
        
        response = requests.get(url, headers=headers)
        data = response.json()
        response_data = data.get("response", [])
        if response_data:
            sorted_fixtures = sorted(response_data, key=lambda x: x.get('fixture', {}).get('date', ''))
            high_sure_matches = {}
            
            for item in sorted_fixtures[:30]:
                fixture_info = item.get('fixture', {})
                status = fixture_info.get('status', {}).get('short', '')
                if status == "NS":
                    f_id = fixture_info.get('id')
                    pred = get_ai_prediction(f_id, headers)
                    
                    if pred and "predictions" in pred:
                        predictions_data = pred.get("predictions", {})
                        percent_data = predictions_data.get("percent", {})
                        
                        try:
                            win_home = int(str(percent_data.get("home", "0")).replace("%", ""))
                            win_away = int(str(percent_data.get("away", "0")).replace("%", ""))
                            btts_pct = int(str(predictions_data.get("btts", "0")).replace("%", ""))
                        except:
                            win_home, win_away, btts_pct = 0, 0, 0
                        
                        if win_home >= 60 or win_away >= 60 or btts_pct >= 60:
                            raw_date = fixture_info.get('date', '')
                            match_time = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%H:%M")
                            max_pct = max(win_home, win_away, btts_pct)
                            type_tag = "⚽ Знак" if max_pct in [win_home, win_away] else "🎯 Голове"
                            teams_info = item.get('teams', {})
                            key = f"🔥 [{match_time}] {type_tag}: {max_pct}% | {teams_info.get('home', {}).get('name')} - {teams_info.get('away', {}).get('name')}"
                            high_sure_matches[key] = {"id": f_id, "home_id": teams_info.get('home', {}).get('id'), "away_id": teams_info.get('away', {}).get('id')}
            
            if high_sure_matches:
                st.session_state.matches = high_sure_matches
                st.toast(f"✅ Намерени са {len(high_sure_matches)} топ мача!")
            else:
                st.warning("⚠️ Няма открити силни събития в тази извадка.")

# Основен интерфейс
if st.session_state.matches:
    st.subheader("🏟️ Изберете мачове за анализ и фиш" if st.session_state.filter_mode == "Всички" else "🎯 Топ филтрирани мачове")
    
    selected_matches = st.multiselect("Маркирайте мачовете за преглед:", options=list(st.session_state.matches.keys()))
    
    if selected_matches and st.button("🏆 СТАРТИРАЙ МАСОВ АНАЛИЗ", use_container_width=True):
        ticket_items = []
        
        for match_name in selected_matches:
            match_data = st.session_state.matches[match_name]
            fixture_id = match_data["id"]
            
            pred_data = get_ai_prediction(fixture_id, headers)
            odds_data = get_match_odds(fixture_id, headers)
            home_stats = get_team_last_10_fixtures(match_data["home_id"], headers)
            away_stats = get_team_last_10_fixtures(match_data["away_id"], headers)
            
            clean_name = match_name.split(" | ")[-1] if "|" in match_name else match_name
            home_team, away_team = clean_name.split(" - ") if " - " in clean_name else ("Домакин", "Гост")
            
            win_home, win_away, win_draw, btts_chance = 33, 33, 34, 50
            advice = "Равностоен мач."
            
            if pred_data and "predictions" in pred_data:
                predictions_data = pred_data.get("predictions", {})
                percent_data = predictions_data.get("percent", {})
                try:
                    win_home = int(str(percent_data.get("home", "33")).replace("%", ""))
                    win_away = int(str(percent_data.get("away", "33")).replace("%", ""))
                    win_draw = int(str(percent_data.get("draw", "34")).replace("%", ""))
                    advice = predictions_data.get("advice", "Няма съвет")
                    if predictions_data.get("btts"):
                        btts_chance = int(str(predictions_data.get("btts")).replace("%", ""))
                except:
                    pass
            
            calc_home = int((home_stats["win_rate"] + (100 - away_stats["win_rate"])) / 2)
            calc_away = int((away_stats["win_rate"] + (100 - home_stats["win_rate"])) / 2)
            combined_btts_rate = int((home_stats["btts_rate"] + away_stats["btts_rate"]) / 2)
            combined_goals = (home_stats["avg_goals"] + away_stats["avg_goals"]) / 2
            
            with st.expander(f"📋 {match_name}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🏠 {home_team}:**")
