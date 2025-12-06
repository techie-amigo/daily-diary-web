import streamlit as st
import json
from datetime import datetime, date
import hashlib
from pathlib import Path
import uuid

# -----------------------------
# File Setup
# -----------------------------
USERS_FILE = Path("users.json")
DIARY_FILE = Path("diary.json")
ALARMS_FILE = Path("alarms.json")

def init_files():
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}")
    if not DIARY_FILE.exists():
        DIARY_FILE.write_text("{}")
    if not ALARMS_FILE.exists():
        ALARMS_FILE.write_text("{}")

init_files()

# -----------------------------
# JSON Helpers
# -----------------------------
def read_json(path):
    try:
        return json.loads(path.read_text())
    except:
        return {}

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2))

# -----------------------------
# Utility Functions
# -----------------------------
def sha256(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def now_hhmm():
    return datetime.now().strftime("%H:%M")

# -----------------------------
# Auth Functions
# -----------------------------
def signup(username, password):
    users = read_json(USERS_FILE)
    if username in users:
        return False, "Username already exists."
    users[username] = sha256(password)
    write_json(USERS_FILE, users)
    return True, "Account created successfully."

def login(username, password):
    users = read_json(USERS_FILE)
    if username not in users:
        return False, "Unknown username."
    if users[username] != sha256(password):
        return False, "Incorrect password."
    return True, "Login successful."

# -----------------------------
# Diary Functions
# -----------------------------
def save_diary(username, date_key, text):
    diary = read_json(DIARY_FILE)
    diary.setdefault(username, {})
    diary[username][date_key] = text
    write_json(DIARY_FILE, diary)

def load_diary(username, date_key):
    diary = read_json(DIARYFILE)
    return diary.get(username, {}).get(date_key, "")

# -----------------------------
# Alarm Functions
# -----------------------------
def add_alarm(username, time_hhmm, label):
    alarms = read_json(ALARMS_FILE)
    alarms.setdefault(username, [])
    alarm = {
        "id": str(uuid.uuid4()),
        "time": time_hhmm,
        "label": label or "Alarm",
        "enabled": True,
    }
    alarms[username].append(alarm)
    write_json(ALARMS_FILE, alarms)

def get_alarms(username):
    alarms = read_json(ALARMS_FILE)
    return alarms.get(username, [])

def disable_alarm(username, alarm_id):
    alarms = read_json(ALARMS_FILE)
    for alarm in alarms.get(username, []):
        if alarm["id"] == alarm_id:
            alarm["enabled"] = False
    write_json(ALARMS_FILE, alarms)

def delete_alarm(username, alarm_id):
    alarms = read_json(ALARMS_FILE)
    alarms[username] = [
        a for a in alarms.get(username, []) if a["id"] != alarm_id
    ]
    write_json(ALARMS_FILE, alarms)


# -----------------------------
# 🟦 Custom CSS (Modern UI)
# -----------------------------
st.markdown("""
<style>

body {
    background: #f0f2f6;
}

/* Fade-in animation */
@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}

.main-card {
    background: rgba(255,255,255,0.7);
    padding: 30px;
    border-radius: 16px;
    backdrop-filter: blur(10px);
    animation: fadeIn 0.8s ease-in-out;
    box-shadow: 0px 4px 18px rgba(0,0,0,0.1);
}

.section-card {
    background: white;
    padding: 22px;
    border-radius: 14px;
    margin-top: 14px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.07);
    animation: fadeIn 0.8s ease;
}

button {
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)

st.title("🌟 Daily Diary")

# -----------------------------
# SESSION CHECK
# -----------------------------
if "username" not in st.session_state:
    st.session_state.username = None

# -----------------------------
# LOGIN / SIGNUP UI
# -----------------------------
if not st.session_state.username:

    st.markdown("<div class='main-card'>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            ok, msg = login(username.strip(), password)
            if ok:
                st.session_state.username = username.strip()
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        st.subheader("Create Account")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        new_pass2 = st.text_input("Confirm Password", type="password")

        if st.button("Sign Up"):
            if new_pass != new_pass2:
                st.error("Passwords do not match.")
            else:
                ok, msg = signup(new_user.strip(), new_pass)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# -----------------------------
# MAIN APPLICATION (Dashboard)
# -----------------------------
username = st.session_state.username

st.markdown("<div class='main-card'>", unsafe_allow_html=True)
st.success(f"Logged in as: {username}")

if st.button("Logout"):
    st.session_state.username = None
    st.rerun()

# DIARY + ALARMS SIDE BY SIDE
left, right = st.columns(2)

# -----------------------------
# DIARY SECTION
# -----------------------------
with left:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    st.header("📝 Diary")
    selected_date = st.date_input("Select Date", date.today())
    date_key = selected_date.isoformat()

    existing = load_diary(username, date_key)
    text = st.text_area("Your entry:", existing, height=200)

    if st.button("Save Entry"):
        save_diary(username, date_key, text)
        st.success("Saved successfully.")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# ALARM SECTION
# -----------------------------
with right:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    st.header("⏰ Alarm")

    alarm_time = st.time_input("Set Alarm Time")
    alarm_label = st.text_input("Alarm Label")

    if st.button("Add Alarm"):
        hhmm = alarm_time.strftime("%H:%M")
        add_alarm(username, hhmm, alarm_label)
        st.success(f"Alarm set for {hhmm}")

    st.subheader("Your Alarms")
    alarms = get_alarms(username)

    for a in alarms:
        st.write(f"• {a['time']} — {a['label']} (Enabled: {a['enabled']})")
        col1, col2 = st.columns([1,1])

        with col1:
            if st.button("Disable", key=f"disable{a['id']}"):
                disable_alarm(username, a["id"])
                st.rerun()

        with col2:
            if st.button("Delete", key=f"delete{a['id']}"):
                delete_alarm(username, a["id"])
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# ALARM CHECKER
# -----------------------------
alarms = get_alarms(username)
current = now_hhmm()

for a in alarms:
    if a["enabled"] and a["time"] == current:
        st.warning(f"Alarm Triggered: {a['label']}")
        st.audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg", autoplay=True)
        disable_alarm(username, a["id"])
        break

st.markdown("</div>", unsafe_allow_html=True)
