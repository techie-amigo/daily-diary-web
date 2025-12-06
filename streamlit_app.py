# streamlit_app.py
# Full-feature Daily Diary: calendar, date-linked notes, favorites, tags, search, alarms, dark mode
import streamlit as st
import json
from datetime import date, datetime, timedelta
from pathlib import Path
import hashlib
import uuid
import calendar as pycalendar

# -------------------------
# Files & init
# -------------------------
USERS_FILE = Path("users.json")
NOTES_FILE = Path("notes.json")
ALARMS_FILE = Path("alarms.json")

def ensure_file(p: Path):
    if not p.exists():
        p.write_text("{}")

ensure_file(USERS_FILE)
ensure_file(NOTES_FILE)
ensure_file(ALARMS_FILE)

def read_json(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def write_json(p: Path, data):
    p.write_text(json.dumps(data, indent=2))

# -------------------------
# Utilities
# -------------------------
def sha256(s: str):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def iso(d: date):
    return d.isoformat()

def now_iso():
    return datetime.now().isoformat()

def now_hhmm():
    return datetime.now().strftime("%H:%M")

def today():
    return date.today()

# -------------------------
# Auth
# -------------------------
def signup_user(username: str, password: str):
    users = read_json(USERS_FILE)
    if not username or not password:
        return False, "Provide username and password."
    if username in users:
        return False, "Username exists."
    users[username] = sha256(password)
    write_json(USERS_FILE, users)
    return True, "Account created."

def login_user(username: str, password: str):
    users = read_json(USERS_FILE)
    if username not in users:
        return False, "Unknown username."
    if users[username] != sha256(password):
        return False, "Incorrect password."
    return True, "Login successful."

# -------------------------
# Notes & favorites & tags
# Structure:
# notes.json = { username: { "YYYY-MM-DD": { "text": "...", "title":"", "tags":[..], "favorite":bool, "modified":"iso" } } }
# -------------------------
def load_notes(username):
    all_notes = read_json(NOTES_FILE)
    return all_notes.get(username, {})

def save_note(username, date_key, title, text, tags, fav):
    all_notes = read_json(NOTES_FILE)
    user_notes = all_notes.get(username, {})
    entry = {
        "title": title or "",
        "text": text or "",
        "tags": tags or [],
        "favorite": bool(fav),
        "modified": now_iso()
    }
    user_notes[date_key] = entry
    all_notes[username] = user_notes
    write_json(NOTES_FILE, all_notes)

def delete_note(username, date_key):
    all_notes = read_json(NOTES_FILE)
    user_notes = all_notes.get(username, {})
    if date_key in user_notes:
        user_notes.pop(date_key)
    all_notes[username] = user_notes
    write_json(NOTES_FILE, all_notes)

def toggle_favorite(username, date_key):
    all_notes = read_json(NOTES_FILE)
    user_notes = all_notes.get(username, {})
    if date_key in user_notes:
        user_notes[date_key]["favorite"] = not bool(user_notes[date_key].get("favorite", False))
    all_notes[username] = user_notes
    write_json(NOTES_FILE, all_notes)

def list_favorites(username):
    notes = load_notes(username)
    favs = [(d, v) for d, v in notes.items() if v.get("favorite")]
    favs.sort(reverse=True)
    return favs

# -------------------------
# Alarms / Reminders
# alarms.json structure:
# { username: [ {id, date, time, label, enabled, repeat_daily(bool)} ] }
# -------------------------
def load_alarms(username):
    all_alarms = read_json(ALARMS_FILE)
    return all_alarms.get(username, [])

def save_alarm(username, date_key, time_hhmm, label, repeat_daily=False):
    all_alarms = read_json(ALARMS_FILE)
    user_alarms = all_alarms.get(username, [])
    alarm = {
        "id": str(uuid.uuid4()),
        "date": date_key,           # iso date string; if repeat_daily True, date may be "" (ignored)
        "time": time_hhmm,          # "HH:MM"
        "label": label or "Reminder",
        "enabled": True,
        "repeat_daily": bool(repeat_daily),
        "last_fired": None
    }
    user_alarms.append(alarm)
    all_alarms[username] = user_alarms
    write_json(ALARMS_FILE, all_alarms)

def toggle_alarm(username, alarm_id, enabled):
    all_alarms = read_json(ALARMS_FILE)
    user_alarms = all_alarms.get(username, [])
    for a in user_alarms:
        if a["id"] == alarm_id:
            a["enabled"] = bool(enabled)
    all_alarms[username] = user_alarms
    write_json(ALARMS_FILE, all_alarms)

def remove_alarm(username, alarm_id):
    all_alarms = read_json(ALARMS_FILE)
    user_alarms = all_alarms.get(username, [])
    user_alarms = [a for a in user_alarms if a["id"] != alarm_id]
    all_alarms[username] = user_alarms
    write_json(ALARMS_FILE, all_alarms)

def mark_alarm_fired(username, alarm_id):
    all_alarms = read_json(ALARMS_FILE)
    user_alarms = all_alarms.get(username, [])
    for a in user_alarms:
        if a["id"] == alarm_id:
            a["last_fired"] = now_iso()
            if not a.get("repeat_daily"):
                a["enabled"] = False
    all_alarms[username] = user_alarms
    write_json(ALARMS_FILE, all_alarms)

# -------------------------
# UI helpers: calendar grid
# -------------------------
def month_matrix(year, month):
    cal = pycalendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)
    return weeks

