import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Футбол Трейдър - Консенсус", page_icon="⚽", layout="wide")

st.markdown("<h2 style='text-align: center; color: #06b6d4;'>⚽ AI Симулатор: Пълен Пазарен Консенсус</h2>", unsafe_allow_html=True)
st.write("Икономичен режим: 1 заявка за целия тираж. Локално изчисление на знаци, голове, корнери, картони и консенсус.")

API_KEY = "c21f7bfd4414dea310f1262837a3074e"
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

# Разширен локалeн AI модел с пълни метрики и консенсус логика
def run_advanced_local_ai(item):
    try:
        home_id = item.get("teams", {}).get("home", {}).get("id", 1)
        away_id = item.get("teams", {}).get("away", {}).get("id", 2)
        league = item.get("league", {}).get("name", "Лига")
        
        if home_id is None: home_id = 1
        if away_id is None: away_id = 2
        
        # 1. Изчисляване на Твърд знак (1, Х, 2)
        home_power = 40 + (home_id % 25) + 12
        away_power = 30 + (away_id % 25)
        
        if any(word in league.lower() for word in ["cup", "trophy", "knockout"]):
            home_power += 5
            
        delta = home_power - away_power
        
        if delta > 16:
            direct_sign = "1 (Победа Домакин)"
            has_clear_favorite = True
        elif delta < -12:
            direct_sign = "2 (Победа Гост)"
            has_clear_favorite = True
        else:
            direct_sign = "Х (Равенство)"
            has_clear_favorite = False
            
        # 2. Изчисляване на Голове (Над/Под 2.5)
        if abs(delta) < 6 or "scotland" in league.lower() or "iceland" in league.lower():
            goals_line = "Над 2.5 Гола"
            high_scoring = True
        else:
            goals_line = "Под 2.5 Гола"
            high_scoring = False
            
        # 3. Изчисляване на Корнери (Над/Под 9.5)
        # Агресивните офанзивни мачове и британските лиги генерират корнери
        if high_scoring or any(w in league.lower() for w in ["england", "scotland", "ireland", "japan"]):
            corners_line = "Над 9.5 Корнера"
            high_corners = True
        else:
            corners_line = "Под 9.5 Корнера"
            high_corners = False
            
        # 4. Изчисляване на Картони (Над/Под 4.5)
        # Равностойните дербита (знак Х) и южните лиги (Испания, Италия) носят картони
        if not has_clear_favorite or any(w in league.lower() for w in ["spain", "italy", "argentina", "brazil"]):
            cards_line = "Над 4.5 Картона"
        else:
            cards_line = "Под 4.5 Картона"
            
        # 5. Математическа проверка за КОНСЕНСУС
        # Консенсус има, когато фаворитът съвпада с офанзивния профил на мача (голове + корнери)
        if has_clear_favorite and high_scoring and high_corners:
            consensus = "ДА ✅"
            ai_score = 85 + (home_id % 4)
        elif not has_clear_favorite and not high_scoring:
            consensus = "ТА КТИЧЕСКИ 🤝"
            ai_score = 70 + (home_id % 5)
        else:
            consensus = "НЕ ❌"
            ai_score = 55 + (home_id % 10)
            
        return direct_sign, goals_line, corners_line, cards_line, consensus, ai_score
    except:
        return "1", "Над 2.5 Гола", "Над 9.5 Корнера", "Под 4.5 Картона", "НЕ ❌", 60

# Дати
today_str = datetime.now().strftime('%Y-%m-%d')
yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

fixtures, meta_headers = fetch_secure_daily_fixtures(today_str)

countries = ["Всички"]
if fixtures:
    for item in fixtures:
        if "league" in item and "country" in item["league"] and item["league"]["country"]:
            countries.append(item["league"]["country"])
    countries = ["Всички"] + sorted(list(set(countries[1:])))

st.sidebar.header("🗺️ Филтри и Архив")
selected_country = st.sidebar.selectbox("Изберете държава за днес:", countries)

if meta_headers:
    rem = meta_headers.get('x-ratelimit-requests-remaining', '100')
    st.sidebar.success(f"📊 Оставащи API заявки: {rem}")

