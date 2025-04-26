import re
import imaplib
import email
import os
import json
from email.header import decode_header
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
from urllib.parse import urlparse

# File paths
PROCESSED_EMAILS_FILE = "processed_emails.json"
SPAM_EMAILS_FILE = "spam_emails.json"

# --- Step 1: Train Spam Detection Model ---
dataset = pd.read_csv('emails.csv')
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(dataset['text'])
X_train, X_test, Y_train, Y_test = train_test_split(X, dataset['spam'], test_size=0.2)
model = MultinomialNB()
model.fit(X_train, Y_train)

# Evaluate model (optional)
accuracy = accuracy_score(Y_test, model.predict(X_test))
print(f"Model Accuracy: {accuracy:.2f}")

# --- Step 2: Load Trusted Links and Whitelisted Senders ---
def load_list(file_path, column_name):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    try:
        data = pd.read_csv(file_path)[column_name].tolist()
        return [item.lower() for item in data]
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

TRUSTED_LINKS = load_list('realistic_trusted_links.csv', 'domain')
WHITELIST_SENDERS = [item.split('@')[-1] for item in load_list('realistic_whitelisted_senders.csv', 'sender')]

# --- Step 3: Helper Functions ---
def delete_files():
    for file_path in [PROCESSED_EMAILS_FILE, SPAM_EMAILS_FILE]:
        if os.path.exists(file_path):
            os.remove(file_path)

def decode_email(content):
    if content is None:
        return ""
    decoded_bytes, encoding = decode_header(content)[0]
    if isinstance(decoded_bytes, bytes):
        return decoded_bytes.decode(encoding or 'utf-8', errors="ignore")
    return decoded_bytes

def extract_domain(sender):
    match = re.search(r'@([a-zA-Z0-9.-]+)>?', sender)
    return match.group(1).lower() if match else ""

def is_whitelisted(sender):
    domain = extract_domain(sender)
    return domain in WHITELIST_SENDERS

def extract_links(body):
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    return re.findall(url_pattern, body)

def get_base_domain(link):
    try:
        return urlparse(link).netloc.lower()
    except:
        return ""

def contains_suspicious_links(links):
    for link in links:
        base_domain = get_base_domain(link)
        for trusted_link in TRUSTED_LINKS:
            trusted_domain = get_base_domain(trusted_link)
            if base_domain == trusted_domain:
                return False  # Trusted
        return True  # Suspicious
    return False  # No links suspicious

def classify_email(body, sender):
    if is_whitelisted(sender):
        return 'Ham'

    links = extract_links(body)
    if links:
        if contains_suspicious_links(links):
            return 'Spam (Suspicious Links)'
        return 'Ham (Trusted Links)'

    message_vector = vectorizer.transform([body])
    prediction = model.predict(message_vector)
    return 'Spam' if prediction[0] == 1 else 'Ham'

def append_to_file(file_path, data):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                file_data = json.load(f)
        else:
            file_data = []
        file_data.append(data)
        with open
