import os
import re
from io import BytesIO

import pyotp
import qrcode

from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken


# ==========================================
# BYTEME TOTP VERIFIER
# Handles two-factor authentication
# ==========================================

load_dotenv()

ISSUER_NAME = "ByteMe"

TOTP_DIGITS = 6
TOTP_INTERVAL = 30
VALID_WINDOW = 1


# ==========================================
# ENCRYPTION CONFIGURATION
# ==========================================

def get_encryption_cipher():
    """
    Loads the permanent encryption key from .env.
    """

    encryption_key = os.getenv(
        "BYTEME_TOTP_ENCRYPTION_KEY"
    )

    if not encryption_key:
        raise RuntimeError(
            "TOTP encryption key is missing from .env."
        )

    try:
        return Fernet(encryption_key.encode("utf-8"))

    except (ValueError, TypeError) as error:
        raise RuntimeError(
            "The TOTP encryption key is invalid."
        ) from error


# ==========================================
# GENERATE TOTP SECRET
# ==========================================

def generate_totp_secret():
    """
    Generates a unique secret for each user.
    """

    return pyotp.random_base32()


# ==========================================
# GENERATE AUTHENTICATOR URI
# ==========================================

def generate_totp_uri(secret, username):
    """
    Creates a provisioning URI compatible with
    Google Authenticator and Microsoft Authenticator.
    """

    if not secret or not username:
        raise ValueError(
            "Secret and username are required."
        )

    totp = pyotp.TOTP(
        secret,
        digits=TOTP_DIGITS,
        interval=TOTP_INTERVAL
    )

    return totp.provisioning_uri(
        name=username,
        issuer_name=ISSUER_NAME
    )


# ==========================================
# GENERATE QR CODE
# ==========================================

def generate_qr_code(secret, username):
    """
    Generates a QR code image for authenticator setup.

    Returns a PNG image in memory.
    """

    uri = generate_totp_uri(
        secret,
        username
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4
    )

    qr.add_data(uri)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    image_buffer = BytesIO()

    image.save(
        image_buffer,
        format="PNG"
    )

    image_buffer.seek(0)

    return image_buffer


# ==========================================
# VERIFY TOTP CODE
# ==========================================

def verify_totp_code(secret, code):
    """
    Verifies a six-digit authenticator code.

    Allows a small clock difference between devices.
    """

    if not secret or not isinstance(code, str):
        return False

    code = code.strip()

    if not re.fullmatch(r"\d{6}", code):
        return False

    try:

        totp = pyotp.TOTP(
            secret,
            digits=TOTP_DIGITS,
            interval=TOTP_INTERVAL
        )

        return totp.verify(
            code,
            valid_window=VALID_WINDOW
        )

    except (ValueError, TypeError):
        return False


# ==========================================
# ENCRYPT TOTP SECRET
# ==========================================

def encrypt_totp_secret(secret):
    """
    Encrypts an authenticator secret before
    storing it in the database.
    """

    if not secret:
        raise ValueError(
            "Authenticator secret cannot be empty."
        )

    cipher = get_encryption_cipher()

    encrypted_secret = cipher.encrypt(
        secret.encode("utf-8")
    )

    return encrypted_secret.decode("utf-8")


# ==========================================
# DECRYPT TOTP SECRET
# ==========================================

def decrypt_totp_secret(encrypted_secret):
    """
    Decrypts a stored authenticator secret.
    """

    if not encrypted_secret:
        raise ValueError(
            "Encrypted authenticator secret is missing."
        )

    cipher = get_encryption_cipher()

    try:

        decrypted_secret = cipher.decrypt(
            encrypted_secret.encode("utf-8")
        )

        return decrypted_secret.decode("utf-8")

    except InvalidToken as error:
        raise ValueError(
            "Unable to decrypt authenticator secret. "
            "Check your encryption key."
        ) from error


# ==========================================
# VERIFY ENCRYPTED TOTP SECRET
# ==========================================

def verify_encrypted_totp_code(encrypted_secret, code):
    """
    Decrypts the user's stored secret and verifies
    the authenticator code.
    """

    try:

        secret = decrypt_totp_secret(
            encrypted_secret
        )

        return verify_totp_code(
            secret,
            code
        )

    except (ValueError, RuntimeError):
        return False
