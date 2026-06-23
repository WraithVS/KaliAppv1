import streamlit as st
import sqlite3
import bcrypt
from datetime import date
import json
import time

# =========================
# PWA / UI CONFIG
# =========================
st.set_page_config(
    page_title="Calisthenics AI Coach",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# DB
# =========================
conn = sqlite3.connect("calisthenics_pwa.db", check_same_thread=False)
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

    if data and bcrypt.checkpw(p.encode(), data[0]):
        return True
    return False

# =========================
# PLAN PRO
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
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "timer" not in st.session_state:
    st.session_state.timer = 0

if "running" not in st.session_state:
    st.session_state.running = False

# =========================
# LOGIN PAGE
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
    "Trening PRO",
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

    st.metric("Treningi", workouts)

    if last:
        st.info(f"Ostatni trening: {last[0]} | {last[1]}")

# =========================
# TRAINING
# =========================
elif menu == "Trening PRO":
    st.title("🏋️ Trening PRO")

    plan_name = list(PLAN.keys())[0]
    plan = PLAN[plan_name]

    day = st.selectbox("Wybierz dzień", list(plan.keys()))
    exercises = plan[day]

    today = str(date.today())
    done = []

    st.write("📅", today)
    st.subheader(day)

    for ex in exercises:
        if st.checkbox(ex):
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
            st.write(f"📅 {r[0]} | {r[1]} | {r[2]} | ✔ {len(json.loads(r[3]))}")

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
        st.write(d[0], "→", d[1])

# =========================
# AI COACH
# =========================
def ai_coach(user):
    c.execute("SELECT COUNT(*) FROM workouts WHERE user=?", (user,))
    workouts = c.fetchone()[0]

    c.execute("SELECT done FROM workouts WHERE user=?", (user,))
    rows = c.fetchall()

    exercises = sum(len(json.loads(r[0])) for r in rows)

    score = workouts * 5 + exercises

    if score > 120:
        return score, "🔥 Idziesz mocno — zwiększ trudność (planche + MU eksplozja)"
    elif score > 60:
        return score, "⚖️ Stabilny progres — utrzymaj poziom"
    else:
        return score, "🧱 Buduj bazę — mniej objętości, więcej techniki"

# =========================
# AI COACH UI
# =========================
if menu == "AI Coach":
    st.title("🧠 AI Coach")

    score, msg = ai_coach(st.session_state.user)

    st.metric("Form Score", score)
    st.info(msg)

# =========================
# TIMER
# =========================
elif menu == "Timer":
    st.title("⏱ Timer odpoczynku")

    mins = st.slider("Minuty", 1, 10, 2)

    if st.button("Start"):
        st.session_state.timer = mins * 60
        st.session_state.running = True

    placeholder = st.empty()

    if st.session_state.running:
        if st.session_state.timer > 0:
            placeholder.write(f"⏳ {st.session_state.timer} sec")
            time.sleep(1)
            st.session_state.timer -= 1
            st.rerun()
        else:
            st.session_state.running = False
            st.success("Czas!")