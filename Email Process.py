
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
