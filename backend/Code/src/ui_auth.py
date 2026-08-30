"""Streamlit login/register UI for local user accounts."""

from __future__ import annotations

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None

from .user_manager import authenticate_user, create_user, list_users


def require_login(config) -> dict | None:
    """Render login/register UI and return the logged-in user record."""
    if st is None:
        return None
    if not getattr(config, "enable_user_accounts", True):
        return {"user_id": "default", "username": "Default"}
    if st.session_state.get("current_user"):
        user = st.session_state["current_user"]
        st.sidebar.caption(f"Logged in: {user['username']}")
        if st.sidebar.button("Logout"):
            st.session_state.pop("current_user", None)
            st.rerun()
        return user
    st.title("Alim Study Assistant")
    tab_login, tab_register = st.tabs(["Login", "Register"])
    with tab_login:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user = authenticate_user(username, password, config)
            if user:
                st.session_state["current_user"] = user
                st.rerun()
            st.error("Login failed. Check username and password.")
    with tab_register:
        new_username = st.text_input("New username", key="register_username")
        new_password = st.text_input("New password", type="password", key="register_password")
        existing = list_users(config)
        template_options = [""] + [user["user_id"] for user in existing]
        template = st.selectbox("Copy study material from", template_options, format_func=lambda item: "Shared template/default" if item == "" else item)
        if st.button("Create account"):
            try:
                user = create_user(new_username, new_password, config, template_user_id=template or None)
                st.session_state["current_user"] = user
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    return None
