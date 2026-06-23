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
# PREMIUM DARK UI
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1220, #0f172a);
    color: white;
}

/* sidebar */
section[data-testid="stSidebar"] {
    background: #0a0f1c;
}

/* buttons */
.stButton>button {
    width: 100%;
    background: linear-gradient(90deg, #6366f1, #22c55e);
    color: white;
    border-radius: 12px;
    padding: 10px;
    font-weight: 600;
    border: none;
}

/* inputs */
input {
    border-radius: 10px !important;
}

/* cards */
.card {
    padding: 14px;
    margin: 10px 0;
    background: rgba(255,255,255,0.05);
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
}

/* HEADER CARD (BONUS) */
.header-card {
    padding: 12px;
    margin: 10px 0;
    background: linear-gradient(90deg, rgba(99,102,241,0.25), rgba(34,197,94,0.15));
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.15);
}

/* column headers */
.table-header {
    padding: 10px;
    margin-top: 10px;
    margin-bottom: 10px;
    background: rgba(255,255,255,0.06);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    font-size: 14px;
    font-weight: 600;
    color: #cbd5e1;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DB
# =========================
conn = sqlite3.connect("calisthenics.db", check_same_thread=False)
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
    conn.commit()

init_db()

# =========================
# AUTH
# =========================
def register(u, p):
    hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users VALUES (NULL,?,?)", (u, hashed))
        conn.commit()
        return True
    except:
        return False

def login(u, p):
    c.execute("SELECT password FROM users WHERE username=?", (u,))
    data = c.fetchone()
    return data and bcrypt.checkpw(p.encode(), data[0])

# =========================
# TRAINING PLAN
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

    u = st.text_input("Login")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(u, p):
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Błąd logowania")

    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.title(f"👤 {st.session_state.user}")

menu = st.sidebar.radio("Menu", ["Trening"])

# =========================
# TRAINING
# =========================
if menu == "Trening":
    st.title("🏋️ Trening PRO")

    plan_name = list(PLAN.keys())[0]
    day = list(PLAN[plan_name].keys())[0]
    exercises = PLAN[plan_name][day]

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