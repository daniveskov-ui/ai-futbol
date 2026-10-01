import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Футбол Трейдър - Успеваемост", page_icon="⚽", layout="wide")

st.markdown("<h2 style='text-align: center; color: #06b6d4;'>⚽ AI Симулатор: Анализ на Днешния Тираж & Вчерашна Успеваемост</h2>", unsafe_allow_html=True)
st.write("Икономичен режим: Използва се само 1 API заявка за днешния тираж и 1 заявка за вчерашния архив.")

API_KEY = "5e7733082a7ccd5b3960167e82c94007"
API_HOST = "v3.football.api-sports.io"

# Дълбоко кеширане за защита на лимита (24 часа)
@st.cache_data(ttl=86400)
def fetch_secure_daily_fixtures(date_str):
    url = f"https://{API_HOST}/fixtures?date={date_str}"
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get("response", []), res.headers
    except:
        return [], {}
    return [], {}

# Помощна функция за локалния AI алгоритъм
def run_local_ai_model(item):
    home = item["teams"]["home"]["name"]
    away = item["teams"]["away"]["name"]
    league = item["league"]["name"]
    
    home_id = item["teams"]["home"]["id"]
    away_id = item["teams"]["away"]["id"]
    
    home_power = 40 + (home_id % 25) + 12
    away_power = 30 + (away_id % 25)
    
    is_cup = any(word in league.lower() for word in ["cup", "trophy", "knockout"])
    if any(word in league.lower() for word in ["league", "championship", "division"]):
        home_power += 5
        
    total_delta = home_power - away_power
    ai_confidence = min(int(50 + (abs(total_delta) * 0.8)), 88)
    
    if is_cup or abs(total_delta) < 6 or "scotland" in league.lower() or "iceland" in league.lower():
        goal_line = "Над 2.5 Гола"
        goal_type = "OVER_25"
    else:
        goal_line = "Под 2.5 Гола"
        goal_type = "UNDER_25"
        
    if total_delta > 15:
        main_market = "1X"
        pred_type = "HOME_WIN_OR_DRAW"
    elif total_delta < -10:
        main_market = "X2"
        pred_type = "AWAY_WIN_OR_DRAW"
    else:
        main_market = "ГГ (Да)"
        pred_type = "GG"
        
    return main_market, goal_line, ai_confidence, pred_type, goal_type

# Инициализиране на датите
today_str = datetime.now().strftime('%Y-%m-%d')
yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

fixtures, meta_headers = fetch_secure_daily_fixtures(today_str)

# Подсигуряване на списъка с държави при празен сутрешен тираж
countries = ["Всички"]
if fixtures:
    countries.extend(sorted(list(set([item["league"]["country"] for item in fixtures if "league" in item]))))
else:
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    tomorrow_fixtures, _ = fetch_secure_daily_fixtures(tomorrow_str)
    if tomorrow_fixtures:
        countries.extend(sorted(list(set([item["league"]["country"] for item in tomorrow_fixtures if "league" in item]))))

# --- СТРАНИЧНА ЛЕНТА ---
st.sidebar.header("🗺️ Филтри и Архив")
selected_country = st.sidebar.selectbox("Изберете държава за днес:", countries)

# Показване на оставащи заявки
if meta_headers:
    rem = meta_headers.get('x-ratelimit-requests-remaining', '100')
    st.sidebar.success(f"📊 Оставащи API заявки: {rem}")

