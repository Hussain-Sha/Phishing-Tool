# Function to check if the sender domain is whitelisted
def is_whitelisted(sender):
    domain = extract_domain(sender) 
    return domain in WHITELIST_SENDERS