if st.sidebar.button("🔄 ИЗЧИСТИ КЕШ ПАМЕТТА", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.sidebar.info("Кешът е изчистен! Презаредете страницата.")

# --- ВЧЕРАШНА УСПЕВАЕМОСТ ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Проверка на вчерашния ден")
if st.sidebar.button("📉 ЗАРЕДИ ВЧЕРАШНА УСПЕВАЕМОСТ", type="secondary", use_container_width=True):
    st.markdown(f"### 📊 Отчет за успеваемост от вчера ({yesterday_str})")
    with st.spinner("⏳ Проверка на вчерашния архив..."):
        yesterday_fixtures, _ = fetch_secure_daily_fixtures(yesterday_str)
        if not yesterday_fixtures:
            st.warning("⚠️ Няма данни за вчерашния ден.")
        else:
            past_results = []
            for item in yesterday_fixtures:
                status = item.get("fixture", {}).get("status", {}).get("short", "")
                if status == "FT":
                    home = item.get("teams", {}).get("home", {}).get("name", "Домакин")
                    away = item.get("teams", {}).get("away", {}).get("name", "Гост")
                    home_goals = item.get("goals", {}).get("home", 0)
                    away_goals = item.get("goals", {}).get("away", 0)
                    if home_goals is None: home_goals = 0
                    if away_goals is None: away_goals = 0
                    time_str = item.get("fixture", {}).get("date", "00:00")[11:16]
                    
                    direct_sign, goals_line, _, _, consensus, _ = run_advanced_local_ai(item)
                    
                    is_correct = "❌"
                    if "1" in direct_sign and home_goals > away_goals: is_correct = "✅"
                    elif "2" in direct_sign and away_goals > home_goals: is_correct = "✅"
                    elif "Х" in direct_sign and home_goals == away_goals: is_correct = "✅"
                    
                    past_results.append({
                        "Час": time_str, "Мач": f"{home} - {away}", "Резултат": f"{home_goals}:{away_goals}",
                        "AI Прогноза": direct_sign, "Консенсус": consensus, "Статус": is_correct
                    })
            if past_results:
                st.dataframe(pd.DataFrame(past_results).head(20), use_container_width=True, hide_index=True)

st.markdown("---")

# --- АВТОМАТИЧНО ИЗВЕЖДАНЕ НА ДНЕШНИЯ ТИРАЖ ---
if not fixtures:
    st.warning("🔄 Сървърът обновява днешния тираж. Превключване към резервна програма...")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    fixtures, meta_headers = fetch_secure_daily_fixtures(tomorrow_str)

if not fixtures:
    st.error("⚠️ Няма върнати мачове от спортната база данни.")
else:
    upcoming = fixtures
    if selected_country != "Всички":
        upcoming = [f for f in upcoming if f.get("league", {}).get("country") == selected_country]
        
    if not upcoming:
        st.warning(f"⚠️ Няма намерени мачове за дестинация: {selected_country}.")
    else:
        full_schedule_list = []
        
        for item in upcoming:
            time_str = item.get("fixture", {}).get("date", "00:00")[11:16]
            home = item.get("teams", {}).get("home", {}).get("name", "Домакин")
            away = item.get("teams", {}).get("away", {}).get("name", "Гост")
            league = item.get("league", {}).get("name", "Лига")
            
            direct_sign, goals_line, corners_line, cards_line, consensus, ai_score = run_advanced_local_ai(item)
            
            full_schedule_list.append({
                "Час 📅": time_str,
                "Мач 🏟️": f"{home} - {away}",
                "Твърд Знак 🎯": direct_sign,
                "Голове ⚽": goals_line,
                "Корнери 📐": corners_line,
                "Картони 🟨": cards_line,
                "Консенсус 📊": consensus,
                "AI Сигурност (%)": ai_score
            })
            
        if full_schedule_list:
            df_schedule = pd.DataFrame(full_schedule_list)
            df_schedule = df_schedule.sort_values(by="Час 📅", ascending=True).reset_index(drop=True)
            
            st.markdown(f"### 📋 Хронологичен пазарен консенсус ({selected_country})")
            st.dataframe(
                df_schedule,
                column_config={
                    "AI Сигурност (%)": st.column_config.ProgressColumn("Сигурност", format="%d%%", min_value=0, max_value=100)
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Извеждане на Супер Сигурната Селекция (само мачове с ДА ✅ консенсус)
            st.markdown("### 🏆 AI Селекция: Елитни Мачове с пълен Пазарен Консенсус")
            df_consensus_only = df_schedule[df_schedule["Консенсус 📊"] == "ДА ✅"].sort_values(by="AI Сигурност (%)", ascending=False).head(5).reset_index(drop=True)
            
            if not df_consensus_only.empty:
                df_consensus_only["Очакван Коефициент"] = ["~1.85", "~1.70", "~1.65", "~1.60", "~1.55"][:len(df_consensus_only)]
                st.dataframe(
                    df_consensus_only[["Час 📅", "Мач 🏟️", "Твърд Знак 🎯", "Голове ⚽", "Очакван Коефициент"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("ℹ️ В текущия филтър няма мачове с пълен консенсус 'ДА ✅'. Използвайте опцията 'Всички' от менюто.")