# -------------------------
# Inject UI CSS + auto-refresh
# -------------------------
def inject_css(dark_mode=False):
    if dark_mode:
        bg = "#0b1220"
        card = "#0f1724"
        text = "#e6eef8"
        accent = "#6ee7b7"
    else:
        bg = "#f4f7fb"
        card = "#ffffff"
        text = "#0f1724"
        accent = "#3b82f6"
    css = f"""
    <style>
    :root{{--bg:{bg}; --card:{card}; --text:{text}; --accent:{accent};}}
    .app-bg{{background:var(--bg); padding:18px;}}
    .card{{background:var(--card); padding:18px; border-radius:12px; box-shadow:0 6px 20px rgba(2,6,23,0.08); color:var(--text);}}
    .muted{{color:rgba(255,255,255,0.7); font-size:0.9rem;}}
    .btn-small{{padding:6px 10px; border-radius:8px;}}
    .calendar-day{{
        padding:10px; border-radius:8px; text-align:center; cursor:pointer;
    }}
    .today{{border:2px solid var(--accent);}}
    .dot{{height:8px;width:8px;border-radius:50%;display:inline-block;margin-left:6px;background:var(--accent)}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def inject_autorefresh(interval_ms=15000):
    html = f"""
    <script>
    if (!window.__diary_refresh) {{
      window.__diary_refresh = true;
      setInterval(()=>{{ try{{ window.location.reload(); }}catch(e){{}} }}, {interval_ms});
    }}
    </script>
    """
    st.components.v1.html(html, height=0)

# -------------------------
# App start
# -------------------------
st.set_page_config(page_title="Personal Diary", layout="wide")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "username" not in st.session_state:
    st.session_state.username = None
if "selected_date" not in st.session_state:
    st.session_state.selected_date = today()

inject_css(st.session_state.dark_mode)
inject_autorefresh(15000)  # keep alarms active in background while tab is open

# Top bar
col1, col2, col3 = st.columns([2,6,1])
with col1:
    st.markdown("<div class='card'><strong>Personal Diary</strong></div>", unsafe_allow_html=True)
with col2:
    st.markdown("", unsafe_allow_html=True)
with col3:
    if st.button("Toggle Theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.experimental_rerun()

# Authentication
if not st.session_state.username:
    left, right = st.columns(2)
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Sign in")
        login_user_input = st.text_input("Username", key="login")
        login_pass_input = st.text_input("Password", type="password", key="loginpass")
        if st.button("Sign in"):
            ok, msg = login_user(login_user_input.strip(), login_pass_input)
            if ok:
                st.session_state.username = login_user_input.strip()
                st.experimental_rerun()
            else:
                st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Create account")
        su = st.text_input("Choose username", key="su")
        sp = st.text_input("Choose password", type="password", key="sp")
        sp2 = st.text_input("Confirm password", type="password", key="sp2")
        if st.button("Create account"):
            if not su or not sp:
                st.error("Enter username and password.")
            elif sp != sp2:
                st.error("Passwords do not match.")
            else:
                ok, msg = signup_user(su.strip(), sp)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

username = st.session_state.username

# Layout: left calendar, center editor, right favorites & search & alarms
cal_col, editor_col, right_col = st.columns([2, 3, 1.2])

# -------------------------
# LEFT: Calendar
# -------------------------
with cal_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Calendar")

    # month navigation
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = today().year
        st.session_state.cal_month = today().month

    y = st.session_state.cal_year
    m = st.session_state.cal_month

    nav1, nav2, nav3 = st.columns([1,4,1])
    with nav1:
        if st.button("Prev"):
            if m == 1:
                m = 12; y -= 1
            else:
                m -= 1
            st.session_state.cal_year = y; st.session_state.cal_month = m
            st.experimental_rerun()
    with nav2:
        st.markdown(f"**{pycalendar.month_name[m]} {y}**")
    with nav3:
        if st.button("Next"):
            if m == 12:
                m = 1; y += 1
            else:
                m += 1
            st.session_state.cal_year = y; st.session_state.cal_month = m
            st.experimental_rerun()

    weeks = month_matrix(y, m)
    # weekday headings
    header_cols = st.columns(7)
    for i, wd in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
        header_cols[i].markdown(f"**{wd}**")

    # show each week
    for wk in weeks:
        cols = st.columns(7)
        for i, day in enumerate(wk):
            if day == 0:
                cols[i].write("")  # empty cell
            else:
                d = date(y, m, day)
                dkey = iso(d)
                notes = load_notes(username)
                has_note = dkey in notes and notes[dkey].get("text")
                fav = dkey in notes and notes[dkey].get("favorite")
                alarms = [a for a in load_alarms(username) if a.get("date")==dkey and a.get("enabled")]
                css_classes = "calendar-day"
                if d == today():
                    css_classes += " today"
                label = str(day)
                if has_note:
                    label = f"{label} ●"
                if fav:
                    label = f"{label} ★"
                if alarms:
                    label = f"{label} <span class='dot'></span>"
                btn = cols[i].button(label, key=f"day_{dkey}")
                if btn:
                    st.session_state.selected_date = d
                    st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# CENTER: Editor & Search Results
# -------------------------
with editor_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Diary Editor")

    sel = st.session_state.selected_date
    st.markdown(f"**Selected date:** {sel.isoformat()}")

    notes = load_notes(username)
    existing = notes.get(iso(sel), {})
    title = st.text_input("Title", value=existing.get("title",""), key=f"title_{iso(sel)}")
    body = st.text_area("Write your note", value=existing.get("text",""), height=300, key=f"body_{iso(sel)}")
    tags_raw = st.text_input("Tags (comma-separated)", value=",".join(existing.get("tags",[])), key=f"tags_{iso(sel)}")
    fav_state = st.checkbox("Favorite", value=existing.get("favorite", False), key=f"fav_{iso(sel)}")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Save", key=f"save_{iso(sel)}"):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            save_note(username, iso(sel), title, body, tags, fav_state)
            st.success("Saved.")
            st.experimental_rerun()
    with c2:
        if st.button("Delete Note", key=f"del_{iso(sel)}"):
            delete_note(username, iso(sel))
            st.info("Deleted.")
            st.experimental_rerun()
    with c3:
        if st.button("Toggle Favorite", key=f"favbtn_{iso(sel)}"):
            toggle_favorite(username, iso(sel))
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Search notes")
    q = st.text_input("Search by text, tag, or date (YYYY-MM-DD)")
    if st.button("Search"):
        results = []
        notes = load_notes(username)
        for d, v in notes.items():
            if q.lower() in (v.get("text","")+v.get("title","")).lower() or q in d or q.lower() in " ".join(v.get("tags",[])).lower() or (q=="favorite" and v.get("favorite")):
                results.append((d, v))
        if results:
            for d, v in results:
                st.markdown(f"**{d} — {v.get('title','(no title)')}**")
                st.write(v.get("text","")[:400])
                if st.button("Open", key=f"open_{d}"):
                    st.session_state.selected_date = date.fromisoformat(d)
                    st.experimental_rerun()
        else:
            st.write("No results found.")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# RIGHT: Favorites, Alarms add/list
# -------------------------
with right_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Favorites")
    favs = list_favorites(username)
    if favs:
        for d, v in favs[:15]:
            if st.button(f"{d} — {v.get('title','(no title)')}", key=f"favopen_{d}"):
                st.session_state.selected_date = date.fromisoformat(d)
                st.experimental_rerun()
    else:
        st.write("No favorites yet.")

    st.markdown("---")
    st.subheader("Add Reminder / Alarm")
    alarm_date = st.date_input("Date for reminder", value=st.session_state.selected_date, key="alarm_date")
    alarm_time = st.time_input("Time (HH:MM)", key="alarm_time")
    alarm_label = st.text_input("Label", value="", key="alarm_label")
    repeat_daily = st.checkbox("Repeat daily (ignore date)", value=False, key="alarm_repeat")
    if st.button("Set Reminder"):
        dkey = "" if repeat_daily else iso(alarm_date)
        save_alarm(username, dkey, alarm_time.strftime("%H:%M"), alarm_label, repeat_daily)
        st.success("Reminder saved.")
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Scheduled Reminders")
    user_alarms = load_alarms(username)
    if user_alarms:
        for a in user_alarms:
            desc_date = a["date"] if a.get("date") else "(daily)"
            cols = st.columns([3,1,1])
            cols[0].write(f"{desc_date} {a['time']} — {a['label']}")
            if cols[1].button("Toggle", key=f"toggle_{a['id']}"):
                toggle_alarm(username, a["id"], not a.get("enabled", True))
                st.experimental_rerun()
            if cols[2].button("Delete", key=f"del_alarm_{a['id']}"):
                remove_alarm(username, a["id"])
                st.experimental_rerun()
    else:
        st.write("No reminders.")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Alarm checker (fires when tab open; auto-refresh ensures checks)
# -------------------------
def check_and_fire_alarms(username):
    now = datetime.now()
    current_hhmm = now.strftime("%H:%M")
    current_date = iso(now.date())
    user_alarms = load_alarms(username)
    to_fire = []
    for a in user_alarms:
        if not a.get("enabled", True):
            continue
        # match either exact date or repeat_daily
        if a.get("repeat_daily"):
            if a.get("time") == current_hhmm:
                # check last_fired to avoid duplicate in same minute
                last = a.get("last_fired")
                if not last or datetime.fromisoformat(last).strftime("%Y-%m-%dT%H:%M") != now.strftime("%Y-%m-%dT%H:%M"):
                    to_fire.append(a)
        else:
            if a.get("date") == current_date and a.get("time") == current_hhmm:
                last = a.get("last_fired")
                if not last or datetime.fromisoformat(last).strftime("%Y-%m-%dT%H:%M") != now.strftime("%Y-%m-%dT%H:%M"):
                    to_fire.append(a)
    # fire alarms
    if to_fire:
        # mark fired
        for a in to_fire:
            mark_alarm_fired(username, a["id"])
        # show alerts + play sound
        for a in to_fire:
            st.warning(f"Reminder: {a.get('label')} — {a.get('time')}")
        # audio via HTML to attempt autoplay
        sound = "https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg"
        audio_html = f"""
        <audio id="remplayer" src="{sound}" preload="auto"></audio>
        <script>
        try {{
            var p = document.getElementById('remplayer');
            p.play().catch(e => console.log('autoplay prevented', e));
        }} catch(e){{console.log(e)}}
        </script>
        """
        st.components.v1.html(audio_html, height=0)

check_and_fire_alarms(username)

# footer
st.markdown("<div style='padding:12px; text-align:center; color:gray;'>Local demo: data saved on server as JSON. For production use a DB and secure auth.</div>", unsafe_allow_html=True)
