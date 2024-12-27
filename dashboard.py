import streamlit as st
import json
import time

# Load JSON data
def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return []  # Return empty list if file is not available or has an error

# Paths to JSON files
PROCESSED_EMAILS_FILE = "processed_emails.json"
SPAM_EMAILS_FILE = "spam_emails.json"

# Page Configuration
st.set_page_config(
    page_title="Email Spam Detection Dashboard",
    page_icon="📧",
    layout="wide",
)

# Dashboard Header
st.title("📧 Email Spam Detection Dashboard")

# Two-column Layout
col1, col2 = st.columns(2)

# Add a refresh interval slider in the sidebar
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", min_value=1, max_value=10, value=5)

# Placeholders for dynamic updates
with col1:
    st.header("📨 Processing Emails")
    processed_placeholder = st.empty()  # Placeholder for processed emails

with col2:
    st.header("🚫 Spam Emails")
    spam_placeholder = st.empty()  # Placeholder for spam emails

# Start the dynamic update loop
while True:
    # Load the JSON data
    processed_emails = load_json(PROCESSED_EMAILS_FILE)
    spam_emails = load_json(SPAM_EMAILS_FILE)

    # Update the processed emails section
    with processed_placeholder.container():
        if processed_emails:
            st.markdown("### Latest Processed Emails")
            for email in processed_emails:
                st.markdown(
                    f"**Subject:** {email['subject']} - **Status:** {email['status']} - **Sender:** {email['sender']}"
                )
        else:
            st.write("No processed emails available.")

    # Update the spam emails section
    with spam_placeholder.container():
        if spam_emails:
            st.markdown("### Latest Spam Emails")
            for email in spam_emails:
                st.markdown(
                    f"**Subject:** {email['subject']} - **Status:** {email['status']} - **Sender:** {email['sender']}"
                )
        else:
            st.write("No spam emails detected.")

    # Sleep for the refresh interval before updating
    time.sleep(refresh_interval)
