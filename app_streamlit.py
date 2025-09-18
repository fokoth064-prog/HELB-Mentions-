import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib, ssl
from email.message import EmailMessage

# ---------- CONFIG ----------
# Replace this with your actual Google Sheets CSV export link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ABCxyz1234.../export?format=csv"

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    df['published'] = pd.to_datetime(df['published'], errors='coerce')
    return df

st.set_page_config(layout="wide", page_title="HELB Mentions Dashboard")
st.title("📊 HELB Mentions Dashboard")

df = load_data()

# ---------- FILTERS ----------
st.sidebar.header("Filters")
min_date = df['published'].min().date() if not df['published'].isna().all() else datetime.utcnow().date() - timedelta(days=365)
max_date = df['published'].max().date() if not df['published'].isna().all() else datetime.utcnow().date()
date_range = st.sidebar.date_input("Date range", [min_date, max_date])
sources = st.sidebar.multiselect("Source", options=sorted(df['source'].dropna().unique()), default=None)
tonalities = st.sidebar.multiselect("Tonality", options=["Positive", "Neutral", "Negative"], default=["Positive","Neutral","Negative"])

start, end = date_range
mask = (df['published'].dt.date >= start) & (df['published'].dt.date <= end)
if sources:
    mask &= df['source'].isin(sources)
if tonalities:
    mask &= df['tonality'].isin(tonalities)
filtered = df[mask]

# ---------- METRICS ----------
st.metric("Total Mentions (selected)", len(filtered))

# ---------- CHARTS ----------
if not filtered.empty:
    st.subheader("Mentions Over Time")
    timeseries = filtered.groupby(filtered['published'].dt.date).size()
    st.line_chart(timeseries)

    st.subheader("Source Breakdown")
    st.bar_chart(filtered['source'].value_counts())

    st.subheader("Tonality Breakdown")
    st.bar_chart(filtered['tonality'].value_counts())
else:
    st.warning("No data available for the selected filters.")

# ---------- DATA TABLE ----------
st.subheader("Mentions Table")
st.dataframe(
    filtered[['published','source','tonality','title','summary','link']].sort_values('published', ascending=False),
    height=400
)

# ---------- DOWNLOAD CSV ----------
csv_bytes = filtered.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Filtered CSV", data=csv_bytes, file_name="helb_filtered.csv", mime="text/csv")

# ---------- SHARE BY EMAIL ----------
st.subheader("📧 Share Report by Email")
recips = st.text_input("Recipients (comma-separated)")
sender_email = st.text_input("Sender Email (SMTP user)")  # better: move to st.secrets
smtp_host = st.text_input("SMTP Host (e.g. smtp.gmail.com)")
smtp_port = st.text_input("SMTP Port (e.g. 465)")
smtp_pass = st.text_input("SMTP Password / App Password", type="password")

if st.button("Send Filtered Report"):
    if not (recips and sender_email and smtp_host and smtp_port and smtp_pass):
        st.error("⚠️ Please fill all fields.")
    else:
        msg = EmailMessage()
        msg['Subject'] = f"HELB Report: {start} to {end} ({len(filtered)} mentions)"
        msg['From'] = sender_email
        msg['To'] = [r.strip() for r in recips.split(",")]
        msg.set_content("Attached is the HELB mentions report (CSV).")
        msg.add_attachment(csv_bytes, maintype="text", subtype="csv", filename="helb_filtered.csv")

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, int(smtp_port), context=context) as server:
                server.login(sender_email, smtp_pass)
                server.send_message(msg)
            st.success("✅ Report sent successfully!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
