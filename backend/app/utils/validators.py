import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> str:
    """Validate an email address and normalize it to lowercase."""
    normalized = email.strip().lower()
    if not EMAIL_REGEX.match(normalized):
        raise ValueError("Invalid email address")
    return normalized