import streamlit as st
import sqlite3
import bcrypt
from datetime import date
import json
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Calisthenics AI Coach",
    page_icon="🏋️",
    layout="wide"
)

# =========================
# MODERN UI
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

.stButton>button {
    width: 100%;
    background: linear-gradient(90deg, #6366f1, #22c55e);
    color: white;
    border-radius: 10px;
    padding: 10px;
    font-weight: 600;
    border: none;
}

input {
    border-radius: 10px !important;
}

.card {
    padding: 12px;
    margin: 8px 0;
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
}
</style>
""", unsafe_allow_html=True)

# =========================
# DB
# =========================
conn = sqlite3.connect("calisthenics_final.db", check_same_thread=False)
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
        day TEXT,
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
# FULL TRAINING PLAN
# =========================
PLAN = {
    "Planche + Muscle-up PRO": {
        "A - Planche + Push Strength": [
            {"name": "Planche Lean", "sets": 5, "reps": "15–30s", "rest": "90–120s"},
            {"name": "Pseudo Planche Push-ups", "sets": 4, "reps": "6–12", "rest": "90s"},
            {"name": "Dips", "sets": 4, "reps": "5–10", "rest": "120s"},
            {"name": "Pike Push-ups", "sets": 3, "reps": "6–10", "rest": "90s"},
            {"name": "Hollow Body", "sets": 3, "reps": "20–40s", "rest": "60s"},
            {"name": "Leg Raises", "sets": 3, "reps": "8–12", "rest": "60–90s"}
        ],

        "B - Muscle-up (Pull + Explosion)": [
            {"name": "Pull-ups", "sets": 5, "reps": "5–10", "rest": "120s"},
            {"name": "Explosive Pull-ups", "sets": 5, "reps": "3–5", "rest": "120s"},
            {"name": "Chest-to-Bar", "sets": 4, "reps": "3–5", "rest": "120s"},
            {"name": "Australian Pull-ups", "sets": 4, "reps": "8–12", "rest": "90s"},
            {"name": "Dips", "sets": 4, "reps": "5–10", "rest": "120s"},
            {"name": "Hollow Body", "sets": 3, "reps": "30s", "rest": "60s"},
            {"name": "Plank", "sets": 3, "reps": "40–60s", "rest": "60s"}
        ],

        "C - Skill Mix": [
            {"name": "Planche Lean Heavy", "sets": 6, "reps": "15–25s", "rest": "120s"},
            {"name": "Tuck Planche", "sets": 5, "reps": "8–20s", "rest": "120–150s"},
            {"name": "Muscle-up Transition", "sets": 4, "reps": "3–5", "rest": "120s"},
            {"name": "Explosive Pull-ups", "sets": 4, "reps": "3–5", "rest": "120s"},
            {"name": "Pseudo Planche Push-ups", "sets": 3, "reps": "6–10", "rest": "90s"},
            {"name": "Core Finisher", "sets": 3, "reps": "30–40s", "rest": "60s"},
            {"name": "Leg Raises", "sets": 3, "reps": "10", "rest": "60s"}
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
# MENU
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
    w = c.fetchone()[0]

    st.metric("Treningi", w)

    st.markdown("<div class='card'>🔥 Trenuj konsekwentnie — planche + muscle-up = cierpliwość.</div>", unsafe_allow_html=True)

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


    # =========================
    # 🔥 HEADER CARD (BONUS)
    # =========================
    st.markdown("""
    <div class="header-card">
        🔥 <b>Dzień A - Planche + Push Strength</b><br>
        💡 Focus: siła statyczna + push + kontrola ciała
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # TABLE HEADER (FIX + UX)
    # =========================
    st.markdown("""
    <div class="table-header">
    <div style="display:flex; justify-content:space-between;">
        <div style="width:40%;">🏋️ Ćwiczenie</div>
        <div style="width:15%;">📦 Serie</div>
        <div style="width:20%;">🔁 Powt./Czas</div>
        <div style="width:20%;">⏱ Przerwa</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    done = []

    # =========================
    # EXERCISES
    # =========================
    for ex in exercises:

        st.markdown("""
        <div class="card">
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([4, 1, 2, 2])

        with col1:
            st.markdown(f"💪 **{ex['name']}**")

        with col2:
            st.markdown(f"{ex['sets']}x")

        with col3:
            st.markdown(ex['reps'])

        with col4:
            st.markdown(ex['rest'])

        if st.checkbox(f"✔ Done {ex['name']}", key=ex['name']):
            done.append(ex)

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # SAVE
    # =========================
    if st.button("Zapisz trening"):
        c.execute(
            "INSERT INTO workouts VALUES (NULL,?,?,?,?,?)",
            (st.session_state.user, str(date.today()), plan_name, day, json.dumps(done))
        )
        conn.commit()
        st.success("Zapisano!")
# =========================
# HISTORY
# =========================
elif menu == "Kalendarz":
    st.title("📅 Historia")

    c.execute("SELECT date, plan, day, done FROM workouts WHERE user=? ORDER BY id DESC",
              (st.session_state.user,))
    rows = c.fetchall()

    for r in rows:
        st.markdown(f"""
        <div class='card'>
            📅 <b>{r[0]}</b><br>
            🏋️ {r[1]}<br>
            🧠 {r[2]}<br>
            ✔ Ćwiczeń: {len(json.loads(r[3]))}
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

# =========================
# AI COACH
# =========================
elif menu == "AI Coach":
    st.title("🧠 AI Coach")

    c.execute("SELECT COUNT(*) FROM workouts WHERE user=?", (st.session_state.user,))
    w = c.fetchone()[0]

    c.execute("SELECT done FROM workouts WHERE user=?", (st.session_state.user,))
    rows = c.fetchall()

    ex = sum(len(json.loads(r[0])) for r in rows)

    score = w * 5 + ex

    if score > 120:
        msg = "🔥 Idziesz mocno — zwiększ trudność"
    elif score > 60:
        msg = "⚖️ Stabilny progres"
    else:
        msg = "🧱 Buduj bazę"

    st.metric("Form Score", score)
    st.markdown(f"<div class='card'>🤖 {msg}</div>", unsafe_allow_html=True)

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