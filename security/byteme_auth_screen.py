import time
from contextlib import closing

import streamlit as st

from security.byteme_user_registry import (
    get_connection,
    get_user_by_username,
    create_user,
    update_last_login
)

from security.byteme_password_guard import (
    validate_password,
    hash_password,
    verify_password
)

from security.byteme_totp_verifier import (
    generate_totp_secret,
    generate_qr_code,
    encrypt_totp_secret,
    verify_totp_code,
    verify_encrypted_totp_code
)

from security.byteme_recovery_vault import (
    generate_recovery_codes,
    verify_recovery_code
)


# ==========================================
# BYTEME AUTHENTICATION SCREEN
# Registration, login and 2FA verification
# ==========================================

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 900

AUTH_KEY = "byteme_authenticated_user"
PENDING_LOGIN_KEY = "byteme_pending_login"
PENDING_REGISTER_KEY = "byteme_pending_registration"
RECOVERY_DISPLAY_KEY = "byteme_new_recovery_codes"


# ==========================================
# DATABASE LOGIN ATTEMPT LIMITS
# ==========================================

def _create_attempt_table():
    """Creates the persistent login-attempt table."""

    with closing(get_connection()) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS auth_attempt_limits (
                username TEXT PRIMARY KEY,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until REAL NOT NULL DEFAULT 0
            )
        """)

        connection.commit()


def _is_account_locked(username):
    """Checks whether an account is temporarily locked."""

    normalized = username.strip().casefold()
    _create_attempt_table()

    with closing(get_connection()) as connection:

        result = connection.execute(
            """
            SELECT failed_attempts, locked_until
            FROM auth_attempt_limits
            WHERE username = ?
            """,
            (normalized,)
        ).fetchone()

        if not result:
            return 0

        remaining = result["locked_until"] - time.time()

        if remaining > 0:
            return int(remaining) + 1

        if result["locked_until"] > 0:
            connection.execute(
                "DELETE FROM auth_attempt_limits WHERE username = ?",
                (normalized,)
            )
            connection.commit()

        return 0


def _record_failed_attempt(username):
    """Records a failed login or verification attempt."""

    normalized = username.strip().casefold()
    _create_attempt_table()

    with closing(get_connection()) as connection:

        result = connection.execute(
            """
            SELECT failed_attempts
            FROM auth_attempt_limits
            WHERE username = ?
            """,
            (normalized,)
        ).fetchone()

        attempts = result["failed_attempts"] if result else 0
        attempts += 1

        locked_until = (
            time.time() + LOCKOUT_SECONDS
            if attempts >= MAX_FAILED_ATTEMPTS
            else 0
        )

        connection.execute(
            """
            INSERT INTO auth_attempt_limits (
                username,
                failed_attempts,
                locked_until
            )
            VALUES (?, ?, ?)

            ON CONFLICT(username)
            DO UPDATE SET
                failed_attempts = excluded.failed_attempts,
                locked_until = excluded.locked_until
            """,
            (normalized, attempts, locked_until)
        )

        connection.commit()


def _clear_failed_attempts(username):
    """Resets failed attempts after successful authentication."""

    with closing(get_connection()) as connection:

        connection.execute(
            "DELETE FROM auth_attempt_limits WHERE username = ?",
            (username.strip().casefold(),)
        )

        connection.commit()


# ==========================================
# SESSION MANAGEMENT
# ==========================================

def _finish_login(user):
    """Completes authentication after both factors succeed."""

    update_last_login(user["id"])
    _clear_failed_attempts(user["username"])

    st.session_state[AUTH_KEY] = {
        "user_id": user["id"],
        "username": user["username"],
        "authenticated_at": time.time()
    }

    st.session_state.pop(PENDING_LOGIN_KEY, None)

    st.rerun()


def logout():
    """Ends the current authenticated session."""

    st.session_state.pop(AUTH_KEY, None)
    st.session_state.pop(PENDING_LOGIN_KEY, None)

    st.rerun()


# ==========================================
# REGISTRATION SCREEN
# ==========================================

def _render_registration():

    st.subheader("Create your ByteMe account")

    with st.form("byteme_registration_form"):

        username = st.text_input(
            "Choose a username",
            max_chars=32
        )

        password = st.text_input(
            "Create a password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm your password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Continue to authenticator setup",
            use_container_width=True
        )

    if submitted:

        username = username.strip()

        if not username:
            st.error("Please enter a username.")

        elif len(username) < 3:
            st.error("Username must contain at least 3 characters.")

        elif get_user_by_username(username):
            st.error("This username is already registered.")

        elif password != confirm_password:
            st.error("Your passwords do not match.")

        else:

            valid, message = validate_password(password)

            if not valid:
                st.error(message)

            else:

                secret = generate_totp_secret()

                st.session_state[PENDING_REGISTER_KEY] = {
                    "username": username,
                    "password_hash": hash_password(password),
                    "encrypted_secret": encrypt_totp_secret(secret),
                    "secret": secret
                }

                st.rerun()

    # Authenticator setup
    pending = st.session_state.get(PENDING_REGISTER_KEY)

    if pending:

        st.divider()

        st.subheader("Set up two-factor authentication")

        st.write(
            "Open Google Authenticator or Microsoft Authenticator "
            "on your phone and scan the QR code below."
        )

        qr_image = generate_qr_code(
            pending["secret"],
            pending["username"]
        )

        st.image(qr_image, width=220)

        st.info(
            "Enter the six-digit code displayed in your authenticator app."
        )

        st.caption("Manual setup key (keep private):")

        st.code(pending["secret"])

        with st.form("byteme_registration_verify_form"):

            verification_code = st.text_input(
                "Authenticator verification code",
                max_chars=6
            )

            verify_button = st.form_submit_button(
                "Verify and create account",
                use_container_width=True
            )

        if verify_button:

            if verify_totp_code(
                pending["secret"],
                verification_code
            ):

                try:

                    user_id = create_user(
                        pending["username"],
                        pending["password_hash"],
                        pending["encrypted_secret"]
                    )

                    recovery_codes = generate_recovery_codes(
                        user_id
                    )

                    st.session_state[RECOVERY_DISPLAY_KEY] = recovery_codes

                    st.session_state.pop(
                        PENDING_REGISTER_KEY,
                        None
                    )

                    st.rerun()

                except (ValueError, RuntimeError) as error:

                    st.error(
                        f"Account creation failed: {error}"
                    )

            else:

                st.error(
                    "Invalid verification code. Please try again."
                )


# ==========================================
# RECOVERY CODE DISPLAY
# ==========================================

def _render_recovery_codes():

    st.subheader("Your recovery codes")

    st.success("Your account and 2FA have been activated!")

    st.warning(
        "Save these recovery codes somewhere safe. "
        "Each code can only be used once. They will not "
        "be displayed again after you dismiss this screen."
    )

    codes = st.session_state[RECOVERY_DISPLAY_KEY]

    st.code("\n".join(codes))

    st.download_button(
        "Download recovery codes",
        data="\n".join(codes),
        file_name="byteme_recovery_codes.txt",
        mime="text/plain",
        use_container_width=True
    )

    if st.button(
        "I've saved my recovery codes",
        use_container_width=True
    ):

        st.session_state.pop(RECOVERY_DISPLAY_KEY, None)
        st.session_state["byteme_auth_mode"] = "Sign in"

        st.rerun()


# ==========================================
# LOGIN SCREEN
# ==========================================

def _render_login():

    st.subheader("Welcome back")

    with st.form("byteme_login_form"):

        username = st.text_input(
            "Username",
            max_chars=32
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Continue",
            use_container_width=True
        )

    if submitted:

        username = username.strip()

        if not username or not password:
            st.error("Please enter your username and password.")

        else:

            remaining = _is_account_locked(username)

            if remaining > 0:

                st.error(
                    f"Too many failed attempts. "
                    f"Try again in approximately {remaining} seconds."
                )

            else:

                user = get_user_by_username(username)

                if (
                    user
                    and user["is_active"] == 1
                    and verify_password(
                        password,
                        user["password_hash"]
                    )
                ):

                    st.session_state[PENDING_LOGIN_KEY] = {
                        "user_id": user["id"],
                        "username": user["username"],
                        "encrypted_secret": user["totp_secret_encrypted"]
                    }

                    st.rerun()

                else:

                    _record_failed_attempt(username)

                    st.error(
                        "Invalid username or password."
                    )


# ==========================================
# SECOND FACTOR VERIFICATION
# ==========================================

def _render_second_factor():

    pending = st.session_state.get(PENDING_LOGIN_KEY)

    if not pending:
        return

    username = pending["username"]

    st.subheader("Two-factor verification")

    st.write(
        f"Enter the authenticator code for **{username}**."
    )

    st.caption(
        "You can also use one of your recovery codes if "
        "you cannot access your authenticator app."
    )

    with st.form("byteme_2fa_form", clear_on_submit=True):

        entered_code = st.text_input(
            "Authenticator or recovery code",
            max_chars=40
        )

        submitted = st.form_submit_button(
            "Verify and sign in",
            use_container_width=True
        )

    if submitted:

        remaining = _is_account_locked(username)

        if remaining > 0:

            st.session_state.pop(PENDING_LOGIN_KEY, None)

            st.error(
                f"Account temporarily locked. Try again in "
                f"approximately {remaining} seconds."
            )

            return

        verified = verify_encrypted_totp_code(
            pending["encrypted_secret"],
            entered_code
        )

        used_recovery_code = False

        if not verified:

            verified = verify_recovery_code(
                pending["user_id"],
                entered_code
            )

            used_recovery_code = verified

        if verified:

            user = get_user_by_username(username)

            if user and user["is_active"] == 1:

                _finish_login(user)

                if used_recovery_code:
                    st.info("A recovery code was used.")

            else:

                st.session_state.pop(PENDING_LOGIN_KEY, None)

                st.error("Your account is unavailable.")

        else:

            _record_failed_attempt(username)

            remaining = _is_account_locked(username)

            if remaining > 0:

                st.session_state.pop(PENDING_LOGIN_KEY, None)

                st.error(
                    "Too many failed verification attempts. "
                    f"Try again in approximately {remaining} seconds."
                )

            else:

                st.error(
                    "Incorrect verification code. Please try again."
                )


# ==========================================
# MAIN AUTHENTICATION INTERFACE
# ==========================================

def render_authentication():
    """
    Displays the login/registration interface.

    Returns True only when the current Streamlit session
    has successfully completed authentication.
    """

    # Already authenticated
    authenticated_user = st.session_state.get(AUTH_KEY)

    if authenticated_user:

        with st.sidebar:

            st.success(
                f"Signed in as {authenticated_user['username']}"
            )

            if st.button(
                "Log out",
                use_container_width=True
            ):
                logout()

        return True

    # Recovery codes must be saved before continuing
    if RECOVERY_DISPLAY_KEY in st.session_state:

        st.title("🔐 ByteMe Security")
        _render_recovery_codes()

        return False

    # Registration or login is in progress
    if PENDING_LOGIN_KEY in st.session_state:

        st.title("🔐 ByteMe Security")
        _render_second_factor()

        return False

    if PENDING_REGISTER_KEY in st.session_state:

        st.title("🔐 ByteMe Security")
        _render_registration()

        return False

    # Normal login / registration
    st.title("🔐 ByteMe Secure Access")

    st.caption(
        "Sign in securely using your password and "
        "authenticator app."
    )

    mode = st.radio(
        "Choose an option",
        ["Sign in", "Create account"],
        horizontal=True,
        key="byteme_auth_mode"
    )

    if mode == "Sign in":

        _render_login()

    else:

        _render_registration()

    return False
