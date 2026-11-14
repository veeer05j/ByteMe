import streamlit as st

from security.byteme_user_registry import initialize_database
from security.byteme_auth_screen import render_authentication

st.set_page_config(
    page_title="ByteMe Security Test",
    page_icon="🔐"
)

# Initialise the separate authentication database
initialize_database()

# Display the authentication interface
authenticated = render_authentication()

if authenticated:

    user = st.session_state.get(
        "byteme_authenticated_user",
        {}
    )

    st.success("Authentication successful!")

    st.title("Welcome to ByteMe Security Testing 🔐")

    st.write(
        f"You are successfully logged in as "
        f"{user.get('username', 'User')}."
    )

    st.info(
        "This is an isolated security test. "
        "Your friend's app.py and the other project pages "
        "have not been modified."
    )