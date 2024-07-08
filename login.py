# pages/login.py
import streamlit as st
from utils.authentication import check_credentials 

def show(cookies):
    st.title("Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if check_credentials(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            cookies.set('logged_in', True)
            # st.success(f"Welcome {username}!")
            st.rerun()  # Rerun to reflect login state
        else:
            st.error("Invalid username or password")
