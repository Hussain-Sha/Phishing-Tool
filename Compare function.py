def compare(email1: str, email2: str) -> bool:
    """
    Compare two email addresses by normalizing them (lowercase and stripping spaces).

    Args:
        email1 (str): First email address.
        email2 (str): Second email address.

    Returns:
        bool: True if both emails are equal after normalization, False otherwise.
    """
    if not isinstance(email1, str) or not isinstance(email2, str):
        raise ValueError("Both inputs must be strings representing email addresses.")

    normalized_email1 = email1.strip().lower()
    normalized_email2 = email2.strip().lower()

    return normalized_email1 == normalized_email2


# Example usage
if __name__ == "__main__":
    email_a = " Example@Domain.COM "
    email_b = "example@domain.com"
    result = compare(email_a, email_b)
    print("Emails match:" if result else "Emails do not match.")
