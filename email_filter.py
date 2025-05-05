import re
import imaplib
import email
import os
import json  # Added for writing outputs
from email.header import decode_header
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import time

# File paths for output
PROCESSED_EMAILS_FILE = "processed_emails.json"
SPAM_EMAILS_FILE = "spam_emails.json"
def delete_files():
    try:
        if os.path.exists(PROCESSED_EMAILS_FILE):
            os.remove(PROCESSED_EMAILS_FILE)
            print(f"Deleted {PROCESSED_EMAILS_FILE}")
        if os.path.exists(SPAM_EMAILS_FILE):
            os.remove(SPAM_EMAILS_FILE)
            print(f"Deleted {SPAM_EMAILS_FILE}")
    except Exception as e:
        print(f"Error deleting files: {e}")
# Function to save data to JSON files
def save_to_file(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving to file {file_path}: {e}")

# --- Step 1: Train Spam Detection Model ---
# Load the dataset
dataset = pd.read_csv('emails.csv')  
vectorizer = CountVectorizer()
x = vectorizer.fit_transform(dataset['text'])
X_train, X_test, Y_train, Y_test = train_test_split(x, dataset['spam'], test_size=0.2)
model = MultinomialNB()
model.fit(X_train, Y_train)
yPred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(Y_test, yPred)
print(f"Model Accuracy: {accuracy}")

# --- Step 2: Load Trusted Links and Whitelisted Senders ---
def load_list(file_path, column_name):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    try:
        data = pd.read_csv(file_path)[column_name].tolist()
        return [item.lower() for item in data]  # Ensure all entries are lowercase
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return []

# Paths to trusted links and whitelisted senders files
TRUSTED_LINKS_FILE = 'realistic_trusted_links.csv'  # Replace with the actual path
WHITELIST_SENDERS_FILE = 'realistic_whitelisted_senders.csv'  # Replace with the actual path

# Load the trusted links and whitelisted senders
TRUSTED_LINKS = load_list(TRUSTED_LINKS_FILE, 'domain')
WHITELIST_SENDERS = [item.split('@')[-1] for item in load_list(WHITELIST_SENDERS_FILE, 'sender')]
print(TRUSTED_LINKS[0])
print(WHITELIST_SENDERS[0])
if 'amazon.com' in WHITELIST_SENDERS:
    print('true')

# --- Step 3: Define Helper Functions ---
# Function to decode email content
def decode_email(content):
    if content is None:
        return ""
    decoded_bytes, encoding = decode_header(content)[0]
    if isinstance(decoded_bytes, bytes):
        return decoded_bytes.decode(encoding or 'utf-8', errors="ignore")
    return decoded_bytes

# Function to extract the domain from the sender email
def extract_domain(sender):
    match = re.search(r'@([a-zA-Z0-9.-]+)>?', sender)
    return match.group(1).lower() if match else ""

# Function to check if the sender domain is whitelisted
def is_whitelisted(sender):
    domain = extract_domain(sender) 
    return domain in WHITELIST_SENDERS

# Function to check if the email body contains links
def extract_links(body):
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    return re.findall(url_pattern, body)

# Function to check if links are genuine
from urllib.parse import urlparse

# Function to extract base domain from a URL
def get_base_domain(link):
    try:
        parsed_url = urlparse(link)
        # Return the netloc (domain) part of the URL
        return parsed_url.netloc.lower()
    except Exception as e:
        print(f"Error parsing link {link}: {e}")
        return ""

# Function to check if links are genuine
def contains_suspicious_links(links):
    for link in links:
        base_domain = get_base_domain(link)  # Extract base domain from the email link
        for trusted_link in TRUSTED_LINKS:
            trusted_domain = get_base_domain(trusted_link)  # Normalize trusted link
            if base_domain == trusted_domain:  # Match base domains
                return False  # Trusted link found
        print(f"Suspicious link detected: {link}")
        return True
    return False  # No links were suspicious

# Function to classify an email as spam or ham
def classify_email(body, sender):
    # Step 1: Check if sender is whitelisted
    if is_whitelisted(sender):
        return 'Ham'  # Trusted sender

    # Step 2: Check for links in the email
    links = extract_links(body)
    if links:
        if contains_suspicious_links(links):
            return 'Spam (Potential Phishing)'  # Suspicious links found
        return 'Ham (Contains Trusted Links)'  # Links are trusted

    # Step 3: Pass the email through the spam detection model
    messageVector = vectorizer.transform([body])
    prediction = model.predict(messageVector)
    return 'Spam' if prediction[0] == 1 else 'Ham'

# --- Step 4: Process Emails ---
def process_emails(mail, search_criteria):
    # Search for emails based on criteria (e.g., Primary tab or All emails)
    status, messages = mail.search(None, search_criteria)
    email_ids = messages[0].split()

    if not email_ids:
        print(f"No emails to process for criteria: {search_criteria}.")
        return

    for email_id in email_ids:
        # Fetch the email by ID
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Decode subject, sender, and body
                subject = decode_email(msg.get("Subject"))
                sender = decode_email(msg.get("From"))
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                # Classify the email
                result = classify_email(body, sender)
                print(f"{result}: {subject} from {sender} (Domain: {extract_domain(sender)})")

                # Store processed email data
                email_data = {"subject": subject, "sender": sender, "status": result}

                # Write to JSON files incrementally
                if result.startswith('Spam'):
                    append_to_file(SPAM_EMAILS_FILE, email_data)  # Spam emails
                    #mail.store(email_id, '+X-GM-LABELS', '\\Spam')  # Move spam to folder
                else:
                    append_to_file(PROCESSED_EMAILS_FILE, email_data)  # Processed emails


# Function to append data to a JSON file incrementally
def append_to_file(file_path, data):
    try:
        # Read existing data
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                file_data = json.load(f)
        else:
            file_data = []

        # Append new data
        file_data.append(data)

        # Write updated data back to the file
        with open(file_path, "w") as f:
            json.dump(file_data, f, indent=4)

    except Exception as e:
        print(f"Error appending to file {file_path}: {e}")

def move_to_spam():
    username = ""  # Use your Gmail email address
    password = ""
    imap_server = "imap.gmail.com"  # Gmail IMAP server

    # Login to Gmail
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(username, password)
    print("Logged in")
    mail.select("inbox")  # Access the inbox folder

    print("Processing Primary emails...")
    process_emails(mail, 'X-GM-RAW "category:primary"')  # Process Primary tab emails

    print("Processing remaining emails...")
    process_emails(mail, "ALL")  # Process all remaining emails

    mail.close()
    mail.logout()

# --- Main Loop ---
if __name__ == "__main__":
    while True:
        try:
            move_to_spam()  # Run the spam detection checker
            print("Checked for new emails.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            delete_files()
        time.sleep(300)  # Wait for 5 minutes before checking again

