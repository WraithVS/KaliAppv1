import streamlit as st
import sqlite3
import bcrypt
from datetime import date
import json
import time

# =========================
# PAGE CONFIG (PWA STYLE)
# =========================
st.set_page_config(
    page_title="Calisthenics AI Coach",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# MODERN UI STYLE
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1220, #0f172a);
    color: white;
}

section[data-testid="stSidebar"] {
    background: #0a0f1c;
}

/* Buttons */
.stButton>button {
    width: 100%;
    background: linear-gradient(90deg, #6366f1, #22c55e);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px;
    font-weight: 600;
}

/* Inputs */
input, textarea {
    border-radius: 10px !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,0.1);
}

/* Cards */
.card {
    padding: 15px;
    margin: 10px 0;
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
}

/* Titles */
h1, h2, h3 {
    color: white;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DB
# =========================
conn = sqlite3.connect("calisthenics_ui.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY,
        user TEXT,
        date TEXT,
        plan TEXT,
        day_type TEXT,
        done TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY,
        user TEXT,
        exercise TEXT,
        value INTEGER,
        date TEXT
    )
    """)
    conn.commit()

init_db()

# =========================
# AUTH
# =========================
def register_user(u, p):
    hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users VALUES (NULL,?,?)", (u, hashed))
        conn.commit()
        return True
    except:
        return False


def login_user(u, p):
    c.execute("SELECT password FROM users WHERE username=?", (u,))
    data = c.fetchone()
    return data and bcrypt.checkpw(p.encode(), data[0])

# =========================
# PLAN
# =========================
PLAN = {
    "Planche + Muscle-up PRO": {
        "A - Planche": [
            "Planche lean",
            "Pseudo planche push-ups",
            "Dips",
            "Pike push-ups",
            "Hollow body",
            "Leg raises"
        ],
        "B - Muscle-up": [
            "Pull-ups",
            "Explosive pull-ups",
            "Chest-to-bar",
            "Australian pull-ups",
            "Dips",
            "Core hollow"
        ],
        "C - Skill Mix": [
            "Tuck planche",
            "Planche lean heavy",
            "Muscle-up transition",
            "Explosive pull-ups",
            "Pseudo planche push-ups",
            "Core finisher"
        ]
    }
}

# =========================
# SESSION
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

# =========================
# LOGIN
# =========================
if st.session_state.user is None:
    st.title("🏋️ Calisthenics AI Coach")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Login")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if login_user(u, p):
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Błędne dane")

    with tab2:
        u2 = st.text_input("New user")
        p2 = st.text_input("New password", type="password")

        if st.button("Create account"):
            if register_user(u2, p2):
                st.success("OK")
            else:
                st.error("User exists")

    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.title(f"👤 {st.session_state.user}")

menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Trening",
    "Kalendarz",
    "Progres",
    "AI Coach",
    "Timer"
])

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Dashboard")

    c.execute("SELECT COUNT(*) FROM workouts WHERE user=?", (st.session_state.user,))
    workouts = c.fetchone()[0]

    c.execute("SELECT date, plan FROM workouts WHERE user=? ORDER BY id DESC LIMIT 1",
              (st.session_state.user,))
    last = c.fetchone()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("🏋️ Treningi", workouts)

    with col2:
        st.metric("📅 Ostatni", last[0] if last else "Brak")

    st.markdown("<div class='card'>🔥 Trenuj konsekwentnie — planche i muscle-up to gra cierpliwości.</div>", unsafe_allow_html=True)

# =========================
# TRAINING
# =========================
elif menu == "Trening":
    st.title("🏋️ Trening PRO")

    plan_name = list(PLAN.keys())[0]
    plan = PLAN[plan_name]

    day = st.selectbox("Wybierz dzień", list(plan.keys()))
    exercises = plan[day]

    today = str(date.today())
    done = []

    st.write(f"📅 {today}")
    st.subheader(day)

    for ex in exercises:
        col1, col2 = st.columns([6, 1])

        with col1:
            st.markdown(f"💪 {ex}")

        with col2:
            if st.checkbox("", key=ex):
                done.append(ex)

    if st.button("Zapisz trening"):
        c.execute(
            "INSERT INTO workouts VALUES (NULL,?,?,?,?,?)",
            (st.session_state.user, today, plan_name, day, json.dumps(done))
        )
        conn.commit()
        st.success("Zapisano!")

# =========================
# HISTORY
# =========================
elif menu == "Kalendarz":
    st.title("📅 Historia")

    c.execute(
        "SELECT date, plan, day_type, done FROM workouts WHERE user=? ORDER BY id DESC",
        (st.session_state.user,)
    )

    rows = c.fetchall()

    if not rows:
        st.info("Brak treningów")
    else:
        for r in rows:
            st.markdown(f"""
            <div class='card'>
                📅 <b>{r[0]}</b><br>
                🏋️ {r[1]}<br>
                🧠 {r[2]}<br>
                ✔ {len(json.loads(r[3]))} ćwiczeń
            </div>
            """, unsafe_allow_html=True)

# =========================
# PROGRESS
# =========================
elif menu == "Progres":
    st.title("📈 Progres")

    ex = st.text_input("Ćwiczenie")
    val = st.number_input("Wynik", 1, 1000)

    if st.button("Zapisz"):
        c.execute(
            "INSERT INTO progress VALUES (NULL,?,?,?,?)",
            (st.session_state.user, ex, val, str(date.today()))
        )
        conn.commit()
        st.success("OK")

    c.execute(
        "SELECT exercise, value FROM progress WHERE user=?",
        (st.session_state.user,)
    )

    data = c.fetchall()

    for d in data:
        st.markdown(f"""
        <div class='card'>
            💪 <b>{d[0]}</b> → {d[1]}
        </div>
        """, unsafe_allow_html=True)

# =========================
# AI COACH
# =========================
def ai_coach(user):
    c.execute("SELECT COUNT(*) FROM workouts WHERE user=?", (user,))
    w = c.fetchone()[0]

    c.execute("SELECT done FROM workouts WHERE user=?", (user,))
    rows = c.fetchall()

    ex = sum(len(json.loads(r[0])) for r in rows)

    score = w * 5 + ex

    if score > 120:
        return score, "🔥 Idziesz mocno — zwiększ trudność (planche + MU)"
    elif score > 60:
        return score, "⚖️ Stabilny progres — utrzymaj poziom"
    return score, "🧱 Buduj bazę — technika > ego"

# =========================
# AI UI
# =========================
if menu == "AI Coach":
    st.title("🧠 AI Coach")

    score, msg = ai_coach(st.session_state.user)

    st.metric("Form Score", score)

    st.markdown(f"""
    <div class='card'>
        🤖 {msg}
    </div>
    """, unsafe_allow_html=True)

# =========================
# TIMER
# =========================
elif menu == "Timer":
    st.title("⏱ Timer")

    mins = st.slider("Minuty", 1, 10, 2)

    if st.button("Start"):
        sec = mins * 60

        placeholder = st.empty()

        for i in range(sec, 0, -1):
            placeholder.markdown(f"<h1 style='text-align:center'>{i}</h1>", unsafe_allow_html=True)
            time.sleep(1)