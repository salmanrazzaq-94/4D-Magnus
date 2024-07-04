# pages/login.py
import streamlit as st
from utils.authentication import check_credentials

def show():
    st.title("Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login = st.button("Login")

    if login:
        if check_credentials(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid username or password")
