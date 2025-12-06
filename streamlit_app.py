import streamlit as st
import json
from datetime import date
from pathlib import Path
import calendar as pycal

# -----------------------------
# Storage
# -----------------------------
NOTES_FILE = Path("notes.json")

def ensure_file(p):
    if not p.exists():
        p.write_text("{}")

ensure_file(NOTES_FILE)

def read_notes():
    try:
        return json.loads(NOTES_FILE.read_text())
    except:
        return {}

def write_notes(data):
    NOTES_FILE.write_text(json.dumps(data, indent=2))

# -----------------------------
# Calendar Helper
# -----------------------------
def get_month_matrix(year, month):
    cal = pycal.Calendar(firstweekday=0)
    return cal.monthdayscalendar(year, month)

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="Diary + Calendar", layout="wide")
st.title("📅 Daily Diary — Calendar View")

# -----------------------------
# Session State
# -----------------------------
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

if "cal_year" not in st.session_state:
    st.session_state.cal_year = date.today().year

if "cal_month" not in st.session_state:
    st.session_state.cal_month = date.today().month

# -----------------------------
# Load Notes
# -----------------------------
all_notes = read_notes()

# -----------------------------
# Calendar UI (Left Column)
# -----------------------------
left, right = st.columns([1.4, 2])

with left:
    st.subheader("Calendar")

    year = st.session_state.cal_year
    month = st.session_state.cal_month

    # Navigation
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("← Prev"):
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
            st.session_state.cal_year = year
            st.session_state.cal_month = month
            st.rerun()

    with c2:
        st.write(f"**{pycal.month_name[month]} {year}**")

    with c3:
        if st.button("Next →"):
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
            st.session_state.cal_year = year
            st.session_state.cal_month = month
            st.rerun()

    # Days of week header
    dow = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i in range(7):
        cols[i].write(f"**{dow[i]}**")

    # Month matrix
    matrix = get_month_matrix(year, month)

    for week in matrix:
        cols = st.columns(7)
        for i, daynum in enumerate(week):
            if daynum == 0:
                cols[i].write("")  
            else:
                d = date(year, month, daynum)
                dkey = d.isoformat()

                note_exists = dkey in all_notes

                label = str(daynum)
                if note_exists:
                    label += " ●"

                b = cols[i].button(label, key=f"day_{dkey}")
                if b:
                    st.session_state.selected_date = d
                    st.rerun()

# -----------------------------
# Diary Editor (Right Column)
# -----------------------------
with right:
    st.subheader("Diary Entry")

    selected = st.session_state.selected_date
    st.write(f"### {selected.strftime('%A, %d %B %Y')}")

    dkey = selected.isoformat()
    existing_text = all_notes.get(dkey, "")

    text = st.text_area("Write your entry:", value=existing_text, height=300)

    if st.button("Save Entry"):
        all_notes[dkey] = text
        write_notes(all_notes)
        st.success("Saved!")
