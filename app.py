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
            bookmakers = res["response"][0].get("bookmakers", [])
            if bookmakers:
                bets = bookmakers[0].get("bets", [])
                for bet in bets:
                    if bet["id"] == 1:
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
            return res["response"][0]
    except:
        pass
    return None

# Кеширана функция за статистика и форма (Последни 10 мача)
@st.cache_data(ttl=43200)
def get_team_history(team_id, league_id, _headers):
    url = f"https://api-sports.io{team_id}&league={league_id}&season={datetime.now().year}"
    try:
        res = requests.get(url, headers=_headers).json()
        if res.get("response"):
            return res["response"]
    except:
        pass
    return None

if "matches" not in st.session_state:
    st.session_state.matches = None

# Бутон за зареждане на тиража за деня
if st.button("📅 ЗАРЕДИ ДНЕШНИЯ ТИРАЖ ПО ЛИГИ", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://{HOST}/fixtures?date={today}"
    
    with st.spinner("🔄 Зареждане и сортиране на тиража..."):
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if not data.get("response"):
                st.error("❌ Няма налични мачове или грешен API ключ.")
                st.session_state.matches = None
            else:
                # Сортиране по час на започване
                sorted_fixtures = sorted(data["response"], key=lambda x: x['fixture']['date'])
                
                filtered_matches = {}
                for item in sorted_fixtures:
                    if item['fixture']['status']['short'] == "NS":
                        raw_date = item['fixture']['date']
                        # Извличане на часа във формат ЧЧ:ММ
                        match_time = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%H:%M")
                        
                        league_name = item['league']['name']
                        home = item['teams']['home']['name']
                        away = item['teams']['away']['name']
                        
                        # Красив текст за менюто: [18:30] Англия - Висша Лига | Арсенал - Челси
                        key = f"[{match_time}] {item['league']['country']} - {league_name} | {home} - {away}"
                        
                        filtered_matches[key] = {
                            "id": item['fixture']['id'],
                            "home_id": item['teams']['home']['id'],
                            "away_id": item['teams']['away']['id'],
                            "league_id": item['league']['id']
                        }
                
                st.session_state.matches = filtered_matches
                st.toast("✅ Тиражът е зареден и подреден по часове!")
        except Exception as e:
            st.error(f"Грешка при връзката: {e}")

# Главен интерфейс на програмата
if st.session_state.matches:
    st.subheader("🏟️ Изберете мачове за анализ и фиш")
    
    selected_matches = st.multiselect(
        "Маркирайте мачовете за преглед:", 
        options=list(st.session_state.matches.keys())
    )
    
    if selected_matches:
        if st.button("🏆 СТАРТИРАЙ МАСОВ АНАЛИЗ", use_container_width=True):
            ticket_items = []  # За фиша на деня
            
            for match_name in selected_matches:
                match_data = st.session_state.matches[match_name]
                fixture_id = match_data["id"]
                
                with st.spinner(f"📊 Анализиране на {match_name.split('|')[-1]}..."):
                    pred_data = get_ai_prediction(fixture_id, headers)
                    odds_data = get_match_odds(fixture_id, headers)
                    
                    # Изтегляне на история за последните мачове
                    home_stats = get_team_history(match_data["home_id"], match_data["league_id"], headers)
                    away_stats = get_team_history(match_data["away_id"], match_data["league_id"], headers)
                    
                    # Извличане на имената на отборите
                    clean_name = match_name.split(" | ")[-1]
                    home_team, away_team = clean_name.split(" - ")
                    
                    win_home, win_away, win_draw = 33, 33, 34
                    advice = "Няма предоставена препоръка."
                    
                    if pred_data and "predictions" in pred_data:
                        try:
                            win_home = int(str(pred_data["predictions"]["percent"]["home"]).replace("%", ""))
                            win_away = int(str(pred_data["predictions"]["percent"]["away"]).replace("%", ""))
                            win_draw = int(str(pred_data["predictions"]["percent"]["draw"]).replace("%", ""))
                            advice = pred_data["predictions"].get("advice", advice)
                        except:
                            pass
                    
                    # Генериране на визуален панел за мача
                    with st.expander(f"📋 {match_name}", expanded=True):
                        
                        # 📈 Секция Статистика & Форма
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**🏠 {home_team}:**")
                            if home_stats and "form" in home_stats:
                                form_str = " ".join(["✅" if c=="W" else "❌" if c=="L" else "🤝" for c in list(str(home_stats["form"]))[-5:]])
                                st.write(f"Форма (последни 5): {form_str}")
                                st.write(f"Вкарани голове: {home_stats['goals']['for']['total']['home']}")
                            else:
                                st.write("Форма: Няма данни")
                        with col2:
                            st.markdown(f"**🚀 {away_team}:**")
                            if away_stats and "form" in away_stats:
                                form_str = " ".join(["✅" if c=="W" else "❌" if c=="L" else "🤝" for c in list(str(away_stats["form"]))[-5:]])
                                st.write(f"Форма (последни 5): {form_str}")
                                st.write(f"Вкарани голове: {away_stats['goals']['for']['total']['away']}")
                            else:
                                st.write("Форма: Няма данни")
                                
                        # 💰 Секция Коефициенти
                        odds_dict = {}
                        if odds_data:
                            odds_text = " | ".join([f"**{o['value']}:** {o['odd']}" for o in odds_data])
                            st.markdown(f"💰 **Коефициенти (1X2):** {odds_text}")
                            odds_dict = {o['value']: float(o['odd']) for o in odds_data}
                        
                        # 🤖 Извеждане на Консенсус Прогноза
                        st.markdown(f"📊 **Вероятности:** 🏠 {win_home}% | 🤝 {win_draw}% | 🚀 {win_away}%")
                        
                        final_pick = ""
                        final_odd = 1.00
                        
                        if win_home > 60:
                            final_pick = f"1 (Победа за {home_team})"
                            final_odd = odds_dict.get('Home', 1.50)
                            st.success(f"🎯 **AI Консенсус:** {final_pick} (Сигурност: {win_home}%)")
                        elif win_away > 60:
                            final_pick = f"2 (Победа за {away_team})"
                            final_odd = odds_dict.get('Away', 1.50)
                            st.success(f"🎯 **AI Консенсус:** {final_pick} (Сигурност: {win_away}%)")
                        else:
                            st.info(f"🎯 **AI Консенсус:** Равностоен сблъсък. Препоръка: {advice}")
                            if "Home" in advice or "1" in advice:
                                final_pick = "1X (Двоен шанс)"
                                final_odd = 1.30
                            else:
                                final_pick = "Под/Над голове"
                                final_odd = 1.60
                        
                        # Добавяне към списъка за фиш, ако имаме категорична прогноза
                        if final_pick and final_odd > 1.05:
                            ticket_items.append({"match": clean_name, "pick": final_pick, "odd": final_odd})
            
            # 🎫 ГЕНЕРИРАНЕ НА ФИШ НА ДЕНЯ
            if ticket_items:
                st.markdown("---")
                st.subheader("🎫 Генериран Фиш на Деня (Комбо)")
                total_odd = 1.0
                
