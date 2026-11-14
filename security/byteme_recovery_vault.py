import re
import secrets
import bcrypt

from .byteme_user_registry import (
    save_recovery_codes,
    get_unused_recovery_codes,
    mark_recovery_code_used
)


# ==========================================
# BYTEME RECOVERY VAULT
# Manages one-time backup authentication codes
# ==========================================

RECOVERY_CODE_COUNT = 10
BCRYPT_ROUNDS = 12


# ==========================================
# NORMALISE RECOVERY CODE
# ==========================================

def normalize_recovery_code(code):
    """
    Removes separators and validates the recovery-code format.
    """

    if not isinstance(code, str):
        return None

    normalized = (
        code.strip()
        .replace("-", "")
        .replace(" ", "")
        .upper()
    )

    if not re.fullmatch(r"[A-F0-9]{32}", normalized):
        return None

    return normalized


# ==========================================
# HASH RECOVERY CODE
# ==========================================

def hash_recovery_code(code):
    """
    Hashes a recovery code using bcrypt.
    """

    normalized = normalize_recovery_code(code)

    if not normalized:
        raise ValueError("Invalid recovery-code format.")

    hashed = bcrypt.hashpw(
        normalized.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    )

    return hashed.decode("utf-8")


# ==========================================
# GENERATE RECOVERY CODES
# ==========================================

def generate_recovery_codes(user_id, count=RECOVERY_CODE_COUNT):
    """
    Generates unique, one-time recovery codes.

    Only the hashed versions are saved in the database.

    The original codes are returned once so the user
    can save them somewhere secure.
    """

    if not isinstance(count, int) or not 5 <= count <= 20:
        raise ValueError(
            "Recovery-code count must be between 5 and 20."
        )

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    plain_codes = []
    hashed_codes = []

    for _ in range(count):

        # Generate 128 bits of random data
        raw_code = secrets.token_hex(16).upper()

        # Format as eight groups of four characters
        formatted_code = "-".join(
            raw_code[index:index + 4]
            for index in range(0, 32, 4)
        )

        plain_codes.append(formatted_code)

        # Only store the bcrypt hash
        hashed_codes.append(
            hash_recovery_code(formatted_code)
        )

    # Replace the user's previous recovery-code set
    save_recovery_codes(
        user_id,
        hashed_codes
    )

    # Original codes are returned only once
    return plain_codes


# ==========================================
# VERIFY RECOVERY CODE
# ==========================================

def verify_recovery_code(user_id, entered_code):
    """
    Checks whether a recovery code belongs to the user.

    A successfully verified recovery code is immediately
    marked as used and cannot be used again.
    """

    if not isinstance(user_id, int) or user_id <= 0:
        return False

    normalized = normalize_recovery_code(entered_code)

    if not normalized:
        return False

    stored_codes = get_unused_recovery_codes(user_id)

    for stored_code in stored_codes:

        try:
            matches = bcrypt.checkpw(
                normalized.encode("utf-8"),
                stored_code["code_hash"].encode("utf-8")
            )

        except (ValueError, TypeError):
            continue

        if matches:

            # Mark the code as used
            return mark_recovery_code_used(
                stored_code["id"],
                user_id
            )

    return False


# ==========================================
# CHECK UNUSED RECOVERY CODES
# ==========================================

def count_unused_recovery_codes(user_id):
    """
    Returns the number of unused recovery codes.
    """

    if not isinstance(user_id, int) or user_id <= 0:
        return 0

    return len(
        get_unused_recovery_codes(user_id)
    )
