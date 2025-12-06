import streamlit as st
import json
from datetime import date
from pathlib import Path

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
# Page Setup
# -----------------------------
st.set_page_config(page_title="Daily Diary", layout="centered")
st.title("Daily Diary — Basic Version")

# -----------------------------
# Select Date
# -----------------------------
chosen_date = st.date_input("Select a date", value=date.today())
dkey = chosen_date.isoformat()

# load saved notes
all_notes = read_notes()
existing_text = all_notes.get(dkey, "")

# -----------------------------
# Text Area for Note
# -----------------------------
text = st.text_area("Write your diary entry:", value=existing_text, height=300)

# -----------------------------
# Save Button
# -----------------------------
if st.button("Save"):
    all_notes[dkey] = text
    write_notes(all_notes)
    st.success("Saved successfully!")

# -----------------------------
# Show current note info
# -----------------------------
st.write("---")
st.subheader("Current Saved Entry")
if existing_text:
    st.write(existing_text)
else:
    st.write("No entry saved for this date yet.")

