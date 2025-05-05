
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