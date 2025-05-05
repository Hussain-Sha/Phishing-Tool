 Load Trusted Links and Whitelisted Senders ---
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