# Бутон за принудително изчистване на кеша
if st.sidebar.button("🔄 ИЗЧИСТИ КЕШ ПАМЕТТА", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.info("Кешът е изчистен! Презаредете страницата.")

# --- СЕКЦИЯ: ПРОВЕРКА НА ВЧЕРАШНИТЕ РЕЗУЛТАТИ ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Проверка на вчерашния ден")
if st.sidebar.button("📉 ЗАРЕДИ ВЧЕРАШНА УСПЕВАЕМОСТ", type="secondary", use_container_width=True):
    st.markdown(f"### 📊 Отчет за успеваемост от вчера ({yesterday_str})")
    
    with st.spinner("⏳ Извличане и проверка на резултатите..."):
        yesterday_fixtures, _ = fetch_secure_daily_fixtures(yesterday_str)
        
        if not yesterday_fixtures:
            st.warning("⚠️ Няма данни за вчерашния ден.")
        else:
            past_results = []
            all_generated_predictions = []
            won_count = 0
            lost_count = 0
            
            for item in yesterday_fixtures:
                status = item["fixture"]["status"]["short"]
                if status == "FT":
                    home = item["teams"]["home"]["name"]
                    away = item["teams"]["away"]["name"]
                    home_goals = item["goals"]["home"]
                    away_goals = item["goals"]["away"]
                    time_str = item["fixture"]["date"][11:16]
                    
                    main_market, goal_line, ai_confidence, pred_type, goal_type = run_local_ai_model(item)
                    
                    is_correct = "❌"
                    if pred_type == "HOME_WIN_OR_DRAW" and home_goals >= away_goals:
                        is_correct = "✅"
                    elif pred_type == "AWAY_WIN_OR_DRAW" and away_goals >= home_goals:
                        is_correct = "✅"
                    elif pred_type == "GG" and home_goals > 0 and away_goals > 0:
                        is_correct = "✅"
                        
                    if is_correct == "✅": won_count += 1
                    else: lost_count += 1
                    
                    match_summary = {
                        "Час": time_str,
                        "Мач": f"{home} - {away}",
                        "Резултат": f"{home_goals}:{away_goals}",
                        "AI Прогноза": main_market,
                        "Голова линия": goal_line,
                        "Ref_Confidence": ai_confidence,
                        "Статус": is_correct
                    }
                    past_results.append(match_summary)
                    all_generated_predictions.append(match_summary)
            
            if past_results:
                col1, col2, col3 = st.columns(3)
                total_checked = won_count + lost_count
                win_rate = round((won_count / total_checked) * 100, 1) if total_checked > 0 else 0
                
                col1.metric("Познати Прогнози", f"{won_count} ✅")
                col2.metric("Сгрешени Прогнози", f"{lost_count} ❌")
                col3.metric("Процент на успеваемост", f"{win_rate}%")
                
                st.markdown("### 🏆 Проверка на вчерашния Топ Акумулатор")
                df_all_pred = pd.DataFrame(all_generated_predictions)
                df_yesterday_top_5 = df_all_pred.sort_values(by="Ref_Confidence", ascending=False).head(5).reset_index(drop=True)
                
                st.dataframe(df_yesterday_top_5[["Час", "Мач", "Резултат", "AI Прогноза", "Голова линия", "Статус"]], use_container_width=True, hide_index=True)
                
                if "❌" in df_yesterday_top_5["Статус"].values:
                    st.error("🚨 Вчерашната Супер Сигурна Колонка ГУБИ поради грешна прогноза.")
                else:
                    st.success("🎉 Вчерашната Супер Сигурна Колонка ПЕЧЕЛИ изцяло!")
                
                st.markdown("### 📋 Пълен отчет на вчерашните прогнози")
                df_past_print = pd.DataFrame(past_results).drop(columns=["Ref_Confidence"])
                st.dataframe(df_past_print.head(30), use_container_width=True, hide_index=True)
            else:
                st.info("Вчерашните мачове още не са актуализирани in базата данни.")

st.markdown("---")

# --- ОСНОВЕН БУТОН ЗА ДНЕШНИЯ ТИРАЖ ---
if st.button("⚡ СКАНИРАЙ ДНЕШНИЯ ТИРАЖ И ИЗЧИСЛИ ЛОКАЛНИЯ КОНСЕНСУС", type="primary", use_container_width=True):
    today_str = datetime.now().strftime('%Y-%m-%d')
    fixtures, meta_headers = fetch_secure_daily_fixtures(today_str)
    
    if not fixtures:
        st.warning("🔄 Сървърът обновява днешния тираж. Превключване към утрешната програма...")
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        fixtures, meta_headers = fetch_secure_daily_fixtures(tomorrow_str)
        
    if not fixtures:
        st.error("⚠️ Няма върнати мачове от спортната база данни.")
        st.stop()
        
    upcoming = [f for f in fixtures if f["fixture"]["status"]["short"] == "NS"]
    if not upcoming: upcoming = fixtures[:30]
    
    if selected_country != "Всички":
        upcoming = [f for f in upcoming if f["league"]["country"] == selected_country]
        
    if not upcoming:
        st.warning(f"⚠️ Няма предстоящи мачове за: {selected_country}")
        st.stop()
        
    block_1, block_2, block_3, block_4 = [], [], [], []
    top_20_list = []
    
    for item in upcoming:
        time_str = item["fixture"]["date"][11:16]
        home = item["teams"]["home"]["name"]
        away = item["teams"]["away"]["name"]
        league = item["league"]["name"]
        
        main_market, goal_line, ai_confidence, _, _ = run_local_ai_model(item)
        
        match_data = {
            "Час": time_str, "Мач": f"{home} - {away}", "Първенство": league,
            "Основен пазар": main_market, "Голова линия": goal_line, "Сигурност": ai_confidence
        }
        
        if "11:30" <= time_str <= "14:30":
            block_1.append(match_data)
        elif "14:31" <= time_str <= "17:30":
            block_2.append(match_data)
        elif "17:31" <= time_str <= "20:30":
            block_3.append(match_data)
        else:
            block_4.append(match_data)
        
        top_20_list.append({
            "Час": time_str, 
            "Мач": f"{home} - {away}", 
            "Лига": league,
            "Tоп Прогноза": main_market, 
            "Линия Голове": goal_line, 
            "AI Сигурност (%)": ai_confidence
        })
        
    st.markdown(f"### 📅 Хронологичен филтър на заредената програма ({selected_country})")
    
    # Секция Блок 1
    if block_1:
        st.write("**⚫ Блок 1: Ранни (11:30 - 14:30)**")
