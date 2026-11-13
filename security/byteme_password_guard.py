import bcrypt


# ==========================================
# BYTEME PASSWORD GUARD
# Handles password validation and security
# ==========================================

# Password configuration
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_BYTES = 72
BCRYPT_ROUNDS = 12


# ==========================================
# VALIDATE PASSWORD
# ==========================================

def validate_password(password):
    """
    Checks whether a password meets ByteMe's requirements.

    Minimum: 12 characters.
    Maximum: 72 UTF-8 bytes (bcrypt limitation).
    """

    if not isinstance(password, str):
        return False, "Password must be text."

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, (
            f"Password must contain at least "
            f"{MIN_PASSWORD_LENGTH} characters."
        )

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False, (
            "Password is too long. Please use a password "
            "of no more than 72 UTF-8 bytes."
        )

    if password.isspace():
        return False, "Password cannot contain only spaces."

    return True, "Password meets the requirements."


# ==========================================
# HASH PASSWORD
# ==========================================

def hash_password(password):
    """
    Converts a plain-text password into a bcrypt hash.

    The original password is never stored.
    """

    valid, message = validate_password(password)

    if not valid:
        raise ValueError(message)

    password_bytes = password.encode("utf-8")

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    )

    # Store the hash as text in SQLite
    return password_hash.decode("utf-8")


# ==========================================
# VERIFY PASSWORD
# ==========================================

def verify_password(password, stored_hash):
    """
    Checks a login password against its stored bcrypt hash.

    Returns True if the password matches.
    Returns False if it does not match.
    """

    if not isinstance(password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False

    try:

        return bcrypt.checkpw(
            password_bytes,
            stored_hash.encode("utf-8")
        )

    except (ValueError, TypeError):
        return False


# ==========================================
# PASSWORD SECURITY INFORMATION
# ==========================================

def password_requirements():
    """
    Returns the password requirements for the UI.
    """

    return {
        "minimum_length": MIN_PASSWORD_LENGTH,
        "maximum_bytes": MAX_PASSWORD_BYTES,
        "hashing_algorithm": "bcrypt",
        "bcrypt_rounds": BCRYPT_ROUNDS
    }
