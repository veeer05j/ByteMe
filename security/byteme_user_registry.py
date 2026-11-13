import sqlite3
from pathlib import Path
from contextlib import closing


# ==========================================
# BYTEME USER REGISTRY
# Manages user accounts and authentication data
# ==========================================

# Project database location
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "DATA" / "byteme_auth.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    """
    Creates a connection to the ByteMe authentication database.
    """

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ==========================================
# INITIALISE DATABASE
# ==========================================

def initialize_database():
    """
    Creates the authentication tables if they do not exist.
    """

    with closing(get_connection()) as connection:

        connection.executescript("""

            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT NOT NULL UNIQUE COLLATE NOCASE,

                password_hash TEXT NOT NULL,

                totp_secret_encrypted TEXT NOT NULL,

                is_active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                last_login TEXT

            );


            CREATE TABLE IF NOT EXISTS recovery_codes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                code_hash TEXT NOT NULL,

                used_at TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                UNIQUE(user_id, code_hash)

            );

        """)

        connection.commit()


# ==========================================
# CREATE USER ACCOUNT
# ==========================================

def create_user(username, password_hash, encrypted_totp_secret):
    """
    Registers a new user.

    Passwords must already be hashed.
    TOTP secrets must already be encrypted.
    """

    username = username.strip()

    if len(username) < 3 or len(username) > 32:
        raise ValueError(
            "Username must contain between 3 and 32 characters."
        )

    if not password_hash or not encrypted_totp_secret:
        raise ValueError(
            "Password hash and encrypted authenticator secret are required."
        )

    try:

        with closing(get_connection()) as connection:

            cursor = connection.execute(
                """
                INSERT INTO users (
                    username,
                    password_hash,
                    totp_secret_encrypted
                )
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    encrypted_totp_secret
                )
            )

            connection.commit()

            return cursor.lastrowid

    except sqlite3.IntegrityError as error:

        raise ValueError(
            "This username is already registered."
        ) from error


# ==========================================
# FIND USER ACCOUNT
# ==========================================

def get_user_by_username(username):
    """
    Finds a user using their username.
    Returns None when the account does not exist.
    """

    with closing(get_connection()) as connection:

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username.strip(),)
        ).fetchone()

        return dict(user) if user else None


def get_user_by_id(user_id):
    """
    Finds a user using their unique account ID.
    """

    with closing(get_connection()) as connection:

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        return dict(user) if user else None


# ==========================================
# UPDATE LAST LOGIN
# ==========================================

def update_last_login(user_id):
    """
    Records the user's most recent successful login.
    """

    with closing(get_connection()) as connection:

        connection.execute(
            """
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE id = ? AND is_active = 1
            """,
            (user_id,)
        )

        connection.commit()


# ==========================================
# MANAGE RECOVERY CODES
# ==========================================

def save_recovery_codes(user_id, code_hashes):
    """
    Saves hashed, one-time recovery codes for a user.
    Replaces any existing recovery codes.
    """

    with closing(get_connection()) as connection:

        user = connection.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            raise ValueError("User account not found.")

        connection.execute(
            "DELETE FROM recovery_codes WHERE user_id = ?",
            (user_id,)
        )

        for code_hash in code_hashes:

            if not code_hash:
                continue

            connection.execute(
                """
                INSERT INTO recovery_codes (
                    user_id,
                    code_hash
                )
                VALUES (?, ?)
                """,
                (user_id, code_hash)
            )

        connection.commit()


def get_unused_recovery_codes(user_id):
    """
    Retrieves unused recovery-code hashes.
    """

    with closing(get_connection()) as connection:

        rows = connection.execute(
            """
            SELECT id, code_hash
            FROM recovery_codes
            WHERE user_id = ?
            AND used_at IS NULL
            """,
            (user_id,)
        ).fetchall()

        return [dict(row) for row in rows]


def mark_recovery_code_used(code_id, user_id):
    """
    Marks a recovery code as used.
    A recovery code cannot be reused.
    """

    with closing(get_connection()) as connection:

        cursor = connection.execute(
            """
            UPDATE recovery_codes
            SET used_at = CURRENT_TIMESTAMP
            WHERE id = ?
            AND user_id = ?
            AND used_at IS NULL
            """,
            (code_id, user_id)
        )

        connection.commit()

        return cursor.rowcount == 1
