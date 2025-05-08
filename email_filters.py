import re
import imaplib
import email
import os
import json
import pandas as pd
from email.header import decode_header
from urllib.parse import urlparse
import time

# File paths
PROCESSED_EMAILS_FILE = "processed_emails.json"
SPAM_EMAILS_FILE = "spam_emails.json"
TRUSTED_LINKS_FILE = 'realistic_trusted_links.csv'
WHITELIST_SENDERS_FILE = 'realistic_whitelisted_senders.csv'

# Delete old JSON files (optional cleanup)
def delete_files():
    for file in [PROCESSED_EMAILS_FILE, SPAM_EMAILS_FILE]:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"Error deleting {file}: {e}")

# Load list from CSV
def load_list(file_path, column_name):
    try:
        if not os.path.exists(file_path):
            print(f"Missing file: {file_path}")
            return []
        data = pd.read_csv(file_path)[column_name].dropna().tolist()
        return [item.strip().lower() for item in data]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

# Load trusted domains and whitelisted senders
TRUSTED_LINKS = load_list(TRUSTED_LINKS_FILE, 'domain')
WHITELIST_SENDERS = [item.split('@')[-1] for item in load_list(WHITELIST_SENDERS_FILE, 'sender')]

# Email content decoding
def decode_email(content):
    if content is None:
        return ""
    decoded_bytes, encoding = decode_header(content)[0]
    if isinstance(decoded_bytes, bytes):
        return decoded_bytes.decode(encoding or 'utf-8', errors="ignore")
    return decoded_bytes

# Extract domain from sender address
def extract_domain(sender):
    match = re.search(r'@([a-zA-Z0-9.-]+)>?', sender)
    return match.group(1).lower() if match else ""

# Check if sender is trusted
def is_whitelisted(sender):
    return extract_domain(sender) in WHITELIST_SENDERS

# Extract all URLs from email body
def extract_links(body):
    url_pattern = r"https?://[^\s<>\"]+"
    return re.findall(url_pattern, body)

# Get domain from URL
def get_base_domain(link):
    try:
        return urlparse(link).netloc.lower()
    except:
        return ""

# Check if any links are suspicious
def contains_suspicious_links(links):
    for link in links:
        domain = get_base_domain(link)
        if domain not in TRUSTED_LINKS:
            print(f"Suspicious link found: {link}")
            return True
    return False

# Email classification logic
def classify_email(body, sender):
    if is_whitelisted(sender):
        return 'Ham'
    links = extract_links(body)
    if links and contains_suspicious_links(links):
        return 'Spam (Suspicious Link)'
    return 'Ham'

# Save data incrementally to JSON
def append_to_file(file_path, data):
    try:
        existing_data = []
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        existing_data.append(data)
        with open(file_path, "w") as f:
            json.dump(existing_data, f, indent=4)
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

# Process emails from Gmail
def process_emails(mail, search_criteria):
    status, messages = mail.search(None, search_criteria)
    if status != "OK":
        print("Failed to search inbox.")
        return

    email_ids = messages[0].split()
    if not email_ids:
        print("No emails found.")
        return

    for email_id in email_ids:
        _, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_email(msg.get("Subject"))
                sender = decode_email(msg.get("From"))
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                result = classify_email(body, sender)
                print(f"{result}: {subject} from {sender}")

                email_data = {"subject": subject, "sender": sender, "status": result}
                if result.startswith("Spam"):
                    append_to_file(SPAM_EMAILS_FILE, email_data)
                else:
                    append_to_file(PROCESSED_EMAILS_FILE, email_data)

# Gmail login and email processing
def move_to_spam():
    username = "33356@students.riphah.edu.pk"  # Replace with your Gmail
    password = "ribs zrev wjuw taox"     # Use Gmail App Password
    imap_server = "imap.gmail.com"

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        print("Logged in successfully.")

        mail.select("inbox")
        print("Checking Primary tab...")
        process_emails(mail, 'X-GM-RAW "category:primary"')

        print("Checking all emails...")
        process_emails(mail, "ALL")

        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Login or processing error: {e}")

# Main script loop
if __name__ == "__main__":
    while True:
        try:
            move_to_spam()
            print("Scan complete.")
        except Exception as e:
            print(f"Runtime error: {e}")
        finally:
            delete_files()  # Optional: clean up after each run
        time.sleep(300)  # Wait a minutes before next check
