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